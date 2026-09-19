"""COMPONENT-CLI — the `lspd` entry point and the only orchestrator of the pipeline.

Parses argv with argparse (prog fixed to ``lspd``, 100-column help), runs
load → pre-validate → command → post-validate → emit → render for each
element, holds the single catch-all (PATTERN-ERROR-ENVELOPE) and decides
the exit code (PATTERN-EXIT-CODES).

DICT: COMPONENT-CLI
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from collections.abc import Sequence
from importlib import metadata
from typing import Any

from lspd import emitter, loader, render, schema, validator
from lspd.commands import init as cmd_init
from lspd.commands import validate as cmd_validate
from lspd.errors import FileExistsAlreadyError, InternalError, LspdError, UsageError
from lspd.model import Finding

DISTRIBUTION = "dictum-binder"
HELP_WIDTH = 100
DEFAULT_FILE = "./bindings.yaml"

GLOBAL_OPTIONS: tuple[tuple[str, dict[str, Any]], ...] = (
    (
        "--file",
        {
            "metavar": "PATH",
            "help": f"target map (default {DEFAULT_FILE}); symlinks resolve to the final target",
        },
    ),
    (
        "--human",
        {"action": "store_true", "help": "readable rendering instead of the JSON envelope"},
    ),
    (
        "--check-paths",
        {
            "action": "store_true",
            "help": "also check that every locator path exists (INV-PATH-EXISTS, an error)",
        },
    ),
    (
        "--no-size-limit",
        {"action": "store_true", "help": "lift the 10 MiB target-size cap (ERR-FILE-TOO-LARGE)"},
    ),
    ("--debug", {"action": "store_true", "help": "also print a traceback on stderr for any ERR-*"}),
)


class _HelpRequested(Exception):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.text = text


class _VersionRequested(Exception):
    pass


class _HelpAction(argparse.Action):
    def __init__(self, option_strings: Sequence[str], dest: str, **kwargs: Any) -> None:
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        raise _HelpRequested(parser.format_help())


class _VersionAction(argparse.Action):
    def __init__(self, option_strings: Sequence[str], dest: str, **kwargs: Any) -> None:
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        raise _VersionRequested()


class _Formatter(argparse.RawDescriptionHelpFormatter):
    def __init__(self, prog: str) -> None:
        super().__init__(prog, width=HELP_WIDTH, max_help_position=28)


class _Parser(argparse.ArgumentParser):
    """argparse's own error path intercepted into ERR-USAGE with this level's help text."""

    path: str = ""
    subparsers_by_name: dict[str, _Parser]

    def error(self, message: str) -> Any:
        raise UsageError(message, self.format_help(), self.path)


def _add_global_options(parser: argparse.ArgumentParser, *, mirrored: bool) -> None:
    for flag, spec in GLOBAL_OPTIONS:
        kwargs = dict(spec)
        if mirrored:
            kwargs["default"] = argparse.SUPPRESS
        elif flag == "--file":
            kwargs["default"] = DEFAULT_FILE
        parser.add_argument(flag, **kwargs)


def _new_parser(prog: str, path: str, description: str, epilog: str) -> _Parser:
    parser = _Parser(
        prog=prog,
        description=description,
        epilog=epilog,
        formatter_class=_Formatter,
        add_help=False,
    )
    parser.path = path
    parser.add_argument(
        "-h", "--help", action=_HelpAction, help="show this help and exit (plain text, exit 0)"
    )
    return parser


_EXIT_TEXT = (
    "exit codes: 0 clean or warnings only · 1 caller-fixable · 2 environment · 130 interrupted"
)


def build_parser() -> _Parser:
    parser = _new_parser(
        "lspd",
        "",
        "lspd — the deterministic reader, writer and validator of a Dictum project's "
        "bindings.yaml.\n"
        "Targets Dictum v1.2.0 binding maps. Output is one JSON envelope on stdout unless --human.",
        f"{_EXIT_TEXT}\n"
        "error codes: ERR-USAGE, ERR-FILE-MISSING, ERR-FILE-EXISTS, ERR-FILE-TOO-LARGE, ERR-IO,\n"
        "  ERR-PARSE, ERR-SCHEMA-VERSION, ERR-FILE-INVALID, ERR-NOT-FOUND, ERR-DUPLICATE, "
        "ERR-INPUT-INVALID,\n"
        "  ERR-INTERNAL",
    )
    parser.add_argument("--version", action=_VersionAction, help="print `lspd <version>` and exit")
    _add_global_options(parser, mirrored=False)
    sub = parser.add_subparsers(dest="command", metavar="<command>", parser_class=_Parser)
    sub.required = True
    parser.subparsers_by_name = {}

    p_init = sub.add_parser(
        "init",
        help="create the canonical empty map; refuses an existing file",
        description=(
            "Create the canonical empty map at the target (schema_version and an empty bindings\n"
            "mapping)."
        ),
        epilog=(
            f"{_EXIT_TEXT}\n"
            "errors: ERR-FILE-EXISTS (1) · ERR-IO (2) · ERR-USAGE (1) · ERR-INTERNAL (2)"
        ),
        formatter_class=_Formatter,
        add_help=False,
    )
    p_init.path = "init"
    p_init.add_argument("-h", "--help", action=_HelpAction, help="show this help and exit")
    _add_global_options(p_init, mirrored=True)

    p_validate = sub.add_parser(
        "validate",
        help="structural validation of the target; findings only, nothing written",
        description=(
            "Validate the target map structurally. Findings carry INV-* codes; exit 1 iff any is "
            "error-level.\n"
            "A schema_version mismatch is reported as the INV-SCHEMA-VERSION finding, never as\n"
            "ERR-SCHEMA-VERSION."
        ),
        epilog=(
            f"{_EXIT_TEXT}\n"
            "errors: ERR-FILE-MISSING (2) · ERR-FILE-TOO-LARGE (1) · ERR-IO (2) · ERR-PARSE (2)\n"
            "  · ERR-USAGE (1) · ERR-INTERNAL (2)"
        ),
        formatter_class=_Formatter,
        add_help=False,
    )
    p_validate.path = "validate"
    p_validate.add_argument("-h", "--help", action=_HelpAction, help="show this help and exit")
    _add_global_options(p_validate, mirrored=True)

    p_schema = sub.add_parser(
        "schema",
        help="print the embedded JSON Schema (raw), or its SHA-256 with --checksum",
        description=(
            "Print the embedded JSON Schema of the canonical map, byte-identical to the shipped\n"
            "lspd.schema.json. Reads no file."
        ),
        epilog=f"{_EXIT_TEXT}\nerrors: ERR-USAGE (1) · ERR-INTERNAL (2)",
        formatter_class=_Formatter,
        add_help=False,
    )
    p_schema.path = "schema"
    p_schema.add_argument("-h", "--help", action=_HelpAction, help="show this help and exit")
    p_schema.add_argument(
        "--checksum",
        action="store_true",
        help="print the lowercase SHA-256 of the schema bytes instead",
    )
    _add_global_options(p_schema, mirrored=True)
    parser.subparsers_by_name.update({"init": p_init, "validate": p_validate, "schema": p_schema})
    return parser


def parse(parser: _Parser, args: Sequence[str]) -> argparse.Namespace:
    """parse_args whose unrecognised-argument error names the deepest level reached."""
    ns, extras = parser.parse_known_args(args)
    if extras:
        deepest = parser.subparsers_by_name.get(ns.command, parser)
        raise UsageError(
            f"unrecognized arguments: {' '.join(extras)}", deepest.format_help(), deepest.path
        )
    return ns


def _write_stdout(text: str) -> None:
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


def _version() -> str:
    return metadata.version(DISTRIBUTION)


def _check_empty_strings(argv: Sequence[str]) -> None:
    if any(arg == "" for arg in argv):
        raise UsageError("empty-string argument", build_parser().format_help(), "")


def _exit_for(findings: list[Finding]) -> int:
    return 1 if any(f.severity == "error" for f in findings) else 0


class _Run:
    """One invocation's state: the pre-findings survive into an error envelope."""

    def __init__(self, ns: argparse.Namespace) -> None:
        self.ns = ns
        self.pre: list[Finding] = []
        self.post: list[Finding] = []

    # -- elements -----------------------------------------------------------------

    def init(self) -> dict[str, Any]:
        target = loader.resolve_target(self.ns.file)
        if os.path.exists(target):
            raise FileExistsAlreadyError(target, "target exists")
        m = cmd_init.empty_map()
        self.post = validator.finalize(validator.validate(m))
        if _exit_for(self.post):  # pragma: no cover — an empty map cannot carry an error
            raise InternalError(
                "post-validation of the empty map failed", "; ".join(f.code for f in self.post)
            )
        emitter.write(m, target, create=True)
        return cmd_init.result(target)

    def validate(self) -> dict[str, Any]:
        m, loaded = loader.load(self.ns.file, size_limit=not self.ns.no_size_limit)
        self.pre = validator.finalize(
            loaded + validator.validate(m, check_paths=self.ns.check_paths, root=os.getcwd())
        )
        return cmd_validate.result(self.pre, paths_checked=self.ns.check_paths)


