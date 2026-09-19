"""COMPONENT-CLI — the `lspd` entry point and the only orchestrator of the pipeline.

Parses argv with argparse (prog fixed to ``lspd``, 100-column help), runs
load → pre-validate → command → post-validate → emit → render for each
element, holds the single catch-all (PATTERN-ERROR-ENVELOPE) and decides
the exit code (PATTERN-EXIT-CODES).

DICT: COMPONENT-CLI
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
from collections.abc import Callable, Sequence
from importlib import metadata
from typing import Any

from lspd import emitter, loader, model, render, schema, validator
from lspd.commands import add as cmd_add
from lspd.commands import comment as cmd_comment
from lspd.commands import coverage as cmd_coverage
from lspd.commands import init as cmd_init
from lspd.commands import query as cmd_query
from lspd.commands import remove as cmd_remove
from lspd.commands import set as cmd_set
from lspd.commands import validate as cmd_validate
from lspd.errors import (
    FileExistsAlreadyError,
    FileInvalidError,
    InputInvalidError,
    InternalError,
    LspdError,
    SchemaVersionError,
    UsageError,
)
from lspd.model import KIND_PATTERN, Anchor, Finding, Map, is_contract_id, kind_of

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
    p_get = sub.add_parser(
        "get",
        help="one or more bindings by ID, in argument order",
        description=(
            "Print the requested bindings (OUT-BINDING, comments included) in argument order.\n"
            "The first unknown ID is ERR-NOT-FOUND and nothing is returned."
        ),
        epilog=(
            f"{_EXIT_TEXT}\n"
            "errors: ERR-NOT-FOUND (1) · ERR-SCHEMA-VERSION (1) · ERR-FILE-MISSING (2)\n"
            "  · ERR-IO (2) · ERR-PARSE (2) · ERR-FILE-TOO-LARGE (1) · ERR-USAGE (1)\n"
            "  · ERR-INTERNAL (2)"
        ),
        formatter_class=_Formatter,
        add_help=False,
    )
    p_get.path = "get"
    p_get.add_argument("-h", "--help", action=_HelpAction, help="show this help and exit")
    p_get.add_argument("ids", metavar="ID", nargs="+", help="contract ID (repeats return copies)")
    _add_global_options(p_get, mirrored=True)

    p_list = sub.add_parser(
        "list",
        help="binding summaries in file order, optionally by kind; --full for whole bindings",
        description=(
            "Print OUT-BINDING-SUMMARY rows in file order, or whole bindings with --full.\n"
            "No --kind means every binding; repeated --kind form a union; no match is an empty\n"
            "list, exit 0."
        ),
        epilog=(
            f"{_EXIT_TEXT}\n"
            "errors: ERR-SCHEMA-VERSION (1) · ERR-FILE-MISSING (2) · ERR-IO (2) · ERR-PARSE (2)\n"
            "  · ERR-FILE-TOO-LARGE (1) · ERR-USAGE (1) · ERR-INTERNAL (2)"
        ),
        formatter_class=_Formatter,
        add_help=False,
    )
    p_list.path = "list"
    p_list.add_argument("-h", "--help", action=_HelpAction, help="show this help and exit")
    p_list.add_argument(
        "--kind",
        metavar="KIND",
        action="append",
        default=[],
        help="keep bindings of this kind ([A-Z][A-Z0-9]+); repeatable, union",
    )
    p_list.add_argument("--full", action="store_true", help="whole bindings instead of summaries")
    _add_global_options(p_list, mirrored=True)

    paths = {
        "init": p_init,
        "validate": p_validate,
        "schema": p_schema,
        "get": p_get,
        "list": p_list,
    }

    def command(
        group: Any, name: str, path: str, help_text: str, description: str, errors: str
    ) -> _Parser:
        p = group.add_parser(
            name,
            help=help_text,
            description=description,
            epilog=f"{_EXIT_TEXT}\nerrors: {errors}",
            formatter_class=_Formatter,
            add_help=False,
        )
        p.path = path
        p.add_argument("-h", "--help", action=_HelpAction, help="show this help and exit")
        paths[path] = p
        return p

    write_errors = (
        "ERR-FILE-INVALID (1) · ERR-INPUT-INVALID (1) · ERR-SCHEMA-VERSION (1)\n"
        "  · ERR-FILE-MISSING (2) · ERR-IO (2) · ERR-PARSE (2) · ERR-FILE-TOO-LARGE (1)\n"
        "  · ERR-USAGE (1) · ERR-INTERNAL (2)"
    )
    p_set = command(
        sub,
        "set",
        "set",
        "create or replace a whole binding from a JSON document",
        "Upsert the binding ID from an OUT-BINDING document (--json DOC, or --json - for stdin).\n"
        "An unknown ID is appended last; a known ID is replaced in place. Comments in the\n"
        "document are set at their anchors; null or omitted means absent.",
        "ERR-USAGE for invalid/non-object JSON or a contradicting id/kind · " + write_errors,
    )
    p_set.add_argument("id", metavar="ID", help="contract ID")
    p_set.add_argument("--json", metavar="DOC", required=True, help="OUT-BINDING document, or -")
    _add_global_options(p_set, mirrored=True)

    p_add_loc = command(
        sub,
        "add-locator",
        "add-locator",
        "append a locator to a binding",
        "Append one locator (path, optional symbol, role and comment) to the binding ID.",
        "ERR-NOT-FOUND (1) · ERR-DUPLICATE (1) · " + write_errors,
    )
    p_add_loc.add_argument("id", metavar="ID", help="contract ID")
    p_add_loc.add_argument("--path", metavar="P", required=True, help="repository-relative path")
    p_add_loc.add_argument("--symbol", metavar="S", help="symbol inside the path")
    p_add_loc.add_argument("--role", choices=("producer", "consumer"), help="wire role")
    p_add_loc.add_argument("--comment", metavar="TEXT", help="comment at the locator")
    _add_global_options(p_add_loc, mirrored=True)

    p_add_field = command(
        sub,
        "add-field",
        "add-field",
        "set a field locator on a binding",
        "Set the field NAME of the binding ID (a present NAME is replaced in place, keeping\n"
        "its comment unless --comment is given; a new NAME is appended last).",
        "ERR-NOT-FOUND (1) · " + write_errors,
    )
    p_add_field.add_argument("id", metavar="ID", help="contract ID")
    p_add_field.add_argument("name", metavar="NAME", help="field name")
    p_add_field.add_argument("--path", metavar="P", required=True, help="repository-relative path")
    p_add_field.add_argument("--symbol", metavar="S", help="symbol inside the path")
    p_add_field.add_argument("--comment", metavar="TEXT", help="comment at the field")
    _add_global_options(p_add_field, mirrored=True)

    p_add_assertion = command(
        sub,
        "add-assertion",
        "add-assertion",
        "append an assertion to a binding",
        "Append one assertion: bound (--path --symbol --run) or owed (--owed), optionally with\n"
        "--arm and --comment. A partial shape or both shapes at once is ERR-USAGE.",
        "ERR-NOT-FOUND (1) · ERR-DUPLICATE (1) · " + write_errors,
    )
    p_add_assertion.add_argument("id", metavar="ID", help="contract ID")
    p_add_assertion.add_argument("--path", metavar="P", help="test file path (bound shape)")
    p_add_assertion.add_argument("--symbol", metavar="S", help="test symbol (bound shape)")
    p_add_assertion.add_argument("--run", metavar="R", help="run selector (bound shape)")
    p_add_assertion.add_argument("--owed", metavar="REF", help="owed reference (owed shape)")
    p_add_assertion.add_argument("--arm", metavar="A", help="arm label")
    p_add_assertion.add_argument("--comment", metavar="TEXT", help="comment at the assertion")
    _add_global_options(p_add_assertion, mirrored=True)

    p_remove = command(
        sub,
        "remove",
        "remove",
        "remove a binding, or one locator, field or assertion inside it",
        "Remove the whole binding ID (with its comments) or, with exactly one selector, one\n"
        "entry: --locator --path P [--symbol S] · --field NAME · --assertion (--path P\n"
        "--symbol S | --owed REF) [--arm A]. Removing the last locator leaves the stub.",
        "ERR-NOT-FOUND (1) · " + write_errors,
    )
    p_remove.add_argument("id", metavar="ID", help="contract ID")
    p_remove.add_argument(
        "--locator", action="store_true", help="select a locator by --path/--symbol"
    )
    p_remove.add_argument("--field", metavar="NAME", help="select the field NAME")
    p_remove.add_argument("--assertion", action="store_true", help="select an assertion by shape")
    p_remove.add_argument("--path", metavar="P", help="path of the selected entry")
    p_remove.add_argument("--symbol", metavar="S", help="symbol of the selected entry")
    p_remove.add_argument("--owed", metavar="REF", help="owed reference of the selected assertion")
    p_remove.add_argument("--arm", metavar="A", help="arm of the selected assertion")
    _add_global_options(p_remove, mirrored=True)

    p_cov = command(
        sub,
        "coverage",
        "coverage",
        "read or edit the coverage declaration (get · fully-bound · curated)",
        "The coverage block: `get` prints it; `fully-bound add|remove KIND` and\n"
        "`curated set|unset KIND` edit it. A group without its subcommand is ERR-USAGE.",
        "ERR-USAGE (1) · ERR-INTERNAL (2)",
    )
    _add_global_options(p_cov, mirrored=True)
    cov_sub = p_cov.add_subparsers(
        dest="group_command", metavar="<subcommand>", parser_class=_Parser
    )
    cov_sub.required = True
    p_cov_get = command(
        cov_sub,
        "get",
        "coverage get",
        "print the coverage block",
        "Print OUT-COVERAGE (empty list / empty object when the file has no coverage block).",
        "ERR-SCHEMA-VERSION (1) · ERR-FILE-MISSING (2) · ERR-IO (2) · ERR-PARSE (2)\n"
        "  · ERR-FILE-TOO-LARGE (1) · ERR-USAGE (1) · ERR-INTERNAL (2)",
    )
    _add_global_options(p_cov_get, mirrored=True)
    p_fb = command(
        cov_sub,
        "fully-bound",
        "coverage fully-bound",
        "add or remove a kind under fully_bound",
        "`add KIND` appends last (ERR-DUPLICATE if listed; ERR-INPUT-INVALID if curated);\n"
        "`remove KIND` drops it (ERR-NOT-FOUND if absent); the last one drops the key.",
        "ERR-DUPLICATE (1) · ERR-NOT-FOUND (1) · " + write_errors,
    )
    p_fb.add_argument("action", choices=("add", "remove"), help="add · remove")
    p_fb.add_argument("kind", metavar="KIND", help="kind ([A-Z][A-Z0-9]+)")
    _add_global_options(p_fb, mirrored=True)
    p_cur = command(
        cov_sub,
        "curated",
        "coverage curated",
        "set or unset a curated entry with its reason",
        "`set KIND --reason TEXT [--comment TEXT]` replaces in place or appends last\n"
        "(ERR-INPUT-INVALID if KIND is fully bound); `unset KIND` drops the entry with its\n"
        "comment (ERR-NOT-FOUND if absent).",
        "ERR-NOT-FOUND (1) · " + write_errors,
    )
    p_cur.add_argument("action", choices=("set", "unset"), help="set · unset")
    p_cur.add_argument("kind", metavar="KIND", help="kind ([A-Z][A-Z0-9]+)")
    p_cur.add_argument("--reason", metavar="TEXT", help="why it is curated (set)")
    p_cur.add_argument("--comment", metavar="TEXT", help="comment at the entry (set)")
    _add_global_options(p_cur, mirrored=True)

    p_comment = command(
        sub,
        "comment",
        "comment",
        "read, set or unset the comment at an anchor (get · set · unset)",
        "The comment at one anchor. Anchors: header · binding ID · locator ID --path P\n"
        "[--symbol S] · field ID NAME · assertion ID (--path P --symbol S | --owed REF)\n"
        "[--arm A] · coverage · curated KIND. A group without its subcommand is ERR-USAGE.",
        "ERR-USAGE (1) · ERR-INTERNAL (2)",
    )
    _add_global_options(p_comment, mirrored=True)
    cm_sub = p_comment.add_subparsers(
        dest="group_command", metavar="<subcommand>", parser_class=_Parser
    )
    cm_sub.required = True
    read_errors = (
        "ERR-NOT-FOUND (1) · ERR-SCHEMA-VERSION (1) · ERR-FILE-MISSING (2) · ERR-IO (2)\n"
        "  · ERR-PARSE (2) · ERR-FILE-TOO-LARGE (1) · ERR-USAGE (1) · ERR-INTERNAL (2)"
    )
    for action, help_text, description, errors in (
        (
            "get",
            "print the comment at an anchor",
            "Print OUT-COMMENT for the anchor; ERR-NOT-FOUND when the target or its comment is\n"
            "absent.",
            read_errors,
        ),
        (
            "set",
            "set the comment at an anchor (--text)",
            "Replace the comment at the anchor with --text (newlines make a block above; a\n"
            "single line trails its entry). Trailing whitespace, empty edge lines, only empty\n"
            "lines or a control character are ERR-INPUT-INVALID (INV-COMMENT-TEXT).",
            "ERR-NOT-FOUND (1) · " + write_errors,
        ),
        (
            "unset",
            "remove the comment at an anchor",
            "Remove the comment at the anchor; ERR-NOT-FOUND when there is none.",
            "ERR-NOT-FOUND (1) · " + write_errors,
        ),
    ):
        p_action = command(cm_sub, action, f"comment {action}", help_text, description, errors)
        p_action.add_argument(
            "anchor",
            metavar="ANCHOR",
            choices=("header", "binding", "locator", "field", "assertion", "coverage", "curated"),
            help="header · binding · locator · field · assertion · coverage · curated",
        )
        p_action.add_argument(
            "target", metavar="ID|KIND", nargs="?", help="binding ID, or KIND for curated"
        )
        p_action.add_argument("name", metavar="NAME", nargs="?", help="field name (field anchor)")
        p_action.add_argument("--path", metavar="P", help="locator / bound-assertion path")
        p_action.add_argument("--symbol", metavar="S", help="locator / bound-assertion symbol")
        p_action.add_argument("--owed", metavar="REF", help="owed-assertion reference")
        p_action.add_argument("--arm", metavar="A", help="assertion arm")
        if action == "set":
            p_action.add_argument("--text", metavar="TEXT", required=True, help="comment text")
        _add_global_options(p_action, mirrored=True)

    parser.subparsers_by_name.update(paths)
    return parser


_KIND_RE = re.compile(KIND_PATTERN)


def parse(parser: _Parser, args: Sequence[str]) -> argparse.Namespace:
    """parse_args whose unrecognised-argument error names the deepest level reached, plus the
    command-line grammar checks argparse cannot express (IDs and kinds)."""
    ns, extras = parser.parse_known_args(args)
    deepest = _deepest(parser, ns)

    def usage(message: str) -> UsageError:
        return UsageError(message, deepest.format_help(), deepest.path)

    if extras:
        raise usage(f"unrecognized arguments: {' '.join(extras)}")
    ids = getattr(ns, "ids", None) or ([ns.id] if getattr(ns, "id", None) else [])
    for contract_id in ids:
        if not is_contract_id(contract_id):
            raise usage(f"`{contract_id}` is not a contract ID")
    kinds = getattr(ns, "kind", None)
    for kind in [kinds] if isinstance(kinds, str) else kinds or []:
        if not _KIND_RE.match(kind):
            raise usage(f"`{kind}` is not a kind (expected {KIND_PATTERN})")
    if ns.command == "add-assertion":
        _check_assertion_shape(ns, usage, run_applies=True)
    elif ns.command == "remove":
        selectors = [ns.locator, ns.field is not None, ns.assertion]
        if sum(selectors) > 1:
            raise usage("--locator, --field and --assertion are mutually exclusive")
        if ns.locator and ns.path is None:
            raise usage("--locator needs --path")
        if ns.assertion:
            _check_assertion_shape(ns, usage, run_applies=False)
        if not any(selectors) and any(v is not None for v in (ns.path, ns.symbol, ns.owed, ns.arm)):
            raise usage("--path/--symbol/--owed/--arm need --locator or --assertion")
        if ns.field is not None and any(
            v is not None for v in (ns.path, ns.symbol, ns.owed, ns.arm)
        ):
            raise usage("--field takes no --path/--symbol/--owed/--arm")
    elif ns.command == "set":
        ns.document = _json_document(ns, usage)
    elif ns.command == "comment" and ns.group_command:
        _check_anchor(ns, usage)
    elif ns.command == "coverage" and ns.group_command == "curated":
        if ns.action == "set" and ns.reason is None:
            raise usage("curated set needs --reason")
        if ns.action == "unset" and (ns.reason is not None or ns.comment is not None):
            raise usage("curated unset takes no --reason/--comment")
    ns.command_path = deepest.path
    return ns


def _check_anchor(ns: argparse.Namespace, usage: Callable[[str], UsageError]) -> None:
    """The anchor grammar of the comment commands (Interfaces, Global conventions)."""
    kind = ns.anchor
    options = [v is not None for v in (ns.path, ns.symbol, ns.owed, ns.arm)]
    if kind in ("header", "coverage"):
        if ns.target is not None or ns.name is not None or any(options):
            raise usage(f"anchor `{kind}` takes no identity")
        return
    if ns.target is None:
        raise usage(f"anchor `{kind}` needs its {'KIND' if kind == 'curated' else 'ID'}")
    if kind == "curated":
        if not _KIND_RE.match(ns.target):
            raise usage(f"`{ns.target}` is not a kind (expected {KIND_PATTERN})")
        if ns.name is not None or any(options):
            raise usage("anchor `curated` takes only its KIND")
        return
    if not is_contract_id(ns.target):
        raise usage(f"`{ns.target}` is not a contract ID")
    if kind == "binding":
        if ns.name is not None or any(options):
            raise usage("anchor `binding` takes only its ID")
    elif kind == "locator":
        if ns.path is None or ns.name is not None or ns.owed is not None or ns.arm is not None:
            raise usage("anchor `locator` is ID --path P [--symbol S]")
    elif kind == "field":
        if ns.name is None or any(options):
            raise usage("anchor `field` is ID NAME")
    else:
        if ns.name is not None:
            raise usage("anchor `assertion` takes no NAME")
        _check_assertion_shape(ns, usage, run_applies=False)


def _deepest(parser: _Parser, ns: argparse.Namespace) -> _Parser:
    parts = [ns.command, getattr(ns, "group_command", None)]
    path = ""
    deepest = parser
    for part in parts:
        if not part:
            break
        path = f"{path} {part}".strip()
        deepest = parser.subparsers_by_name.get(path, deepest)
    return deepest


def _check_assertion_shape(
    ns: argparse.Namespace, usage: Callable[[str], UsageError], *, run_applies: bool
) -> None:
    bound = [ns.path, ns.symbol] + ([ns.run] if run_applies else [])
    if ns.owed is not None and any(v is not None for v in bound):
        raise usage("an assertion is bound (--path --symbol --run) or owed (--owed), not both")
    if any(v is not None for v in bound) and not all(v is not None for v in bound):
        names = "--path --symbol --run" if run_applies else "--path --symbol"
        raise usage(f"a bound assertion needs all of {names}")
    if ns.owed is None and not any(v is not None for v in bound):
        raise usage("an assertion needs its bound shape or --owed")


def _anchor_of(ns: argparse.Namespace) -> Anchor:
    """The anchor an input comment is meant for, from the parsed anchor arguments."""
    if ns.anchor in ("header", "coverage"):
        return Anchor(ns.anchor)
    if ns.anchor == "curated":
        return Anchor("curated", kind=ns.target)
    return Anchor(
        ns.anchor,
        id=ns.target,
        path=ns.path,
        symbol=ns.symbol,
        owed=ns.owed,
        arm=ns.arm,
        field=ns.name,
    )


def _json_document(ns: argparse.Namespace, usage: Callable[[str], UsageError]) -> dict[str, Any]:
    text = sys.stdin.read() if ns.json == "-" else ns.json
    try:
        doc = json.loads(text)
    except ValueError as exc:
        raise usage(f"--json is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise usage("--json must be a JSON object (OUT-BINDING)")
    if "id" in doc and doc["id"] is not None and doc["id"] != ns.id:
        raise usage(f"document id `{doc['id']}` contradicts the positional ID `{ns.id}`")
    if "kind" in doc and doc["kind"] is not None and doc["kind"] != kind_of(ns.id):
        raise usage(f"document kind `{doc['kind']}` contradicts the ID's kind `{kind_of(ns.id)}`")
    return doc


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

    def _load(self, *, gate_schema_version: bool) -> Map:
        """Loader + pre-validation. Every reader but `validate` refuses another schema major
        before any other work (ERR-SCHEMA-VERSION)."""
        m, loaded = loader.load(self.ns.file, size_limit=not self.ns.no_size_limit)
        if gate_schema_version and m.schema_version != schema.SCHEMA_VERSION:
            self.pre = validator.finalize(loaded)
            raise SchemaVersionError(m.schema_version, schema.SCHEMA_VERSION)
        self.pre = validator.finalize(
            loaded + validator.validate(m, check_paths=self.ns.check_paths, root=os.getcwd())
        )
        return m

    def validate(self) -> dict[str, Any]:
        self._load(gate_schema_version=False)
        return cmd_validate.result(self.pre, paths_checked=self.ns.check_paths)

    def get(self) -> dict[str, Any]:
        return cmd_query.get(self._load(gate_schema_version=True), self.ns.ids)

    def list(self) -> dict[str, Any]:
        m = self._load(gate_schema_version=True)
        return cmd_query.list_bindings(m, self.ns.kind, full=self.ns.full)

    # -- writes: PATTERN-VALIDATE-AROUND-WRITE -----------------------------------------

    def _write(self, mutate: Callable[[Map], dict[str, Any]]) -> dict[str, Any]:
        m = self._load(gate_schema_version=True)
        if _exit_for(self.pre):
            raise FileInvalidError([f for f in self.pre if f.severity == "error"])
        result = mutate(m)
        self.post = validator.finalize(
            validator.validate(m, check_paths=self.ns.check_paths, root=os.getcwd())
        )
        if _exit_for(self.post):  # pragma: no cover — valid model + valid input; a tool bug
            raise InternalError(
                "post-validation failed",
                "; ".join(f.code for f in self.post if f.severity == "error"),
            )
        emitter.write(m, loader.resolve_target(self.ns.file))
        return result

    def _input(
        self, value: Any, node: str, *, binding_id: str = "", name: str = "", kind: str = ""
    ) -> Any:
        """validate_input, then the converted object; any error is ERR-INPUT-INVALID."""
        findings = validator.finalize(
            validator.validate_input(
                value,
                node,
                binding_id=binding_id,
                name=name,
                kind=kind,
                check_paths=self.ns.check_paths,
                root=os.getcwd(),
            )
        )
        if _exit_for(findings):
            raise InputInvalidError(findings)
        obj, _ = model.from_input(value, node, binding_id=binding_id, name=name, kind=kind)
        return obj

    def set(self) -> dict[str, Any]:
        b = self._input(self.ns.document, "binding", binding_id=self.ns.id)
        return self._write(lambda m: cmd_set.result(cmd_set.apply(m, b)))

    def add_locator(self) -> dict[str, Any]:
        value = {
            "path": self.ns.path,
            "symbol": self.ns.symbol,
            "role": self.ns.role,
            "comment": self.ns.comment,
        }
        loc = self._input(value, "locator", binding_id=self.ns.id)
        return self._write(lambda m: cmd_set.result(cmd_add.locator(m, self.ns.id, loc)))

    def add_field(self) -> dict[str, Any]:
        value = {"path": self.ns.path, "symbol": self.ns.symbol, "comment": self.ns.comment}
        fl = self._input(value, "field_locator", binding_id=self.ns.id, name=self.ns.name)
        return self._write(
            lambda m: cmd_set.result(
                cmd_add.field(
                    m, self.ns.id, self.ns.name, fl, comment_given=self.ns.comment is not None
                )
            )
        )

    def add_assertion(self) -> dict[str, Any]:
        value = {
            "path": self.ns.path,
            "symbol": self.ns.symbol,
            "run": self.ns.run,
            "arm": self.ns.arm,
            "owed": self.ns.owed,
            "comment": self.ns.comment,
        }
        a = self._input(value, "assertion", binding_id=self.ns.id)
        return self._write(lambda m: cmd_set.result(cmd_add.assertion(m, self.ns.id, a)))

    def remove(self) -> dict[str, Any]:
        ns = self.ns
        if ns.locator:
            return self._write(
                lambda m: cmd_set.result(cmd_remove.locator(m, ns.id, ns.path, ns.symbol))
            )
        if ns.field is not None:
            return self._write(lambda m: cmd_set.result(cmd_remove.field(m, ns.id, ns.field)))
        if ns.assertion:
            identity = (
                ("owed", ns.owed, ns.arm)
                if ns.owed is not None
                else ("bound", ns.path, ns.symbol, ns.arm)
            )
            return self._write(lambda m: cmd_set.result(cmd_remove.assertion(m, ns.id, identity)))
        return self._write(lambda m: cmd_remove.binding(m, ns.id))

    def comment(self) -> dict[str, Any]:
        ns = self.ns

        def target(m: Map) -> cmd_comment.Target:
            return cmd_comment.resolve(
                m,
                ns.anchor,
                ns.target,
                ns.name,
                path=ns.path,
                symbol=ns.symbol,
                owed=ns.owed,
                arm=ns.arm,
            )

        if ns.group_command == "get":
            return cmd_comment.get(target(self._load(gate_schema_version=True)))
        if ns.group_command == "unset":
            return self._write(lambda m: cmd_comment.unset(target(m)))
        findings = validator.finalize(
            validator.validate_input(ns.text, "comment", anchor=_anchor_of(ns))
        )
        if _exit_for(findings):
            raise InputInvalidError(findings)
        return self._write(lambda m: cmd_comment.set_text(target(m), ns.text))

    def coverage(self) -> dict[str, Any]:
        ns = self.ns
        if ns.group_command == "get":
            return cmd_coverage.result(self._load(gate_schema_version=True))
        if ns.group_command == "fully-bound":
            if ns.action == "add":
                return self._write(
                    lambda m: cmd_coverage.result(cmd_coverage.fully_bound_add(m, ns.kind))
                )
            return self._write(
                lambda m: cmd_coverage.result(cmd_coverage.fully_bound_remove(m, ns.kind))
            )
        if ns.action == "set":
            entry = self._input(
                {"reason": ns.reason, "comment": ns.comment}, "curated", kind=ns.kind
            )
            return self._write(
                lambda m: cmd_coverage.result(
                    cmd_coverage.curated_set(
                        m, ns.kind, entry, comment_given=ns.comment is not None
                    )
                )
            )
        return self._write(lambda m: cmd_coverage.result(cmd_coverage.curated_unset(m, ns.kind)))


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
        command = ns.command_path
        if command == "schema":
            _write_stdout(
                schema.checksum() + "\n" if ns.checksum else schema.schema_json().decode("utf-8")
            )
            return 0
        run = _Run(ns)
        result = getattr(run, ns.command.replace("-", "_"))()
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
