"""Contract tier for SUCCESS-COMPLETE-OPS: one passing test per row of Product's table of the
operations the standard performs on the map, each through the command the row names."""

from __future__ import annotations

import json
import unittest

from lspd import loader
from tests._helpers import TempDir, copy_fixture, read_bytes, run_cli


def _ok(argv: list[str], cwd: str) -> dict:
    run = run_cli(argv, cwd=cwd)
    assert run.code == 0, run.stdout
    return run.envelope


class CompleteOps(unittest.TestCase):
    """DICT: SUCCESS-COMPLETE-OPS"""

    def test_row_1_mint_the_map_then_set_per_binding(self) -> None:
        with TempDir() as tmp:
            _ok(["init"], tmp)
            for contract_id in ("CAP-A", "ENTITY-B"):
                _ok(["set", contract_id, "--json", '{"locators": [{"path": "src/x.py"}]}'], tmp)
            ids = [r["id"] for r in _ok(["list"], tmp)["result"]["bindings"]]
            self.assertEqual(ids, ["CAP-A", "ENTITY-B"])

    def test_row_2_stub_a_new_contract(self) -> None:
        with TempDir() as tmp:
            _ok(["init"], tmp)
            env = _ok(["set", "SCREEN-NEW", "--json", '{"locators": []}'], tmp)
            self.assertEqual(env["result"]["binding"]["locators"], [])
            self.assertTrue(_ok(["list"], tmp)["result"]["bindings"][0]["stub"])

    def test_row_3_record_or_update_a_binding_as_a_slice_lands(self) -> None:
        with TempDir() as tmp:
            _ok(["init"], tmp)
            _ok(["set", "ENTITY-U", "--json", '{"locators": []}'], tmp)
            _ok(["add-locator", "ENTITY-U", "--path", "src/u.py", "--symbol", "U"], tmp)
            _ok(
                ["add-field", "ENTITY-U", "email", "--path", "src/u.py", "--symbol", "U.email"], tmp
            )
            env = _ok(
                [
                    "add-assertion",
                    "ENTITY-U",
                    "--path",
                    "t.py",
                    "--symbol",
                    "t_u",
                    "--run",
                    "python3 -m unittest t",
                ],
                tmp,
            )
            b = env["result"]["binding"]
            self.assertEqual(
                (len(b["locators"]), list(b["fields"]), len(b["asserted_by"])), (1, ["email"], 1)
            )

    def test_row_4_record_a_deferred_assertion_as_owed(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            env = _ok(["add-assertion", "ROUTE-HOME", "--owed", "slice-7"], tmp)
            self.assertEqual(env["result"]["binding"]["asserted_by"][-1]["owed"], "slice-7")

    def test_row_5_label_a_multi_arm_assertion(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            _ok(["add-assertion", "ROUTE-HOME", "--owed", "s", "--arm", "a"], tmp)
            env = _ok(["add-assertion", "ROUTE-HOME", "--owed", "s", "--arm", "b"], tmp)
            self.assertEqual(
                [a["arm"] for a in env["result"]["binding"]["asserted_by"]], ["a", "b"]
            )

    def test_row_6_declare_a_dual_realisation_with_its_wire_contract(self) -> None:
        with TempDir() as tmp:
            _ok(["init"], tmp)
            doc = {
                "locators": [
                    {"path": "src/m.py", "symbol": "M", "role": "producer"},
                    {"path": "web/m.ts", "symbol": "M", "role": "consumer"},
                ],
                "wire": {"casing": "camelCase", "enums": "string-names", "dates": "iso-8601-utc"},
            }
            env = _ok(["set", "ENTITY-M", "--json", json.dumps(doc)], tmp)
            self.assertEqual(env["findings"]["post"], [])
            self.assertEqual(env["result"]["binding"]["wire"]["casing"], "camelCase")

    def test_row_7_fix_or_retire_a_dangling_locator(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            _ok(
                [
                    "remove",
                    "ENTITY-USER",
                    "--locator",
                    "--path",
                    "db/schema.sql",
                    "--symbol",
                    "users",
                ],
                tmp,
            )
            env = _ok(
                [
                    "add-locator",
                    "ENTITY-USER",
                    "--path",
                    "db/schema/users.sql",
                    "--symbol",
                    "users",
                ],
                tmp,
            )
            paths = [loc["path"] for loc in env["result"]["binding"]["locators"]]
            self.assertEqual(paths, ["src/models/user.py", "db/schema/users.sql"])

    def test_row_8_remove_a_binding_on_tombstone(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            env = _ok(["remove", "SCREEN-STUB"], tmp)
            self.assertEqual(env["result"], {"binding": None, "removed": "SCREEN-STUB"})
            self.assertEqual(run_cli(["get", "SCREEN-STUB"], cwd=tmp).code, 1)

    def test_row_9_declare_coverage(self) -> None:
        with TempDir() as tmp:
            _ok(["init"], tmp)
            _ok(["coverage", "fully-bound", "add", "ENTITY"], tmp)
            env = _ok(["coverage", "curated", "set", "API", "--reason", "reads not indexed"], tmp)
            self.assertEqual(env["result"]["coverage"]["fully_bound"], ["ENTITY"])
            self.assertEqual(
                env["result"]["coverage"]["curated"]["API"]["reason"], "reads not indexed"
            )

    def test_row_10_self_validate_the_map(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            self.assertEqual(
                _ok(["validate"], tmp)["result"],
                {"errors": 0, "warnings": 0, "paths_checked": False},
            )
            copy_fixture("inv-path-form.yaml", tmp)
            self.assertEqual(run_cli(["validate"], cwd=tmp).code, 1)

    def test_row_11_read_locators_and_check_whether_an_id_is_bound(self) -> None:
        with TempDir() as tmp:
            copy_fixture("canonical.yaml", tmp)
            (b,) = _ok(["get", "ENTITY-USER"], tmp)["result"]["bindings"]
            self.assertEqual(len(b["locators"]), 2)
            rows = _ok(["list", "--kind", "SCREEN"], tmp)["result"]["bindings"]
            self.assertEqual([(r["id"], r["stub"]) for r in rows], [("SCREEN-STUB", True)])

    def test_row_12_carry_prose_alongside_entries(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture("canonical.yaml", tmp)
            _ok(["comment", "set", "binding", "ROUTE-HOME", "--text", "kept as prose"], tmp)
            self.assertEqual(
                _ok(["comment", "get", "binding", "ROUTE-HOME"], tmp)["result"]["text"],
                "kept as prose",
            )
            m, _ = loader.load(target)
            self.assertEqual(m.bindings["ROUTE-HOME"].comment, "kept as prose")
            self.assertIn(b"  # kept as prose\n  ROUTE-HOME:\n", read_bytes(target))


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
