"""Contract tier for the slice-3 elements: set, add-*, remove, coverage; the write-path patterns
(validate-around-write, atomic replace), INV-ORDER-PRESERVED, and the ERR-* rows they force."""

from __future__ import annotations

import io
import json
import unittest
from typing import Any
from unittest import mock

from dbind import emitter, loader
from tests._helpers import TempDir, copy_fixture, read_bytes, run_cli

CANON = "canonical.yaml"


def _lines(path: str) -> list[str]:
    return read_bytes(path).decode("utf-8").split("\n")


def _is_subsequence(needle: list[str], hay: list[str]) -> bool:
    it = iter(hay)
    return all(any(line == h for h in it) for line in needle)


def _codes(env: dict[str, Any], phase: str) -> list[str]:
    return [f["code"] for f in env["findings"][phase]]


class Set(unittest.TestCase):
    """DICT: CLI-SET / OUT-WRITE-RESULT"""

    def test_create_appends_last_and_replace_keeps_place(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = _lines(target)
            doc = {"locators": [{"path": "src/new.py", "symbol": "New", "comment": "fresh"}]}
            run = run_cli(["set", "INV-NEW", "--json", json.dumps(doc)], cwd=tmp)
            env = run.envelope
            self.assertEqual((run.code, env["ok"], env["command"]), (0, True, "set"))
            self.assertEqual(list(env["result"]), ["binding"])
            self.assertEqual(env["result"]["binding"]["id"], "INV-NEW")
            self.assertEqual(env["result"]["binding"]["locators"][0]["comment"], "fresh")
            ids = [r["id"] for r in run_cli(["list"], cwd=tmp).envelope["result"]["bindings"]]
            self.assertEqual(ids[-1], "INV-NEW")
            after = _lines(target)
            self.assertTrue(_is_subsequence(before, after))
            self.assertIn("      - { path: src/new.py, symbol: New } # fresh", after)
            replaced = run_cli(
                ["set", "ROUTE-HOME", "--json", '{"locators": [], "comment": "now a stub"}'],
                cwd=tmp,
            )
            self.assertEqual(replaced.code, 0)
            ids2 = [r["id"] for r in run_cli(["list"], cwd=tmp).envelope["result"]["bindings"]]
            self.assertEqual(ids2, ids)
            got = run_cli(["get", "ROUTE-HOME"], cwd=tmp).envelope["result"]["bindings"][0]
            self.assertEqual((got["locators"], got["comment"]), ([], "now a stub"))

    def test_omitted_equals_null_and_comments_clear(self) -> None:
        with TempDir() as tmp:
            copy_fixture("carriers.yaml", tmp)
            doc = {
                "id": "ENTITY-A",
                "kind": "ENTITY",
                "comment": None,
                "locators": [{"path": "src/a.py", "symbol": "A", "role": None, "comment": None}],
                "fields": None,
            }
            self.assertEqual(
                run_cli(["set", "ENTITY-A", "--json", json.dumps(doc)], cwd=tmp).code, 0
            )
            got = run_cli(["get", "ENTITY-A"], cwd=tmp).envelope["result"]["bindings"][0]
            self.assertEqual(
                got,
                {
                    "id": "ENTITY-A",
                    "kind": "ENTITY",
                    "comment": None,
                    "locators": [
                        {"path": "src/a.py", "symbol": "A", "role": None, "comment": None}
                    ],
                    "compare_via": None,
                    "fields": None,
                    "wire": None,
                    "asserted_by": None,
                },
            )

    def test_stdin_document(self) -> None:
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            with mock.patch("sys.stdin", io.StringIO('{"locators": []}')):
                run = run_cli(["set", "CAP-STDIN", "--json", "-"], cwd=tmp)
            self.assertEqual(run.code, 0, run.stdout)
            self.assertEqual(run.envelope["result"]["binding"]["locators"], [])

    def test_warning_only_input_is_written_and_reported_post(self) -> None:
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            doc = {"locators": [{"path": "src/p.py", "role": "producer"}]}
            run = run_cli(["set", "API-P", "--json", json.dumps(doc)], cwd=tmp)
            self.assertEqual(run.code, 0)
            self.assertEqual(_codes(run.envelope, "post"), ["INV-ROLE-REQUIRES-WIRE"])
            self.assertEqual(run_cli(["get", "API-P"], cwd=tmp).code, 0)

    def test_shape_breaking_input_writes_nothing(self) -> None:
        """Architecture example 3: `lines: 12` fails INV-CLOSED-KEYS and INV-NO-LINE-NUMBERS."""
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = read_bytes(target)
            doc = {"locators": [{"path": "src/x.py", "lines": 12}]}
            run = run_cli(["set", "ENTITY-X", "--json", json.dumps(doc)], cwd=tmp)
            env = run.envelope
            self.assertEqual((run.code, env["error"]["code"]), (1, "ERR-INPUT-INVALID"))
            self.assertEqual(
                sorted(f["code"] for f in env["error"]["details"]["findings"]),
                ["INV-CLOSED-KEYS", "INV-NO-LINE-NUMBERS"],
            )
            self.assertEqual(read_bytes(target), before)
            unknown = run_cli(
                ["set", "ENTITY-X", "--json", '{"locators": [], "bogus": 1}'], cwd=tmp
            )
            self.assertEqual(unknown.envelope["error"]["code"], "ERR-INPUT-INVALID")
            self.assertEqual(read_bytes(target), before)

    def test_comment_value_rules_apply_to_json_input(self) -> None:
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            for comment in ("", "abc ", "\nabc", "a\x01b"):
                doc = {"locators": [], "comment": comment}
                run = run_cli(["set", "ENTITY-C", "--json", json.dumps(doc)], cwd=tmp)
                self.assertEqual(run.envelope["error"]["code"], "ERR-INPUT-INVALID", repr(comment))
                self.assertIn(
                    "INV-COMMENT-TEXT",
                    [f["code"] for f in run.envelope["error"]["details"]["findings"]],
                )
            typed = run_cli(
                ["set", "ENTITY-C", "--json", '{"locators": [], "comment": 3}'], cwd=tmp
            )
            self.assertEqual(typed.envelope["error"]["code"], "ERR-INPUT-INVALID")

    def test_usage_conditions(self) -> None:
        """DICT: ERR-USAGE (--json conditions, contradicting id/kind, numeric ID)"""
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            cases = [
                (["set", "ENTITY-X", "--json", "{not json"], "not valid JSON"),
                (["set", "ENTITY-X", "--json", "[]"], "JSON object"),
                (
                    ["set", "ENTITY-X", "--json", '{"id": "ENTITY-Y", "locators": []}'],
                    "contradicts",
                ),
                (["set", "ENTITY-X", "--json", '{"kind": "INV", "locators": []}'], "contradicts"),
                (["set", "ENTITY-1", "--json", '{"locators": []}'], "not a contract ID"),
                (["set", "ENTITY-X"], "required"),
            ]
            for argv, fragment in cases:
                run = run_cli(argv, cwd=tmp)
                env = run.envelope
                self.assertEqual(
                    (run.code, env["error"]["code"], env["command"]), (1, "ERR-USAGE", "set"), argv
                )
                self.assertIn(fragment, env["error"]["message"], argv)


class AddLocator(unittest.TestCase):
    """DICT: CLI-ADD-LOCATOR / INV-ORDER-PRESERVED"""

    def test_appends_last_with_every_flag(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = _lines(target)
            run = run_cli(
                [
                    "add-locator",
                    "ENTITY-PROJECT",
                    "--path",
                    "src/p2.py",
                    "--symbol",
                    "P2",
                    "--role",
                    "consumer",
                    "--comment",
                    "second consumer",
                ],
                cwd=tmp,
            )
            self.assertEqual(run.code, 0, run.stdout)
            locs = run.envelope["result"]["binding"]["locators"]
            self.assertEqual(
                locs[-1],
                {
                    "path": "src/p2.py",
                    "symbol": "P2",
                    "role": "consumer",
                    "comment": "second consumer",
                },
            )
            after = _lines(target)
            self.assertTrue(_is_subsequence(before, after))
            self.assertEqual(len(after) - len(before), 1)
            self.assertIn(
                "      - { path: src/p2.py, symbol: P2, role: consumer } # second consumer", after
            )

    def test_duplicate_not_found_and_input_rules(self) -> None:
        """DICT: ERR-DUPLICATE / ERR-NOT-FOUND / ERR-INPUT-INVALID (flag channel)"""
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = read_bytes(target)
            dup = run_cli(
                ["add-locator", "ENTITY-USER", "--path", "src/models/user.py", "--symbol", "User"],
                cwd=tmp,
            )
            self.assertEqual((dup.code, dup.envelope["error"]["code"]), (1, "ERR-DUPLICATE"))
            self.assertEqual(dup.envelope["error"]["details"]["id"], "ENTITY-USER")
            self.assertEqual(dup.envelope["error"]["details"]["anchor"]["type"], "locator")
            missing = run_cli(["add-locator", "ENTITY-NOPE", "--path", "a.py"], cwd=tmp)
            self.assertEqual(missing.envelope["error"]["code"], "ERR-NOT-FOUND")
            cases = [
                (["add-locator", "ROUTE-HOME", "--path", "src/x.py:41"], "INV-NO-LINE-NUMBERS"),
                (
                    ["add-locator", "ROUTE-HOME", "--path", "src/x.py", "--symbol", "a\nb"],
                    "INV-SYMBOL-NONEMPTY",
                ),
                (["add-locator", "ROUTE-HOME", "--path", "../x.py"], "INV-PATH-FORM"),
                (
                    ["add-locator", "ROUTE-HOME", "--path", "src/x.py", "--comment", "abc "],
                    "INV-COMMENT-TEXT",
                ),
                (
                    ["--check-paths", "add-locator", "ROUTE-HOME", "--path", "no/such.py"],
                    "INV-PATH-EXISTS",
                ),
            ]
            for argv, code in cases:
                run = run_cli(argv, cwd=tmp)
                self.assertEqual(run.envelope["error"]["code"], "ERR-INPUT-INVALID", argv)
                self.assertIn(
                    code, [f["code"] for f in run.envelope["error"]["details"]["findings"]]
                )
            self.assertEqual(read_bytes(target), before)
            empty = run_cli(
                ["add-locator", "ROUTE-HOME", "--path", "src/x.py", "--comment", ""], cwd=tmp
            )
            self.assertEqual(empty.envelope["error"]["code"], "ERR-USAGE")


class AddField(unittest.TestCase):
    """DICT: CLI-ADD-FIELD"""

    def test_new_appends_and_existing_replaces_keeping_comment(self) -> None:
        with TempDir() as tmp:
            copy_fixture("carriers.yaml", tmp)
            run = run_cli(
                ["add-field", "ENTITY-A", "age", "--path", "src/a.py", "--symbol", "A.age"], cwd=tmp
            )
            self.assertEqual(run.code, 0, run.stdout)
            fields = run.envelope["result"]["binding"]["fields"]
            self.assertEqual(list(fields), ["name", "age"])
            self.assertEqual(fields["age"]["comment"], None)
            replaced = run_cli(["add-field", "ENTITY-A", "name", "--path", "src/a2.py"], cwd=tmp)
            fields = replaced.envelope["result"]["binding"]["fields"]
            self.assertEqual(list(fields), ["name", "age"])
            self.assertEqual(
                fields["name"], {"path": "src/a2.py", "symbol": None, "comment": "trailing field"}
            )
            recommented = run_cli(
                ["add-field", "ENTITY-A", "name", "--path", "src/a3.py", "--comment", "new text"],
                cwd=tmp,
            )
            self.assertEqual(
                recommented.envelope["result"]["binding"]["fields"]["name"]["comment"], "new text"
            )
            fresh = run_cli(["add-field", "ENTITY-B", "f", "--path", "src/b.py"], cwd=tmp)
            self.assertEqual(list(fresh.envelope["result"]["binding"]["fields"]), ["f"])
            missing = run_cli(["add-field", "ENTITY-NOPE", "f", "--path", "src/b.py"], cwd=tmp)
            self.assertEqual(missing.envelope["error"]["code"], "ERR-NOT-FOUND")
            bad_name = run_cli(["add-field", "ENTITY-B", "a\x01", "--path", "src/b.py"], cwd=tmp)
            self.assertEqual(bad_name.envelope["error"]["code"], "ERR-INPUT-INVALID")


class AddAssertion(unittest.TestCase):
    """DICT: CLI-ADD-ASSERTION"""

    def test_bound_and_owed_append_last(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = _lines(target)
            bound = run_cli(
                [
                    "add-assertion",
                    "ROUTE-HOME",
                    "--path",
                    "tests/test_home.py",
                    "--symbol",
                    "test_home",
                    "--run",
                    "python3 -m unittest tests.test_home",
                    "--arm",
                    "a",
                    "--comment",
                    "first",
                ],
                cwd=tmp,
            )
            self.assertEqual(bound.code, 0, bound.stdout)
            owed = run_cli(["add-assertion", "ROUTE-HOME", "--owed", "slice-4"], cwd=tmp)
            self.assertEqual(owed.code, 0)
            asserted = owed.envelope["result"]["binding"]["asserted_by"]
            self.assertEqual([a["comment"] for a in asserted], ["first", None])
            self.assertEqual(asserted[1]["owed"], "slice-4")
            after = _lines(target)
            self.assertTrue(_is_subsequence(before, after))
            self.assertEqual(len(after) - len(before), 3)

    def test_duplicate_identity_and_partial_shapes(self) -> None:
        """DICT: ERR-DUPLICATE / ERR-USAGE (partial assertion shape)"""
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            dup = run_cli(["add-assertion", "ENTITY-USER", "--owed", "slice-9"], cwd=tmp)
            self.assertEqual(dup.envelope["error"]["code"], "ERR-DUPLICATE")
            armed = run_cli(
                ["add-assertion", "ENTITY-USER", "--owed", "slice-9", "--arm", "d"], cwd=tmp
            )
            self.assertEqual(armed.code, 0)
            for argv in (
                ["add-assertion", "ROUTE-HOME", "--path", "t.py"],
                ["add-assertion", "ROUTE-HOME", "--run", "r"],
                ["add-assertion", "ROUTE-HOME", "--arm", "a"],
                [
                    "add-assertion",
                    "ROUTE-HOME",
                    "--path",
                    "t.py",
                    "--symbol",
                    "t",
                    "--run",
                    "r",
                    "--owed",
                    "x",
                ],
                ["add-assertion", "ROUTE-HOME"],
            ):
                run = run_cli(argv, cwd=tmp)
                self.assertEqual(
                    (run.envelope["error"]["code"], run.envelope["command"]),
                    ("ERR-USAGE", "add-assertion"),
                    argv,
                )


class Remove(unittest.TestCase):
    """DICT: CLI-REMOVE / ERR-NOT-FOUND (entry arm)"""

    def test_whole_binding_goes_with_its_comments(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            run = run_cli(["remove", "ENTITY-USER"], cwd=tmp)
            self.assertEqual(run.code, 0, run.stdout)
            self.assertEqual(run.envelope["result"], {"binding": None, "removed": "ENTITY-USER"})
            text = read_bytes(target).decode("utf-8")
            self.assertNotIn("ENTITY-USER", text)
            self.assertNotIn("comment block above a binding", text)
            ids = [r["id"] for r in run_cli(["list"], cwd=tmp).envelope["result"]["bindings"]]
            self.assertEqual(ids, ["ENTITY-PROJECT", "ROUTE-HOME", "SCREEN-STUB"])

    def test_entries(self) -> None:
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            stub = run_cli(
                ["remove", "ROUTE-HOME", "--locator", "--path", "web/src/app.routes.ts"], cwd=tmp
            )
            self.assertEqual(stub.envelope["result"]["binding"]["locators"], [])
            f1 = run_cli(["remove", "ENTITY-USER", "--field", "email"], cwd=tmp)
            self.assertEqual(list(f1.envelope["result"]["binding"]["fields"]), ["config"])
            f2 = run_cli(["remove", "ENTITY-USER", "--field", "config"], cwd=tmp)
            self.assertIsNone(f2.envelope["result"]["binding"]["fields"])
            a1 = run_cli(
                ["remove", "ENTITY-USER", "--assertion", "--owed", "slice-9", "--arm", "c"], cwd=tmp
            )
            self.assertEqual(len(a1.envelope["result"]["binding"]["asserted_by"]), 3)
            a2 = run_cli(
                [
                    "remove",
                    "ENTITY-USER",
                    "--assertion",
                    "--path",
                    "tests/test_user.py",
                    "--symbol",
                    "test_email_case",
                    "--arm",
                    "b",
                ],
                cwd=tmp,
            )
            self.assertEqual(len(a2.envelope["result"]["binding"]["asserted_by"]), 2)
            run_cli(["remove", "ENTITY-USER", "--assertion", "--owed", "slice-9"], cwd=tmp)
            last = run_cli(
                [
                    "remove",
                    "ENTITY-USER",
                    "--assertion",
                    "--path",
                    "tests/test_user.py",
                    "--symbol",
                    "test_email_unique",
                ],
                cwd=tmp,
            )
            self.assertIsNone(last.envelope["result"]["binding"]["asserted_by"])
            self.assertEqual(run_cli(["validate"], cwd=tmp).code, 0)

    def test_not_found_and_selector_usage(self) -> None:
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            for argv in (
                ["remove", "ENTITY-NOPE"],
                ["remove", "ENTITY-USER", "--locator", "--path", "nope.py"],
                ["remove", "ENTITY-USER", "--field", "nope"],
                ["remove", "ENTITY-USER", "--assertion", "--owed", "nope"],
                ["remove", "ENTITY-USER", "--assertion", "--path", "t.py", "--symbol", "t"],
            ):
                run = run_cli(argv, cwd=tmp)
                self.assertEqual(
                    (run.code, run.envelope["error"]["code"]), (1, "ERR-NOT-FOUND"), argv
                )
            for argv in (
                ["remove", "ENTITY-USER", "--locator", "--field", "email", "--path", "x"],
                ["remove", "ENTITY-USER", "--locator"],
                ["remove", "ENTITY-USER", "--path", "x"],
                ["remove", "ENTITY-USER", "--field", "email", "--arm", "a"],
                ["remove", "ENTITY-USER", "--assertion", "--path", "t.py"],
            ):
                run = run_cli(argv, cwd=tmp)
                self.assertEqual(
                    (run.envelope["error"]["code"], run.envelope["command"]),
                    ("ERR-USAGE", "remove"),
                    argv,
                )


class Coverage(unittest.TestCase):
    """DICT: CLI-COVERAGE-GET / CLI-COVERAGE-FULLY-BOUND / CLI-COVERAGE-CURATED / OUT-COVERAGE"""

    def test_get(self) -> None:
        with TempDir() as tmp:
            run_cli(["init"], cwd=tmp)
            empty = run_cli(["coverage", "get"], cwd=tmp)
            self.assertEqual((empty.code, empty.envelope["command"]), (0, "coverage get"))
            self.assertEqual(
                empty.envelope["result"],
                {"coverage": {"comment": None, "fully_bound": [], "curated": {}}},
            )
            copy_fixture(CANON, tmp)
            cov = run_cli(["coverage", "get"], cwd=tmp).envelope["result"]["coverage"]
            self.assertEqual(list(cov), ["comment", "fully_bound", "curated"])
            self.assertEqual(cov["fully_bound"], ["ENTITY", "INV", "ROUTE"])
            self.assertEqual(
                cov["curated"]["API"]["comment"],
                "Optional comment above a curated entry (anchor: curated API).",
            )

    def test_fully_bound(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = _lines(target)
            add = run_cli(["coverage", "fully-bound", "add", "SCREEN"], cwd=tmp)
            self.assertEqual(add.code, 0, add.stdout)
            self.assertEqual(
                add.envelope["result"]["coverage"]["fully_bound"],
                ["ENTITY", "INV", "ROUTE", "SCREEN"],
            )
            self.assertEqual(len(_lines(target)), len(before))
            dup = run_cli(["coverage", "fully-bound", "add", "SCREEN"], cwd=tmp)
            self.assertEqual(dup.envelope["error"]["code"], "ERR-DUPLICATE")
            curated = run_cli(["coverage", "fully-bound", "add", "API"], cwd=tmp)
            self.assertEqual(curated.envelope["error"]["code"], "ERR-INPUT-INVALID")
            self.assertEqual(
                [f["code"] for f in curated.envelope["error"]["details"]["findings"]],
                ["INV-COVERAGE-WELLFORMED"],
            )
            gone = run_cli(["coverage", "fully-bound", "remove", "ZZZ"], cwd=tmp)
            self.assertEqual(gone.envelope["error"]["code"], "ERR-NOT-FOUND")
            for kind in ("ENTITY", "INV", "ROUTE", "SCREEN"):
                self.assertEqual(
                    run_cli(["coverage", "fully-bound", "remove", kind], cwd=tmp).code, 0
                )
            cov = run_cli(["coverage", "get"], cwd=tmp).envelope["result"]["coverage"]
            self.assertEqual(cov["fully_bound"], [])
            self.assertNotIn("fully_bound", read_bytes(target).decode("utf-8"))
            bad = run_cli(["coverage", "fully-bound", "add", "bad"], cwd=tmp)
            self.assertEqual(
                (bad.envelope["error"]["code"], bad.envelope["command"]),
                ("ERR-USAGE", "coverage fully-bound"),
            )

    def test_curated_and_empty_block_removal(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            new = run_cli(
                [
                    "coverage",
                    "curated",
                    "set",
                    "CAP",
                    "--reason",
                    "headline only",
                    "--comment",
                    "why",
                ],
                cwd=tmp,
            )
            self.assertEqual(new.code, 0, new.stdout)
            self.assertEqual(
                new.envelope["result"]["coverage"]["curated"]["CAP"],
                {"reason": "headline only", "comment": "why"},
            )
            kept = run_cli(["coverage", "curated", "set", "CAP", "--reason", "changed"], cwd=tmp)
            self.assertEqual(
                kept.envelope["result"]["coverage"]["curated"]["CAP"],
                {"reason": "changed", "comment": "why"},
            )
            self.assertEqual(list(kept.envelope["result"]["coverage"]["curated"]), ["API", "CAP"])
            fb = run_cli(["coverage", "curated", "set", "ENTITY", "--reason", "x"], cwd=tmp)
            self.assertEqual(fb.envelope["error"]["code"], "ERR-INPUT-INVALID")
            bad_comment = run_cli(
                ["coverage", "curated", "set", "SEC", "--reason", "x", "--comment", "y "], cwd=tmp
            )
            self.assertEqual(bad_comment.envelope["error"]["code"], "ERR-INPUT-INVALID")
            missing = run_cli(["coverage", "curated", "unset", "SEC"], cwd=tmp)
            self.assertEqual(missing.envelope["error"]["code"], "ERR-NOT-FOUND")
            self.assertEqual(run_cli(["coverage", "curated", "unset", "API"], cwd=tmp).code, 0)
            self.assertEqual(run_cli(["coverage", "curated", "unset", "CAP"], cwd=tmp).code, 0)
            self.assertNotIn("curated", read_bytes(target).decode("utf-8"))
            for kind in ("ENTITY", "INV", "ROUTE"):
                run_cli(["coverage", "fully-bound", "remove", kind], cwd=tmp)
            text = read_bytes(target).decode("utf-8")
            self.assertNotIn("coverage", text)
            self.assertNotIn("Optional comment block above coverage", text)
            again = run_cli(["coverage", "curated", "set", "API", "--reason", "back"], cwd=tmp)
            self.assertEqual(
                again.envelope["result"]["coverage"],
                {
                    "comment": None,
                    "fully_bound": [],
                    "curated": {"API": {"reason": "back", "comment": None}},
                },
            )

    def test_group_without_subcommand_is_usage(self) -> None:
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            for argv, command in (
                (["coverage"], "coverage"),
                (["coverage", "fully-bound"], "coverage fully-bound"),
                (["coverage", "curated"], "coverage curated"),
                (["coverage", "curated", "set", "API"], "coverage curated"),
                (["coverage", "curated", "unset", "API", "--reason", "r"], "coverage curated"),
                (["coverage", "fully-bound", "add"], "coverage fully-bound"),
                (["coverage", "fully-bound", "drop", "API"], "coverage fully-bound"),
                (["coverage", "bogus"], "coverage"),
            ):
                run = run_cli(argv, cwd=tmp)
                self.assertEqual(
                    (run.code, run.envelope["error"]["code"], run.envelope["command"]),
                    (1, "ERR-USAGE", command),
                    argv,
                )
                self.assertTrue(
                    run.envelope["error"]["details"]["usage"].startswith(f"usage: dbind {command}"),
                    argv,
                )


class ValidateAroundWrite(unittest.TestCase):
    """DICT: PATTERN-VALIDATE-AROUND-WRITE / ERR-FILE-INVALID"""

    def test_error_level_file_refuses_every_writer(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture("inv-no-line-numbers.yaml", tmp)
            before = read_bytes(target)
            for argv in (
                ["add-locator", "ENTITY-A", "--path", "src/y.py"],
                ["set", "ENTITY-Z", "--json", '{"locators": []}'],
                ["remove", "ENTITY-A"],
                ["coverage", "fully-bound", "add", "API"],
            ):
                run = run_cli(argv, cwd=tmp)
                env = run.envelope
                self.assertEqual(
                    (run.code, env["ok"], env["error"]["code"]),
                    (1, False, "ERR-FILE-INVALID"),
                    argv,
                )
                self.assertTrue(env["error"]["details"]["findings"])
                self.assertTrue(
                    all(f["severity"] == "error" for f in env["error"]["details"]["findings"])
                )
                self.assertIn("INV-NO-LINE-NUMBERS", _codes(env, "pre"))
                self.assertEqual(read_bytes(target), before)

    def test_pre_warning_is_tolerated_and_reported(self) -> None:
        with TempDir() as tmp:
            copy_fixture("inv-role-requires-wire.yaml", tmp)
            ids = [r["id"] for r in run_cli(["list"], cwd=tmp).envelope["result"]["bindings"]]
            run = run_cli(["add-field", ids[0], "f", "--path", "src/f.py"], cwd=tmp)
            env = run.envelope
            self.assertEqual((run.code, env["ok"]), (0, True))
            self.assertIn("INV-ROLE-REQUIRES-WIRE", _codes(env, "pre"))
            self.assertIn("INV-ROLE-REQUIRES-WIRE", _codes(env, "post"))
            self.assertEqual(
                run_cli(["get", ids[0]], cwd=tmp).envelope["result"]["bindings"][0]["fields"]["f"][
                    "path"
                ],
                "src/f.py",
            )

    def test_schema_version_is_refused_before_anything(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture("inv-schema-version.yaml", tmp)
            before = read_bytes(target)
            run = run_cli(["set", "ENTITY-A", "--json", '{"locators": []}'], cwd=tmp)
            self.assertEqual(run.envelope["error"]["code"], "ERR-SCHEMA-VERSION")
            self.assertEqual(read_bytes(target), before)


class OrderPreserved(unittest.TestCase):
    """DICT: INV-ORDER-PRESERVED — a write on a non-canonical file repairs the layout everywhere
    and keeps every order."""

    def test_noncanonical_file_is_repaired_with_order_kept(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture("noncanonical.yaml", tmp)
            run = run_cli(["add-locator", "ENTITY-A", "--path", "src/a2.py"], cwd=tmp)
            self.assertEqual(run.code, 0, run.stdout)
            m, findings = loader.load(target)
            self.assertEqual(findings, [])
            self.assertEqual(read_bytes(target), emitter.emit(m))
            self.assertEqual(list(m.bindings), ["ROUTE-B", "ENTITY-A"])
            self.assertEqual(
                [loc.path for loc in m.bindings["ENTITY-A"].locators], ["src/a.py", "src/a2.py"]
            )
            assert m.coverage is not None
            self.assertEqual(m.coverage.fully_bound, ["ROUTE", "ENTITY"])

    def test_every_write_keeps_the_untouched_lines_in_order(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            steps = [
                ["add-locator", "SCREEN-STUB", "--path", "web/s.ts"],
                ["add-field", "ENTITY-PROJECT", "name", "--path", "src/models/project.py"],
                ["add-assertion", "ENTITY-PROJECT", "--owed", "slice-3"],
                ["coverage", "fully-bound", "add", "SCREEN"],
                ["coverage", "curated", "set", "CAP", "--reason", "r"],
                ["set", "CAP-NEW", "--json", '{"locators": []}'],
            ]
            for argv in steps:
                before = _lines(target)
                self.assertEqual(run_cli(argv, cwd=tmp).code, 0, argv)
                after = _lines(target)
                kept = [
                    ln
                    for ln in before
                    if ln not in ("  fully_bound: [ENTITY, INV, ROUTE]", "    locators: []")
                ]
                self.assertTrue(_is_subsequence(kept, after), argv)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