def main(argv: Sequence[str] | None = None) -> int:
    """The `lspd` console script. Returns the exit code; prints exactly one document."""
    args = list(sys.argv[1:] if argv is None else argv)
    human = "--human" in args
    debug = "--debug" in args
    command = ""
    run: _Run | None = None
    try:
        _check_empty_strings(args)
        parser = build_parser()
        ns = parse(parser, args)
        command = ns.command
        if command == "schema":
            _write_stdout(
                schema.checksum() + "\n" if ns.checksum else schema.schema_json().decode("utf-8")
            )
            return 0
        run = _Run(ns)
        result = run.init() if command == "init" else run.validate()
        _write_stdout(
            render.render(
                command,
                result,
                run.pre,
                run.post,
                None,
                version=_version(),
                schema_version=schema.SCHEMA_VERSION,
                human=human,
            )
        )
        return max(_exit_for(run.pre), _exit_for(run.post))
    except _HelpRequested as help_request:
        _write_stdout(help_request.text)
        return 0
    except _VersionRequested:
        _write_stdout(f"lspd {_version()}\n")
        return 0
    except KeyboardInterrupt:
        return 130
    except LspdError as err:
        if isinstance(err, UsageError):
            command = err.command
        return _fail(err, command, run, human, debug)
    except Exception as exc:  # noqa: BLE001 — the single catch-all of PATTERN-ERROR-ENVELOPE
        return _fail(
            InternalError(f"unexpected {type(exc).__name__}: {exc}", repr(exc)),
            command,
            run,
            human,
            debug,
        )


def _fail(err: LspdError, command: str, run: _Run | None, human: bool, debug: bool) -> int:
    if debug:
        traceback.print_exc(file=sys.stderr)
    pre = run.pre if run is not None else []
    _write_stdout(
        render.render(
            command,
            None,
            pre,
            [],
            err,
            version=_version(),
            schema_version=schema.SCHEMA_VERSION,
            human=human,
        )
    )
    return err.exit_code
