"""Unit tier: input-document conversion (model.from_input) and validate_input edges."""

from __future__ import annotations

import unittest

from lspd import model, validator


def _codes(findings: list[model.Finding]) -> list[str]:
    return sorted(f.code for f in findings)


class FromInput(unittest.TestCase):
    def test_non_object_input(self) -> None:
        for node in ("binding", "locator", "field_locator", "assertion", "curated"):
            obj, findings = model.from_input([], node, binding_id="ENTITY-A", name="f", kind="API")
            self.assertIsNone(obj, node)
            self.assertEqual(_codes(findings), ["INV-CLOSED-KEYS"], node)

    def test_comment_must_be_a_string(self) -> None:
        obj, findings = model.from_input(
            {"path": "a.py", "comment": 1}, "locator", binding_id="X-A"
        )
        self.assertIsNotNone(obj)
        self.assertEqual(_codes(findings), ["INV-CLOSED-KEYS"])
        b, findings = model.from_input(
            {
                "locators": [{"path": "a.py", "comment": []}],
                "fields": {"f": {"path": "a.py", "comment": {}}},
            },
            "binding",
            binding_id="ENTITY-A",
        )
        self.assertEqual(_codes(findings), ["INV-CLOSED-KEYS", "INV-CLOSED-KEYS"])

    def test_nested_comments_and_nulls(self) -> None:
        doc = {
            "id": "ENTITY-A",
            "kind": "ENTITY",
            "comment": "top",
            "locators": [{"path": "a.py", "symbol": None, "comment": "l0"}, {"path": "b.py"}],
            "fields": {"f": {"path": "a.py", "comment": "f0"}},
            "wire": {"casing": "snake", "enums": None, "dates": None},
            "asserted_by": [{"owed": "s1", "comment": "a0"}, {"owed": "s2", "arm": "x"}],
            "compare_via": None,
        }
        b, findings = model.from_input(doc, "binding", binding_id="ENTITY-A")
        self.assertEqual(findings, [])
        assert b is not None and b.fields is not None and b.wire is not None
        assert b.asserted_by is not None
        self.assertEqual(b.comment, "top")
        self.assertEqual([loc.comment for loc in b.locators], ["l0", None])
        self.assertEqual(b.fields["f"].comment, "f0")
        self.assertEqual((b.wire.casing, b.wire.enums), ("snake", None))
        self.assertEqual([a.comment for a in b.asserted_by], ["a0", None])
        self.assertIsNone(b.compare_via)

    def test_dropped_items_do_not_misalign_comments(self) -> None:
        doc = {"locators": [{"path": 1, "comment": "bad"}, {"path": "b.py", "comment": "good"}]}
        b, findings = model.from_input(doc, "binding", binding_id="ENTITY-A")
        assert b is not None
        self.assertTrue(findings)
        self.assertEqual([loc.comment for loc in b.locators], [None])

    def test_non_object_items_and_unrepresentable_bindings(self) -> None:
        b, findings = model.from_input(
            {"locators": ["x", {"path": "b.py"}]}, "binding", binding_id="ENTITY-A"
        )
        assert b is not None
        self.assertEqual(_codes(findings), ["INV-CLOSED-KEYS"])
        self.assertEqual([loc.path for loc in b.locators], ["b.py"])
        b, findings = model.from_input({"locators": "nope"}, "binding", binding_id="ENTITY-A")
        self.assertIsNone(b)
        self.assertEqual(_codes(findings), ["INV-CLOSED-KEYS"])

    def test_curated_entry(self) -> None:
        entry, findings = model.from_input({"reason": "r", "comment": "c"}, "curated", kind="API")
        assert entry is not None
        self.assertEqual((entry.reason, entry.comment, findings), ("r", "c", []))
        entry, findings = model.from_input({"reason": 3}, "curated", kind="API")
        self.assertEqual((entry, _codes(findings)), (None, ["INV-CLOSED-KEYS"]))
        entry, findings = model.from_input({"reason": "r", "extra": 1}, "curated", kind="API")
        self.assertEqual(_codes(findings), ["INV-CLOSED-KEYS"])


class ValidateInput(unittest.TestCase):
    def test_shape_failure_returns_shape_findings_only(self) -> None:
        findings = validator.validate_input("nope", "locator", binding_id="ENTITY-A")
        self.assertEqual(_codes(findings), ["INV-CLOSED-KEYS"])

    def test_comment_trailing_whitespace_is_an_error_on_input(self) -> None:
        findings = validator.validate_input(
            {"path": "a.py", "comment": "x "}, "locator", binding_id="ENTITY-A"
        )
        self.assertEqual([(f.code, f.severity) for f in findings], [("INV-COMMENT-TEXT", "error")])
        findings = validator.validate_input(
            {"path": "a.py", "comment": "x\t"}, "locator", binding_id="ENTITY-A"
        )
        self.assertEqual(len(findings), 1)
        self.assertIn("control", findings[0].message)

    def test_every_node(self) -> None:
        self.assertEqual(
            validator.validate_input({"locators": []}, "binding", binding_id="ENTITY-A"), []
        )
        self.assertEqual(
            validator.validate_input(
                {"path": "a.py"}, "field_locator", binding_id="ENTITY-A", name="f"
            ),
            [],
        )
        self.assertEqual(
            _codes(
                validator.validate_input(
                    {"path": "a.py"}, "field_locator", binding_id="ENTITY-A", name=""
                )
            ),
            ["INV-FIELD-NAME"],
        )
        self.assertEqual(
            _codes(validator.validate_input({"path": "t.py"}, "assertion", binding_id="ENTITY-A")),
            ["INV-ASSERTION-SHAPE"],
        )
        self.assertEqual(validator.validate_input({"reason": "r"}, "curated", kind="API"), [])
        self.assertEqual(
            _codes(validator.validate_input({"reason": ""}, "curated", kind="API")),
            ["INV-COVERAGE-WELLFORMED"],
        )
        self.assertEqual(
            _codes(validator.validate_input({"reason": "a\x01"}, "curated", kind="API")),
            ["INV-SYMBOL-NONEMPTY"],
        )

    def test_path_check_on_input(self) -> None:
        findings = validator.validate_input(
            {"path": "no/such.py"}, "locator", binding_id="ENTITY-A", check_paths=True, root="."
        )
        self.assertEqual(_codes(findings), ["INV-PATH-EXISTS"])


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
