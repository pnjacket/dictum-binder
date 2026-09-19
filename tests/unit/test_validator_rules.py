"""Unit tier: validator rule branches the fixtures do not reach, plus model and loader edges."""

from __future__ import annotations

import os
import unittest
from typing import Any

from dbind import loader, model, validator
from dbind.errors import ParseError
from dbind.model import Anchor, Coverage, CuratedEntry, Map
from tests._helpers import TempDir


def _plain(**binding: Any) -> dict[str, Any]:
    return {"schema_version": 1, "bindings": {"ENTITY-A": {"locators": [], **binding}}}


def _codes(m: Map) -> list[tuple[str, str]]:
    return [(f.code, f.message) for f in validator.finalize(validator.validate(m))]


def _has(findings: list[tuple[str, str]], code: str, fragment: str) -> bool:
    return any(c == code and fragment in msg for c, msg in findings)


class ScalarAndSymbolRules(unittest.TestCase):
    """DICT: INV-SYMBOL-NONEMPTY / INV-NO-LINE-NUMBERS (symbol arm)"""

    def test_control_character_in_symbol(self) -> None:
        m, findings = model.from_plain(_plain(locators=[{"path": "a.py", "symbol": "a\x01b"}]))
        self.assertEqual(findings, [])
        self.assertTrue(_has(_codes(m), "INV-SYMBOL-NONEMPTY", "control character"))

    def test_symbol_ending_in_a_line_number(self) -> None:
        m, _ = model.from_plain(_plain(locators=[{"path": "a.py", "symbol": "f:42"}]))
        self.assertTrue(_has(_codes(m), "INV-NO-LINE-NUMBERS", "symbol `f:42`"))


class CommentRules(unittest.TestCase):
    """DICT: INV-COMMENT-TEXT"""

    def test_edge_empty_line_and_control_character(self) -> None:
        m, _ = model.from_plain(_plain())
        m.bindings["ENTITY-A"].comment = "\nstarts empty"
        self.assertTrue(_has(_codes(m), "INV-COMMENT-TEXT", "begins or ends with an empty line"))
        m.bindings["ENTITY-A"].comment = "ends empty\n"
        self.assertTrue(_has(_codes(m), "INV-COMMENT-TEXT", "begins or ends with an empty line"))
        m.bindings["ENTITY-A"].comment = "bell\x07here"
        self.assertTrue(_has(_codes(m), "INV-COMMENT-TEXT", "control character"))


class FieldRules(unittest.TestCase):
    """DICT: INV-FIELD-NAME"""

    def test_empty_and_control_character_names(self) -> None:
        m, _ = model.from_plain(_plain(fields={"": {"path": "a.py"}, "b\x02": {"path": "a.py"}}))
        codes = _codes(m)
        self.assertTrue(_has(codes, "INV-FIELD-NAME", "field name is empty"))
        self.assertTrue(_has(codes, "INV-SYMBOL-NONEMPTY", "field name"))

    def test_field_locator_without_path_is_dropped_with_a_closed_keys_finding(self) -> None:
        m, findings = model.from_plain(_plain(fields={"f": {"symbol": "x"}}))
        self.assertEqual([f.code for f in findings], ["INV-CLOSED-KEYS"])
        self.assertEqual(m.bindings["ENTITY-A"].fields, {})


class AssertionRules(unittest.TestCase):
    """DICT: INV-ASSERTION-SHAPE"""

    def test_bound_assertion_missing_keys(self) -> None:
        m, _ = model.from_plain(_plain(asserted_by=[{"path": "t.py"}]))
        self.assertTrue(_has(_codes(m), "INV-ASSERTION-SHAPE", "missing `symbol`, `run`"))

    def test_mixed_shape(self) -> None:
        m, _ = model.from_plain(_plain(asserted_by=[{"owed": "s1", "path": "t.py"}]))
        self.assertTrue(_has(_codes(m), "INV-ASSERTION-SHAPE", "mixes the owed shape"))

    def test_present_but_empty(self) -> None:
        m, _ = model.from_plain(_plain(asserted_by=[]))
        self.assertTrue(_has(_codes(m), "INV-ASSERTION-SHAPE", "present but empty"))


