"""Model value types, the rule table, and the JSON Schema derived from it."""

from __future__ import annotations

import json
import unittest

from lspd import model, schema
from lspd.model import (
    SHAPE,
    Anchor,
    Binding,
    Coverage,
    CuratedEntry,
    FieldLocator,
    Locator,
    Map,
    Wire,
)


class ContractIdGrammar(unittest.TestCase):
    """DICT: INV-ID-GRAMMAR — Domain acceptance 2."""

    def test_table(self) -> None:
        cases = {
            "CAP-003": False,
            "API-V2-USERS": True,
            "SCREEN-3D": True,
            "cap-003": False,
            "CAP": False,
            "ENTITY-ORDER.status": False,
            "INV-USER-EMAIL-UNIQUE": True,
            "A1-B2": True,
            "X9-99": False,
            "1AB-CD": False,
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(model.is_contract_id(value), expected)
        self.assertEqual(model.kind_of("ENTITY-USER-PROFILE"), "ENTITY")


class PathForm(unittest.TestCase):
    """DICT: ENTITY-PATH"""

    def test_table(self) -> None:
        good = ["src/x.py", "a", "dir.d/file", "src/models/user.py"]
        bad = ["", "   ", "/abs/x", "C:/x", "a\\b", "~/x", "a//b", "a/./b", "../x", "a/..", "a/"]
        for value in good:
            with self.subTest(value=value):
                self.assertIsNone(model.path_form_problem(value))
        for value in bad:
            with self.subTest(value=value):
                self.assertIsNotNone(model.path_form_problem(value))


class ControlCharacters(unittest.TestCase):
    """DICT: INV-SYMBOL-NONEMPTY — C0, DEL and C1 are control characters."""

    def test_table(self) -> None:
        self.assertFalse(model.has_control_chars("plain text é"))
        for ch in ("\n", "\t", "\r", "\x00", "\x7f", "\x85", "\x9f"):
            with self.subTest(ch=repr(ch)):
                self.assertTrue(model.has_control_chars(f"a{ch}b"))


class FromPlain(unittest.TestCase):
    def test_type_and_required_key_violations_report_closed_keys(self) -> None:
        cases = [
            ({"schema_version": True, "bindings": {}}, "schema_version"),
            ({"schema_version": 1, "bindings": []}, "bindings"),
            ({"schema_version": 1, "bindings": {"ENTITY-A": []}}, "binding"),
            ({"schema_version": 1, "bindings": {"ENTITY-A": {}}}, "locators"),
            ({"schema_version": 1, "bindings": {"ENTITY-A": {"locators": "x"}}}, "locators"),
            ({"schema_version": 1, "bindings": {"ENTITY-A": {"locators": ["x"]}}}, "a locator"),
            (
                {"schema_version": 1, "bindings": {"ENTITY-A": {"locators": [{"symbol": "f"}]}}},
                "path",
            ),
            ({"schema_version": 1, "bindings": {"ENTITY-A": {"locators": [{"path": 3}]}}}, "path"),
            (
                {"schema_version": 1, "bindings": {"ENTITY-A": {"locators": [], "fields": []}}},
                "fields",
            ),
            (
                {
                    "schema_version": 1,
                    "bindings": {"ENTITY-A": {"locators": [], "fields": {"n": 1}}},
                },
                "field",
            ),
            ({"schema_version": 1, "bindings": {"ENTITY-A": {"locators": [], "wire": 1}}}, "wire"),
            (
                {
                    "schema_version": 1,
                    "bindings": {"ENTITY-A": {"locators": [], "asserted_by": {}}},
                },
                "asserted_by",
            ),
            (
                {
                    "schema_version": 1,
                    "bindings": {"ENTITY-A": {"locators": [], "asserted_by": [1]}},
                },
                "an assertion",
            ),
            ({"schema_version": 1, "bindings": {}, "coverage": 1}, "coverage"),
            (
                {"schema_version": 1, "bindings": {}, "coverage": {"fully_bound": "ENTITY"}},
                "fully_bound",
            ),
            (
                {"schema_version": 1, "bindings": {}, "coverage": {"fully_bound": [1]}},
                "fully_bound",
            ),
            ({"schema_version": 1, "bindings": {}, "coverage": {"curated": []}}, "curated"),
            ({"schema_version": 1, "bindings": {}, "coverage": {"curated": {"API": 1}}}, "API"),
            ([], "document"),
        ]
        for plain, needle in cases:
            with self.subTest(needle=needle):
                _, findings = model.from_plain(plain)
                self.assertTrue(findings, plain)
                self.assertTrue(
                    all(f.code == "INV-CLOSED-KEYS" for f in findings), [f.code for f in findings]
                )
                self.assertTrue(
                    any(needle in f.message for f in findings), [f.message for f in findings]
                )

    def test_role_enum_and_grammar_messages(self) -> None:
        _, findings = model.from_plain(
            {
                "schema_version": 1,
                "bindings": {"ENTITY-A": {"locators": [{"path": "a", "role": "x"}]}},
            }
        )
        self.assertEqual([f.code for f in findings], ["INV-ROLE-VALUES"])
        _, findings = model.from_plain(
            {"schema_version": 1, "bindings": {"CAP-003": {"locators": []}}}
        )
        self.assertIn("all-digit segment", findings[0].message)
        _, findings = model.from_plain({"schema_version": 1, "bindings": {"cap": {"locators": []}}})
        self.assertIn("not a contract ID", findings[0].message)

    def test_full_binding_converts_and_projects_back(self) -> None:
        plain = {
            "schema_version": 1,
            "bindings": {
                "ENTITY-A": {
                    "locators": [{"path": "a.py", "symbol": "A", "role": "producer"}],
                    "compare_via": "openapi",
                    "fields": {"x": {"path": "a.py", "symbol": "A.x"}},
                    "wire": {"casing": "camelCase"},
                    "asserted_by": [
                        {"path": "t.py", "symbol": "t", "run": "r", "arm": "a"},
                        {"owed": "s9"},
                    ],
                }
            },
            "coverage": {"fully_bound": ["ENTITY"], "curated": {"API": "why"}},
        }
        m, findings = model.from_plain(plain)
        self.assertEqual(findings, [])
        self.assertEqual(model.map_to_plain(m), plain)
        self.assertEqual(m.bindings["ENTITY-A"].kind, "ENTITY")
        asserted = m.bindings["ENTITY-A"].asserted_by
        assert asserted is not None
        self.assertEqual(asserted[0].identity(), ("bound", "t.py", "t", "a"))
        self.assertEqual(asserted[1].identity(), ("owed", "s9", None))

    def test_check_node_covers_every_node(self) -> None:
        self.assertEqual(model.check_node({"path": "a"}, "locator"), [])
        self.assertEqual(model.check_node({"path": "a"}, "field_locator"), [])
        self.assertEqual(model.check_node({"owed": "s9"}, "assertion"), [])
        self.assertEqual(model.check_node({"fully_bound": ["A"]}, "coverage"), [])
        self.assertEqual(model.check_node({"locators": []}, "binding"), [])
        self.assertEqual(model.check_node({"schema_version": 1, "bindings": {}}, "document"), [])
        self.assertEqual(
            [f.code for f in model.check_node({"path": "a", "x": 1}, "locator")],
            ["INV-CLOSED-KEYS"],
        )


class JsonSchema(unittest.TestCase):
    """DICT: COMPONENT-SCHEMA — the generated document agrees with the rule table entry by entry."""

    def test_every_rule_table_entry_appears_in_the_schema(self) -> None:
        doc = schema.schema()
        nodes = {"document": doc, **doc["$defs"]}
        for node, spec in SHAPE.items():
            with self.subTest(node=node):
                props = nodes[node]["properties"]
                self.assertEqual(set(props), set(spec["keys"]))
                self.assertFalse(nodes[node]["additionalProperties"])
                self.assertEqual(nodes[node].get("required", []), spec["required"])
                for key, key_spec in spec["keys"].items():
                    kind = key_spec["type"]
                    if kind == "str":
                        self.assertEqual(props[key]["type"], "string")
                    elif kind == "int":
                        self.assertEqual(props[key]["type"], "integer")
                    elif kind == "enum":
                        self.assertEqual(props[key]["enum"], key_spec["values"])
                    elif kind == "node":
                        self.assertEqual(props[key]["$ref"], f"#/$defs/{key_spec['node']}")
                    elif kind == "list":
                        self.assertEqual(props[key]["type"], "array")
                    else:
                        self.assertEqual(props[key]["type"], "object")
        self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(
            doc["properties"]["bindings"]["propertyNames"]["pattern"], model.ID_PATTERN
        )

    def test_schema_json_is_deterministic_and_checksummed(self) -> None:
        first, second = schema.schema_json(), schema.schema_json()
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n") and not first.endswith(b"\n\n"))
        self.assertEqual(json.loads(first), schema.schema())
        self.assertEqual(len(schema.checksum()), 64)
        self.assertEqual(schema.check_shape({"path": "a"}, "locator"), [])
        self.assertEqual(schema.RULES, SHAPE)
        self.assertEqual(schema.SCHEMA_VERSION, 1)


class Dataclasses(unittest.TestCase):
    def test_anchor_projection_and_wire_emptiness(self) -> None:
        a = Anchor("locator", id="ENTITY-A", path="a", symbol="s")
        self.assertEqual(a.to_plain()["type"], "locator")
        self.assertEqual(a.key()[0], "locator")
        self.assertTrue(Wire().is_empty())
        self.assertFalse(Wire(casing="x").is_empty())
        b = Binding("ENTITY-A", locators=[Locator("a")], fields={"f": FieldLocator("a")})
        self.assertEqual(
            model.binding_to_plain(b), {"locators": [{"path": "a"}], "fields": {"f": {"path": "a"}}}
        )
        m = Map(schema_version=1, coverage=Coverage(curated={"API": CuratedEntry("r")}))
        self.assertEqual(model.map_to_plain(m)["coverage"], {"curated": {"API": "r"}})


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
