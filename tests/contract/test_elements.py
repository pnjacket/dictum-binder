"""Contract tier for the slice-1 elements.

CLI-INIT, CLI-VALIDATE, CLI-SCHEMA, CLI-HELP, CLI-VERSION.
"""

from __future__ import annotations

import json
import os
import re
import stat
import unittest

from lspd import schema
from tests._helpers import TempDir, copy_fixture, read_bytes, run_cli

ENVELOPE_KEYS = ["lspd", "ok", "command", "result", "findings", "error"]


class Init(unittest.TestCase):
    """DICT: CLI-INIT"""

    def test_creates_the_canonical_empty_map(self) -> None:
        with TempDir() as tmp:
            run = run_cli(["init"], cwd=tmp)
            self.assertEqual(run.code, 0)
            env = run.envelope
            self.assertEqual(list(env), ENVELOPE_KEYS)
            self.assertEqual(env["command"], "init")
            self.assertEqual(
                env["result"], {"path": os.path.realpath(os.path.join(tmp, "bindings.yaml"))}
            )
            self.assertEqual(env["findings"], {"pre": [], "post": []})
            self.assertEqual(
                read_bytes(os.path.join(tmp, "bindings.yaml")),
                b"schema_version: 1\n\nbindings: {}\n",
            )
            self.assertEqual(run.stderr, "")

    def test_refuses_an_existing_target(self) -> None:
        with TempDir() as tmp:
            self.assertEqual(run_cli(["init"], cwd=tmp).code, 0)
            run = run_cli(["init"], cwd=tmp)
            self.assertEqual(run.code, 1)
            self.assertEqual(run.envelope["error"]["code"], "ERR-FILE-EXISTS")
            self.assertEqual(sorted(run.envelope["error"]["details"]), ["path", "reason"])

    def test_file_option_before_or_after_the_command(self) -> None:
        with TempDir() as tmp:
            a = run_cli(["--file", "a.yaml", "init"], cwd=tmp)
            b = run_cli(["init", "--file", "b.yaml"], cwd=tmp)
            self.assertEqual((a.code, b.code), (0, 0))
            self.assertEqual(sorted(os.listdir(tmp)), ["a.yaml", "b.yaml"])

    def test_dangling_symlink_target_is_created_through(self) -> None:
        with TempDir() as tmp:
            link = os.path.join(tmp, "bindings.yaml")
            os.symlink(os.path.join(tmp, "real.yaml"), link)
            run = run_cli(["init"], cwd=tmp)
            self.assertEqual(run.code, 0)
            self.assertTrue(os.path.islink(link))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "real.yaml")))
            self.assertEqual(
                run.envelope["result"]["path"], os.path.realpath(os.path.join(tmp, "real.yaml"))
            )

    def test_unwritable_location_is_io_error(self) -> None:
        with TempDir() as tmp:
            run = run_cli(["--file", "missing/bindings.yaml", "init"], cwd=tmp)
            self.assertEqual(run.code, 2)
            self.assertEqual(run.envelope["error"]["code"], "ERR-IO")

    def test_mode_is_umask_default(self) -> None:
        with TempDir() as tmp:
            old = os.umask(0o022)
            try:
                run_cli(["init"], cwd=tmp)
            finally:
                os.umask(old)
            self.assertEqual(
                stat.S_IMODE(os.stat(os.path.join(tmp, "bindings.yaml")).st_mode), 0o644
            )


