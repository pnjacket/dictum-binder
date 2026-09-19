"""Contract tier for CLI-FORMAT / OUT-FORMAT-RESULT, ADR-FORMAT-ONLY-REORDERS (proof), and
ERR-FILE-INVALID's `format` forcing owed from slice 3."""

from __future__ import annotations

import os
import unittest

from lspd import emitter, loader
from tests._helpers import TempDir, copy_fixture, read_bytes, run_cli

SORTED_NONCANONICAL = (
    "schema_version: 1\n\nbindings:\n\n  ENTITY-A:\n    locators:\n"
    "      - { path: src/a.py, symbol: A }\n\n"
    "  ROUTE-B:\n    locators:\n      - { path: web/b.ts, symbol: B }\n\ncoverage:\n"
    "  fully_bound: [ENTITY, ROUTE]\n"
)


class Format(unittest.TestCase):
    """DICT: CLI-FORMAT / OUT-FORMAT-RESULT"""

    def test_rewrites_sorted_canonical_and_is_idempotent(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture("noncanonical.yaml", tmp)
            run = run_cli(["format"], cwd=tmp)
            env = run.envelope
            self.assertEqual((run.code, env["ok"], env["command"]), (0, True, "format"), run.stdout)
            self.assertEqual(env["result"], {"changed": True, "checked_only": False})
            self.assertEqual(read_bytes(target).decode("utf-8"), SORTED_NONCANONICAL)
            again = run_cli(["format"], cwd=tmp)
            self.assertEqual(
                (again.code, again.envelope["result"]),
                (0, {"changed": False, "checked_only": False}),
            )
            self.assertEqual(read_bytes(target).decode("utf-8"), SORTED_NONCANONICAL)

    def test_check_never_writes_and_exits_1_iff_it_would_change(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture("noncanonical.yaml", tmp)
            before = read_bytes(target)
            run = run_cli(["format", "--check"], cwd=tmp)
            env = run.envelope
            self.assertEqual((run.code, env["ok"], env["error"]), (1, True, None))
            self.assertEqual(env["result"], {"changed": True, "checked_only": True})
            self.assertEqual(read_bytes(target), before)
            self.assertEqual(sorted(os.listdir(tmp)), ["bindings.yaml"])
            run_cli(["format"], cwd=tmp)
            clean = run_cli(["format", "--check"], cwd=tmp)
            self.assertEqual(
                (clean.code, clean.envelope["result"]),
                (0, {"changed": False, "checked_only": True}),
            )

    def test_only_format_reorders_and_only_the_top_level_lists(self) -> None:
        """DICT: ADR-FORMAT-ONLY-REORDERS — bindings, fully_bound and curated sort; locators,
        fields and assertions keep the author's order; comments stay at their anchors."""
        with TempDir() as tmp:
            target = copy_fixture("canonical.yaml", tmp)
            run_cli(
                [
                    "set",
                    "API-Z",
                    "--json",
                    '{"locators": [{"path": "z.py", "symbol": "Z", "comment": "zc"},'
                    ' {"path": "a.py"}]}',
                ],
                cwd=tmp,
            )
            run_cli(["coverage", "fully-bound", "add", "CAP"], cwd=tmp)
            run_cli(
                ["coverage", "curated", "set", "ADR", "--reason", "r", "--comment", "ac"], cwd=tmp
            )
            m_before, _ = loader.load(target)
            self.assertEqual(
                list(m_before.bindings),
                ["ENTITY-PROJECT", "ENTITY-USER", "ROUTE-HOME", "SCREEN-STUB", "API-Z"],
            )
            run = run_cli(["format"], cwd=tmp)
            self.assertEqual((run.code, run.envelope["result"]["changed"]), (0, True))
            m, findings = loader.load(target)
            self.assertEqual(findings, [])
            self.assertEqual(
                list(m.bindings),
                ["API-Z", "ENTITY-PROJECT", "ENTITY-USER", "ROUTE-HOME", "SCREEN-STUB"],
            )
            assert m.coverage is not None and m.coverage.curated is not None
            self.assertEqual(m.coverage.fully_bound, ["CAP", "ENTITY", "INV", "ROUTE"])
            self.assertEqual(list(m.coverage.curated), ["ADR", "API"])
            self.assertEqual(m.coverage.curated["ADR"].comment, "ac")
            self.assertEqual([loc.path for loc in m.bindings["API-Z"].locators], ["z.py", "a.py"])
            self.assertEqual(m.bindings["API-Z"].locators[0].comment, "zc")
            self.assertEqual(list(m.bindings["ENTITY-USER"].fields or {}), ["email", "config"])
            self.assertEqual(
                [a.owed for a in m.bindings["ENTITY-USER"].asserted_by or []][-2:],
                ["slice-9", "slice-9"],
            )
            self.assertEqual(m.header_comment, m_before.header_comment)
            self.assertEqual(
                m.bindings["ENTITY-USER"].comment, m_before.bindings["ENTITY-USER"].comment
            )
            self.assertEqual(read_bytes(target), emitter.emit(m))

    def test_layout_warnings_are_repaired_and_other_warnings_kept(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture("inv-bytes.yaml", tmp)
            run = run_cli(["format"], cwd=tmp)
            self.assertEqual(run.code, 0, run.stdout)
            self.assertIn("INV-BYTES", [f["code"] for f in run.envelope["findings"]["pre"]])
            self.assertEqual(run_cli(["validate"], cwd=tmp).envelope["result"]["warnings"], 0)
            copy_fixture("inv-role-requires-wire.yaml", tmp)
            run = run_cli(["format"], cwd=tmp)
            self.assertEqual(run.code, 0)
            self.assertEqual(
                [f["code"] for f in run.envelope["findings"]["post"]], ["INV-ROLE-REQUIRES-WIRE"]
            )
            self.assertEqual(run_cli(["validate"], cwd=tmp).envelope["result"]["warnings"], 1)
            self.assertEqual(read_bytes(target), emitter.emit(loader.load(target)[0]))

    def test_error_level_findings_refuse_it_under_both_modes(self) -> None:
        """DICT: ERR-FILE-INVALID (format forcing)"""
        with TempDir() as tmp:
            target = copy_fixture("inv-no-line-numbers.yaml", tmp)
            before = read_bytes(target)
            for argv in (["format"], ["format", "--check"]):
                run = run_cli(argv, cwd=tmp)
                env = run.envelope
                self.assertEqual(
                    (run.code, env["ok"], env["error"]["code"]),
                    (1, False, "ERR-FILE-INVALID"),
                    argv,
                )
                self.assertEqual(env["result"], None)
                self.assertEqual(read_bytes(target), before)
            copy_fixture("inv-path-exists.yaml", tmp)
            before = read_bytes(target)
            self.assertEqual(run_cli(["format", "--check"], cwd=tmp).code, 0)
            checked = run_cli(["--check-paths", "format"], cwd=tmp)
            self.assertEqual(checked.envelope["error"]["code"], "ERR-FILE-INVALID")
            self.assertEqual(
                [f["code"] for f in checked.envelope["error"]["details"]["findings"]],
                ["INV-PATH-EXISTS"],
            )
            self.assertEqual(read_bytes(target), before)
            copy_fixture("inv-schema-version.yaml", tmp)
            self.assertEqual(
                run_cli(["format"], cwd=tmp).envelope["error"]["code"], "ERR-SCHEMA-VERSION"
            )


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
