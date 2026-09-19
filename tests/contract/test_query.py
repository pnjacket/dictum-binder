"""Contract tier for the slice-2 elements: CLI-GET, CLI-LIST, their output documents,
ERR-SCHEMA-VERSION (first reader) and the ERR-NOT-FOUND / ERR-USAGE conditions they add."""

from __future__ import annotations

import json
import os
import unittest

from tests._helpers import TempDir, copy_fixture, many_bindings, run_cli

BINDING_KEYS = [
    "id",
    "kind",
    "comment",
    "locators",
    "compare_via",
    "fields",
    "wire",
    "asserted_by",
]
SUMMARY_KEYS = ["id", "kind", "stub", "locators", "fields", "assertions", "has_comment"]


def _write_many(tmp: str, count: int = 50) -> str:
    path = os.path.join(tmp, "bindings.yaml")
    with open(path, "wb") as handle:
        handle.write(many_bindings(count))
    return path


class Get(unittest.TestCase):
    """DICT: CLI-GET / OUT-BINDING / OUT-LOCATOR / OUT-FIELD-LOCATOR / OUT-ASSERTION"""

    def test_full_projection_with_comments(self) -> None:
        with TempDir() as tmp:
            copy_fixture("carriers.yaml", tmp)
            run = run_cli(["get", "ENTITY-A"], cwd=tmp)
            self.assertEqual(run.code, 0, run.stdout)
            env = run.envelope
            self.assertEqual((env["ok"], env["command"], env["error"]), (True, "get", None))
            (b,) = env["result"]["bindings"]
            self.assertEqual(list(b), BINDING_KEYS)
            self.assertEqual((b["id"], b["kind"]), ("ENTITY-A", "ENTITY"))
            self.assertEqual(b["comment"], "binding block\nsecond line")
            self.assertEqual(
                b["locators"],
                [
                    {
                        "path": "src/a.py",
                        "symbol": "A",
                        "role": None,
                        "comment": "trailing locator",
                    },
                    {
                        "path": "src/b.py",
                        "symbol": None,
                        "role": None,
                        "comment": "block above locator\ntwo lines",
                    },
                ],
            )
            self.assertEqual(
                b["fields"],
                {"name": {"path": "src/a.py", "symbol": "A.name", "comment": "trailing field"}},
            )
            self.assertEqual((b["compare_via"], b["wire"]), (None, None))
            self.assertEqual(
                b["asserted_by"],
                [
                    {
                        "path": None,
                        "symbol": None,
                        "run": None,
                        "arm": None,
                        "owed": "slice-2",
                        "comment": "trailing assertion",
                    }
                ],
            )

    def test_bound_assertion_and_wire_projection(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            rows = run_cli(["list", "--full"], cwd=tmp).envelope["result"]["bindings"]
            bound = [a for b in rows for a in (b["asserted_by"] or []) if a["owed"] is None]
            self.assertTrue(bound)
            self.assertEqual(list(bound[0]), ["path", "symbol", "run", "arm", "owed", "comment"])
            self.assertTrue(all(bound[0][k] is not None for k in ("path", "symbol", "run")))
            wires = [b["wire"] for b in rows if b["wire"] is not None]
            self.assertTrue(wires)
            self.assertEqual(list(wires[0]), ["casing", "enums", "dates"])

    def test_stub_and_absent_optionals_are_null(self) -> None:
        with TempDir() as tmp:
            copy_fixture("carriers.yaml", tmp)
            (b,) = run_cli(["get", "ENTITY-B"], cwd=tmp).envelope["result"]["bindings"]
            self.assertEqual(
                b,
                {
                    "id": "ENTITY-B",
                    "kind": "ENTITY",
                    "comment": "trailing on the anchor line, read as a block",
                    "locators": [],
                    "compare_via": None,
                    "fields": None,
                    "wire": None,
                    "asserted_by": None,
                },
            )

    def test_argument_order_and_repeats(self) -> None:
        with TempDir() as tmp:
            _write_many(tmp)
            ids = ["INV-GEN-N001", "ENTITY-GEN-N000", "INV-GEN-N001"]
            run = run_cli(["get", *ids], cwd=tmp)
            self.assertEqual([b["id"] for b in run.envelope["result"]["bindings"]], ids)

    def test_bounded_output(self) -> None:
        """DICT: SUCCESS-BOUNDED-OUTPUT"""
        with TempDir() as tmp:
            _write_many(tmp)
            run = run_cli(["get", "API-GEN-N002", "CAP-GEN-N004"], cwd=tmp)
            self.assertEqual(run.code, 0)
            self.assertEqual(len(run.envelope["result"]["bindings"]), 2)
            for n in range(50):
                token = f"GEN-N{n:03d}"
                self.assertEqual(token in run.stdout, n in (2, 4), token)

    def test_unknown_id_is_not_found_and_returns_nothing(self) -> None:
        """DICT: ERR-NOT-FOUND (get arm)"""
        with TempDir() as tmp:
            _write_many(tmp, 3)
            run = run_cli(["get", "ENTITY-GEN-N000", "ENTITY-NOPE", "INV-GEN-N001"], cwd=tmp)
            env = run.envelope
            self.assertEqual((run.code, env["ok"], env["result"]), (1, False, None))
            self.assertEqual(env["error"]["code"], "ERR-NOT-FOUND")
            anchor = env["error"]["details"]["anchor"]
            self.assertEqual(env["error"]["details"]["id"], "ENTITY-NOPE")
            self.assertEqual((anchor["type"], anchor["id"]), ("binding", "ENTITY-NOPE"))
            self.assertEqual(
                list(anchor), ["type", "id", "path", "symbol", "arm", "owed", "field", "kind"]
            )
            self.assertNotIn("GEN-N000", run.stdout)

    def test_error_level_findings_exit_1_with_the_result(self) -> None:
        with TempDir() as tmp:
            copy_fixture("inv-path-form.yaml", tmp)
            ids = list(json.loads(run_cli(["list"], cwd=tmp).stdout)["result"]["bindings"])
            run = run_cli(["get", ids[0]["id"]], cwd=tmp)
            env = run.envelope
            self.assertEqual((run.code, env["ok"]), (1, True))
            self.assertEqual(len(env["result"]["bindings"]), 1)
            self.assertTrue(any(f["severity"] == "error" for f in env["findings"]["pre"]))

    def test_bad_id_on_the_command_line_is_usage(self) -> None:
        """DICT: ERR-USAGE (ID failing its grammar)"""
        with TempDir() as tmp:
            _write_many(tmp, 1)
            for bad in ("entity-a", "ENTITY-1", "ENTITY", "ENTITY-A:12"):
                run = run_cli(["get", bad], cwd=tmp)
                env = run.envelope
                self.assertEqual(
                    (run.code, env["error"]["code"], env["command"]), (1, "ERR-USAGE", "get")
                )
                self.assertIn("usage: dbind get", env["error"]["details"]["usage"])


class List(unittest.TestCase):
    """DICT: CLI-LIST / OUT-BINDING-SUMMARY"""

    def test_summaries_in_file_order(self) -> None:
        with TempDir() as tmp:
            copy_fixture("carriers.yaml", tmp)
            run = run_cli(["list"], cwd=tmp)
            self.assertEqual(run.code, 0, run.stdout)
            rows = run.envelope["result"]["bindings"]
            self.assertEqual([r["id"] for r in rows], ["ENTITY-A", "ENTITY-B"])
            self.assertEqual(list(rows[0]), SUMMARY_KEYS)
            self.assertEqual(
                rows[0],
                {
                    "id": "ENTITY-A",
                    "kind": "ENTITY",
                    "stub": False,
                    "locators": 2,
                    "fields": 1,
                    "assertions": 1,
                    "has_comment": True,
                },
            )
            self.assertEqual((rows[1]["stub"], rows[1]["has_comment"]), (True, True))

    def test_has_comment_sees_every_anchor(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "bindings.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\n\nbindings:\n\n"
                    "  ENTITY-A:\n    locators:\n      - { path: a.py } # loc\n\n"
                    "  ENTITY-B:\n    locators: []\n    fields:\n      f: { path: a.py } # fld\n\n"
                    "  ENTITY-C:\n    locators: []\n    asserted_by:\n      - { owed: s1 } # as\n\n"
                    "  ENTITY-D:\n    locators: []\n"
                )
            rows = run_cli(["list"], cwd=tmp).envelope["result"]["bindings"]
            self.assertEqual([r["has_comment"] for r in rows], [True, True, True, False])

    def test_kind_filter_union_and_empty_result(self) -> None:
        with TempDir() as tmp:
            _write_many(tmp)
            inv = run_cli(["list", "--kind", "INV"], cwd=tmp)
            rows = inv.envelope["result"]["bindings"]
            self.assertEqual(len(rows), 5)
            self.assertTrue(all(r["kind"] == "INV" for r in rows))
            for n in range(50):
                self.assertEqual(f"GEN-N{n:03d}" in inv.stdout, n % 10 == 1)
            union = run_cli(["list", "--kind", "INV", "--kind", "API"], cwd=tmp)
            self.assertEqual(len(union.envelope["result"]["bindings"]), 10)
            empty = run_cli(["list", "--kind", "ZZZ"], cwd=tmp)
            self.assertEqual((empty.code, empty.envelope["result"]), (0, {"bindings": []}))
            lower = run_cli(["list", "--kind", "inv"], cwd=tmp)
            self.assertEqual(lower.envelope["error"]["code"], "ERR-USAGE")
            self.assertEqual(lower.envelope["command"], "list")

    def test_full(self) -> None:
        with TempDir() as tmp:
            _write_many(tmp, 4)
            rows = run_cli(["list", "--full", "--kind", "API"], cwd=tmp).envelope["result"]
            self.assertEqual([list(b) for b in rows["bindings"]], [BINDING_KEYS])
            self.assertEqual(rows["bindings"][0]["id"], "API-GEN-N002")

    def test_empty_map(self) -> None:
        with TempDir() as tmp:
            self.assertEqual(run_cli(["init"], cwd=tmp).code, 0)
            self.assertEqual(run_cli(["list"], cwd=tmp).envelope["result"], {"bindings": []})


class SchemaVersionGate(unittest.TestCase):
    """DICT: ERR-SCHEMA-VERSION — every reader except validate refuses before any other work."""

    def test_get_and_list_refuse_another_major(self) -> None:
        with TempDir() as tmp:
            copy_fixture("inv-schema-version.yaml", tmp)
            for argv in (["get", "ENTITY-A"], ["list"]):
                run = run_cli(argv, cwd=tmp)
                env = run.envelope
                self.assertEqual((run.code, env["ok"], env["result"]), (1, False, None), argv)
                self.assertEqual(env["error"]["code"], "ERR-SCHEMA-VERSION")
                self.assertEqual(env["error"]["details"], {"found": 2, "expected": 1})
                self.assertEqual(env["findings"], {"pre": [], "post": []})
            validate = run_cli(["validate"], cwd=tmp)
            self.assertEqual(validate.envelope["error"], None)
            self.assertEqual(validate.envelope["findings"]["pre"][0]["code"], "INV-SCHEMA-VERSION")

    def test_missing_schema_version_is_the_same_error(self) -> None:
        with TempDir() as tmp:
            with open(os.path.join(tmp, "bindings.yaml"), "w", encoding="utf-8") as handle:
                handle.write("bindings: {}\n")
            env = run_cli(["list"], cwd=tmp).envelope
            self.assertEqual(env["error"]["code"], "ERR-SCHEMA-VERSION")
            self.assertEqual(env["error"]["details"], {"found": None, "expected": 1})


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