class Validate(unittest.TestCase):
    """DICT: CLI-VALIDATE"""

    def test_clean_file(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual(run.code, 0)
            self.assertEqual(
                run.envelope["result"], {"errors": 0, "warnings": 0, "paths_checked": False}
            )
            self.assertTrue(run.envelope["ok"])

    def test_error_findings_exit_1_with_ok_true(self) -> None:
        with TempDir() as tmp:
            copy_fixture("inv-no-line-numbers.yaml", tmp)
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual(run.code, 1)
            env = run.envelope
            self.assertTrue(env["ok"])
            self.assertIsNone(env["error"])
            self.assertEqual(env["result"]["errors"], 1)
            finding = env["findings"]["pre"][0]
            self.assertEqual(list(finding), ["code", "severity", "anchor", "message"])
            self.assertEqual(finding["code"], "INV-NO-LINE-NUMBERS")
            self.assertEqual(
                list(finding["anchor"]),
                ["type", "id", "path", "symbol", "arm", "owed", "field", "kind"],
            )
            self.assertEqual(finding["anchor"]["type"], "locator")
            self.assertEqual(env["findings"]["post"], [])

    def test_warnings_exit_0(self) -> None:
        with TempDir() as tmp:
            copy_fixture("inv-bytes.yaml", tmp)
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual(run.code, 0)
            self.assertEqual(run.envelope["result"]["warnings"], 1)

    def test_schema_version_mismatch_is_a_finding_not_an_error(self) -> None:
        with TempDir() as tmp:
            copy_fixture("inv-schema-version.yaml", tmp)
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual(run.code, 1)
            self.assertTrue(run.envelope["ok"])
            self.assertEqual(run.envelope["findings"]["pre"][0]["code"], "INV-SCHEMA-VERSION")

    def test_check_paths(self) -> None:
        with TempDir() as tmp:
            copy_fixture("inv-path-exists.yaml", tmp)
            plain = run_cli(["validate"], cwd=tmp)
            self.assertEqual((plain.code, plain.envelope["result"]["paths_checked"]), (0, False))
            checked = run_cli(["--check-paths", "validate"], cwd=tmp)
            self.assertEqual((checked.code, checked.envelope["result"]["paths_checked"]), (1, True))
            self.assertEqual(checked.envelope["findings"]["pre"][0]["code"], "INV-PATH-EXISTS")
            os.makedirs(os.path.join(tmp, "no", "such"))
            with open(os.path.join(tmp, "no", "such", "file.py"), "w", encoding="utf-8") as handle:
                handle.write("")
            self.assertEqual(run_cli(["validate", "--check-paths"], cwd=tmp).code, 0)

    def test_size_cap_and_lift(self) -> None:
        """The cap is inclusive at exactly 10 MiB; --no-size-limit skips the size gate.

        The large files open with a BOM so that passing the size gate surfaces as ERR-PARSE at
        the byte layer, which keeps the boundary proof free of a 10 MiB pure-Python YAML scan.
        """
        cap = 10 * 1024 * 1024
        with TempDir() as tmp:
            path = os.path.join(tmp, "bindings.yaml")
            with open(path, "wb") as handle:
                handle.write(b"\xef\xbb\xbf# " + b"x" * (cap + 1 - 6) + b"\n")
            self.assertEqual(os.path.getsize(path), cap + 1)
            run = run_cli(["validate"], cwd=tmp)
            self.assertEqual((run.code, run.envelope["error"]["code"]), (1, "ERR-FILE-TOO-LARGE"))
            self.assertIn("--no-size-limit", run.envelope["error"]["message"])
            lifted = run_cli(["--no-size-limit", "validate"], cwd=tmp)
            self.assertEqual((lifted.code, lifted.envelope["error"]["code"]), (2, "ERR-PARSE"))
            with open(path, "wb") as handle:
                handle.write(b"\xef\xbb\xbf# " + b"x" * (cap - 6) + b"\n")
            self.assertEqual(os.path.getsize(path), cap)
            at_cap = run_cli(["validate"], cwd=tmp)
            self.assertEqual((at_cap.code, at_cap.envelope["error"]["code"]), (2, "ERR-PARSE"))
            body = b"schema_version: 1\n\nbindings: {}\n"
            with open(path, "wb") as handle:
                handle.write(b"# " + b"x" * 4096 + b"\n" + body)
            self.assertEqual(run_cli(["--no-size-limit", "validate"], cwd=tmp).code, 0)


class Schema(unittest.TestCase):
    """DICT: CLI-SCHEMA"""

    def test_raw_schema_and_checksum(self) -> None:
        raw = run_cli(["schema"])
        self.assertEqual(raw.code, 0)
        self.assertEqual(raw.stdout.encode("utf-8"), schema.schema_json())
        self.assertEqual(
            json.loads(raw.stdout)["title"], "Dictum binding map (lspd canonical shape)"
        )
        checksum = run_cli(["schema", "--checksum"])
        self.assertEqual(checksum.code, 0)
        self.assertRegex(checksum.stdout, r"^[0-9a-f]{64}\n$")
        self.assertEqual(checksum.stdout.strip(), schema.checksum())
        with TempDir() as tmp:  # reads no file
            self.assertEqual(run_cli(["schema", "--human"], cwd=tmp).stdout, raw.stdout)


class HelpAndVersion(unittest.TestCase):
    """DICT: CLI-HELP / CLI-VERSION"""

    def test_help_at_every_level_is_plain_text(self) -> None:
        for argv in (
            ["--help"],
            ["init", "--help"],
            ["validate", "-h"],
            ["schema", "--help"],
            ["get", "--help"],
            ["list", "--help"],
            ["set", "--help"],
            ["add-locator", "--help"],
            ["add-field", "--help"],
            ["add-assertion", "--help"],
            ["remove", "--help"],
            ["coverage", "--help"],
            ["coverage", "get", "--help"],
            ["coverage", "fully-bound", "--help"],
            ["coverage", "curated", "--help"],
            ["comment", "--help"],
            ["comment", "get", "--help"],
            ["comment", "set", "--help"],
            ["comment", "unset", "--help"],
            ["format", "--help"],
        ):
            with self.subTest(argv=argv):
                run = run_cli(argv)
                self.assertEqual(run.code, 0)
                self.assertTrue(run.stdout.startswith("usage: lspd"))
                self.assertIn("exit codes:", run.stdout)
                with self.assertRaises(json.JSONDecodeError):
                    json.loads(run.stdout)
        top = run_cli(["--help"]).stdout
        for option in (
            "--file",
            "--human",
            "--check-paths",
            "--no-size-limit",
            "--debug",
            "--version",
        ):
            self.assertIn(option, top)
        self.assertIn("Targets Dictum v1.2.0 binding maps", top)
        self.assertTrue(all(len(line) <= 100 for line in top.split("\n")), top)

    def test_version(self) -> None:
        run = run_cli(["--version"])
        self.assertEqual(run.code, 0)
        self.assertRegex(run.stdout, r"^lspd \d+\.\d+\.\d+(\.dev\d+)?\n$")

    def test_help_on_unknown_command_is_usage_error(self) -> None:
        run = run_cli(["bogus", "--help"])
        self.assertEqual(run.code, 1)
        self.assertEqual(run.envelope["error"]["code"], "ERR-USAGE")


class Envelope(unittest.TestCase):
    """DICT: OUT-ENVELOPE / PATTERN-OUTPUT-MODE"""

    def test_compact_single_document_with_fixed_key_order(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            run = run_cli(["validate"], cwd=tmp)
            self.assertTrue(run.stdout.startswith('{"lspd":{"version":"'))
            self.assertEqual(run.stdout.count("\n"), 1)
            self.assertTrue(run.stdout.endswith("}\n"))
            self.assertNotIn(": ", run.stdout.split('"message"')[0])
            self.assertEqual(run.envelope["lspd"]["schema_version"], 1)
            self.assertEqual(
                run.envelope["lspd"]["version"], run_cli(["--version"]).stdout.split()[1]
            )

    def test_utf8_bytes_survive_non_ascii_comments(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "bindings.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\n\nbindings:\n\n  ENTITY-A:\n    locators:\n"
                    "      - { path: src/x.py:41, symbol: é }\n"
                )
            run = run_cli(["validate"], cwd=tmp)
            self.assertIn("é", run.stdout)
            self.assertNotIn("\\u00e9", run.stdout)

    def test_human_rendering_minimums(self) -> None:
        with TempDir() as tmp:
            copy_fixture("inv-no-line-numbers.yaml", tmp)
            json_run = run_cli(["validate"], cwd=tmp)
            human = run_cli(["--human", "validate"], cwd=tmp)
            self.assertEqual(human.code, json_run.code)
            with self.assertRaises(json.JSONDecodeError):
                json.loads(human.stdout)
            for finding in json_run.envelope["findings"]["pre"]:
                self.assertIn(finding["code"], human.stdout)
                self.assertIn(finding["message"], human.stdout)
            error = run_cli(["--human", "validate", "--file", "nope.yaml"], cwd=tmp)
            self.assertIn("ERR-FILE-MISSING", error.stdout)
            self.assertIn("run `lspd init`", error.stdout)
            usage = run_cli(["--human"], cwd=tmp)
            self.assertIn("usage:", usage.stdout)
            self.assertIn("ERR-USAGE", usage.stdout)
            self.assertEqual(usage.code, 1)

    def test_debug_adds_a_traceback_only_on_stderr(self) -> None:
        with TempDir() as tmp:
            quiet = run_cli(["validate"], cwd=tmp)
            self.assertEqual(quiet.stderr, "")
            loud = run_cli(["--debug", "validate"], cwd=tmp)
            self.assertIn("Traceback", loud.stderr)
            self.assertEqual(loud.stdout, quiet.stdout)
            self.assertEqual(loud.code, 2)
            usage = run_cli(["--debug", "bogus"], cwd=tmp)
            self.assertIn("Traceback", usage.stderr)
            self.assertEqual(usage.envelope["error"]["code"], "ERR-USAGE")
            ok = run_cli(["--debug", "init"], cwd=tmp)
            self.assertEqual((ok.code, ok.stderr), (0, ""))

    def test_help_text_is_environment_independent(self) -> None:
        with TempDir() as tmp:
            baseline = run_cli(["--help"])
            saved = dict(os.environ)
            try:
                os.environ.clear()
                os.environ["COLUMNS"] = "20"
                with open(os.path.join(tmp, ".lspdrc"), "w", encoding="utf-8") as handle:
                    handle.write("hostile\n")
                again = run_cli(["--help"], cwd=tmp)
            finally:
                os.environ.clear()
                os.environ.update(saved)
            self.assertEqual(again.stdout, baseline.stdout)
            self.assertEqual(re.sub(r"\s+", " ", again.stdout).count("usage: lspd"), 1)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
