"""One test per INV-* over its violating fixture: exactly that code, at the contracted anchor."""

from __future__ import annotations

import os
import unittest

from dbind import loader, validator
from dbind.model import Finding
from tests._helpers import TempDir, fixture

WRITE_GATED = {
    # code: (fixture, anchor type, extra anchor fields)
    "INV-ID-GRAMMAR": ("inv-id-grammar.yaml", "binding", {"id": "CAP-003"}),
    "INV-SCHEMA-VERSION": ("inv-schema-version.yaml", "file", {}),
    "INV-CLOSED-KEYS": ("inv-closed-keys.yaml", "binding", {"id": "ENTITY-A"}),
    "INV-NO-LINE-NUMBERS": (
        "inv-no-line-numbers.yaml",
        "locator",
        {"id": "ENTITY-A", "path": "src/x.py:41", "symbol": "f"},
    ),
    "INV-PATH-FORM": (
        "inv-path-form.yaml",
        "locator",
        {"id": "ENTITY-A", "path": "../x.py", "symbol": "f"},
    ),
    "INV-SYMBOL-NONEMPTY": (
        "inv-symbol-nonempty.yaml",
        "locator",
        {"id": "ENTITY-A", "path": "src/x.py", "symbol": ""},
    ),
    "INV-ROLE-VALUES": ("inv-role-values.yaml", "locator", {"id": "ENTITY-A"}),
    "INV-WIRE-SUBSET": ("inv-wire-subset.yaml", "binding", {"id": "ENTITY-A"}),
    "INV-ASSERTION-SHAPE": (
        "inv-assertion-shape.yaml",
        "assertion",
        {"id": "INV-A", "path": "tests/t.py", "symbol": "t", "owed": "slice-9"},
    ),
    "INV-FIELD-NAME": ("inv-field-name.yaml", "binding", {"id": "ENTITY-A"}),
    "INV-COVERAGE-WELLFORMED": ("inv-coverage-wellformed.yaml", "curated", {"kind": "ENTITY"}),
    "INV-LOCATOR-UNIQUE": (
        "inv-locator-unique.yaml",
        "locator",
        {"id": "ENTITY-A", "path": "src/x.py", "symbol": "f"},
    ),
    "INV-ASSERTION-UNIQUE": (
        "inv-assertion-unique.yaml",
        "assertion",
        {"id": "INV-A", "owed": "slice-9"},
    ),
    "INV-COMMENT-ANCHORED": (
        "inv-comment-anchored.yaml",
        "locator",
        {"id": "ENTITY-A", "path": "src/x.py", "symbol": "f"},
    ),
    "INV-COMMENT-TEXT": ("inv-comment-text.yaml", "binding", {"id": "ENTITY-A"}),
}

ADVISORY = {
    "INV-BYTES": ("inv-bytes.yaml", "file"),
    "INV-ROLE-REQUIRES-WIRE": ("inv-role-requires-wire.yaml", "binding"),
    "INV-OWNED-TWICE": ("inv-owned-twice.yaml", "locator"),
}


def findings_for(name: str, *, check_paths: bool = False, root: str = ".") -> list[Finding]:
    m, loaded = loader.load(fixture(name), size_limit=True)
    return validator.finalize(loaded + validator.validate(m, check_paths=check_paths, root=root))


class WriteGatedInvariants(unittest.TestCase):
    def test_each_write_gated_invariant_fires_exactly_once(self) -> None:
        for code, (name, anchor_type, extra) in WRITE_GATED.items():
            with self.subTest(code=code):
                found = findings_for(name)
                errors = [f for f in found if f.severity == "error"]
                self.assertEqual([f.code for f in errors], [code], [f.message for f in found])
                self.assertEqual(errors[0].anchor.type, anchor_type)
                for key, value in extra.items():
                    self.assertEqual(getattr(errors[0].anchor, key), value)

    def test_advisory_invariants_are_warnings(self) -> None:
        for code, (name, anchor_type) in ADVISORY.items():
            with self.subTest(code=code):
                found = findings_for(name)
                self.assertTrue(found, code)
                self.assertTrue(
                    all(f.severity == "warning" for f in found), [f.code for f in found]
                )
                self.assertIn(code, {f.code for f in found})
                self.assertEqual(found[0].anchor.type, anchor_type)

    def test_owned_twice_names_the_other_binding(self) -> None:
        found = findings_for("inv-owned-twice.yaml")
        messages = {f.anchor.id: f.message for f in found}
        self.assertIn("ENTITY-B", messages["ENTITY-A"])
        self.assertIn("ENTITY-A", messages["ENTITY-B"])

    def test_path_exists_only_with_the_flag(self) -> None:
        self.assertEqual(findings_for("inv-path-exists.yaml"), [])
        with TempDir() as tmp:
            found = findings_for("inv-path-exists.yaml", check_paths=True, root=tmp)
            self.assertEqual([f.code for f in found], ["INV-PATH-EXISTS"])
            self.assertEqual(found[0].severity, "error")
            os.makedirs(os.path.join(tmp, "no", "such"))
            with open(os.path.join(tmp, "no", "such", "file.py"), "w", encoding="utf-8") as handle:
                handle.write("")
            self.assertEqual(findings_for("inv-path-exists.yaml", check_paths=True, root=tmp), [])

    def test_lines_key_fires_both_closed_keys_and_no_line_numbers(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "bindings.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\n\nbindings:\n\n  ENTITY-A:\n    locators:\n"
                    "      - { path: src/x.py, symbol: f, lines: 40-52 }\n"
                )
            m, loaded = loader.load(path)
            codes = sorted(f.code for f in validator.finalize(loaded + validator.validate(m)))
            self.assertEqual(codes, ["INV-CLOSED-KEYS", "INV-NO-LINE-NUMBERS"])

    def test_missing_schema_version_fires_both_codes(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "bindings.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("bindings: {}\n")
            m, loaded = loader.load(path)
            codes = sorted(f.code for f in validator.finalize(loaded + validator.validate(m)))
            self.assertEqual(codes, ["INV-CLOSED-KEYS", "INV-SCHEMA-VERSION"])

    def test_findings_are_in_document_order_then_code_and_deduplicated(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "bindings.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\n\nbindings:\n\n  ENTITY-B:\n    locators:\n"
                    "      - { path: ../b.py, symbol: b }\n\n"
                    '  ENTITY-A:\n    locators:\n      - { path: src/a.py, symbol: "" }\n'
                    '      - { path: src/a.py, symbol: "" }\n'
                )
            m, loaded = loader.load(path)
            found = validator.finalize(loaded + validator.validate(m))
            self.assertEqual(
                [f.code for f in found],
                ["INV-PATH-FORM", "INV-SYMBOL-NONEMPTY", "INV-LOCATOR-UNIQUE"],
            )
            self.assertEqual([f.anchor.id for f in found], ["ENTITY-B", "ENTITY-A", "ENTITY-A"])


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