class CoverageRules(unittest.TestCase):
    """DICT: INV-COVERAGE-WELLFORMED — every arm, including the ones the Model already screens."""

    def _map(self, cov: Coverage) -> Map:
        m, _ = model.from_plain({"schema_version": 1, "bindings": {}})
        m.coverage = cov
        return m

    def test_neither_key(self) -> None:
        codes = _codes(self._map(Coverage()))
        self.assertTrue(_has(codes, "INV-COVERAGE-WELLFORMED", "neither fully_bound nor curated"))

    def test_fully_bound_arms(self) -> None:
        self.assertTrue(
            _has(_codes(self._map(Coverage(fully_bound=[]))), "INV-COVERAGE-WELLFORMED", "empty")
        )
        raw = validator.validate(self._map(Coverage(fully_bound=["bad-kind", "API", "API"])))
        codes = [(f.code, f.message) for f in raw]  # unfinalised: both share the coverage anchor
        self.assertTrue(_has(codes, "INV-COVERAGE-WELLFORMED", "`bad-kind` is not a kind"))
        self.assertTrue(_has(codes, "INV-COVERAGE-WELLFORMED", "`API` is listed twice"))

    def test_curated_arms(self) -> None:
        self.assertTrue(
            _has(_codes(self._map(Coverage(curated={}))), "INV-COVERAGE-WELLFORMED", "empty")
        )
        cov = Coverage(curated={"bad-kind": CuratedEntry("why"), "API": CuratedEntry("")})
        codes = _codes(self._map(cov))
        self.assertTrue(_has(codes, "INV-COVERAGE-WELLFORMED", "`bad-kind` is not a kind"))
        self.assertTrue(_has(codes, "INV-COVERAGE-WELLFORMED", "reason for `API` is empty"))


class PathCheck(unittest.TestCase):
    """DICT: INV-PATH-EXISTS — bound-assertion paths are checked too, at the assertion anchor."""

    def test_bound_assertion_path_under_the_flag(self) -> None:
        m, _ = model.from_plain(
            _plain(asserted_by=[{"path": "tests/nope.py", "symbol": "t", "run": "r"}])
        )
        self.assertEqual(validator.validate(m), [])
        findings = validator.validate(m, check_paths=True, root=".")
        self.assertEqual(
            [(f.code, f.anchor.type) for f in findings], [("INV-PATH-EXISTS", "assertion")]
        )


class ModelEdges(unittest.TestCase):
    def test_type_names(self) -> None:
        cases = [
            (True, "boolean"),
            (1, "integer"),
            (1.5, "number"),
            ("s", "string"),
            ({}, "mapping"),
            ([], "list"),
            (None, "null"),
            (object(), "object"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(model._type_name(value), expected)

    def test_check_node_rejects_an_unknown_node(self) -> None:
        with self.assertRaises(ValueError):
            model.check_node({}, "no-such-node")


class LoaderEdges(unittest.TestCase):
    def test_line_of_falls_back_to_none(self) -> None:
        self.assertIsNone(loader._line_of({"a": 1}, "a"))
        from ruamel.yaml.comments import CommentedMap

        self.assertIsNone(loader._line_of(CommentedMap(), "missing"))

    def test_anchor_tables_ignore_objects_without_lines(self) -> None:
        m, _ = model.from_plain(_plain(locators=[{"path": "a.py"}]))
        anchors = loader._Anchors(m)
        self.assertEqual((anchors.start, anchors.end, anchors.inner), ({}, {}, set()))

    def test_inner_line_of_a_three_line_entry_cannot_carry_a_comment(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "b.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\nbindings:\n  ENTITY-A:\n    locators:\n"
                    "      - path: a.py\n        symbol: A # middle\n        role: producer\n"
                )
            with self.assertRaises(ParseError):
                loader.load(path)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\nbindings:\n  ENTITY-A:\n    locators:\n"
                    "      - path: a.py\n        symbol: A\n        role: producer # last\n"
                )
            m, _ = loader.load(path)
            self.assertEqual(m.bindings["ENTITY-A"].locators[0].comment, "last")


class AnchorsAreHashable(unittest.TestCase):
    def test_key(self) -> None:
        self.assertEqual(Anchor("binding", id="X").key(), Anchor("binding", id="X").key())


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
