"""Fitness tier: naming clause, licence/contribution sentences, pins, workflow, schema file, licence
gate.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import unittest
from importlib import metadata
from typing import cast

from dbind import schema
from tests._helpers import ROOT, run_cli

INDEPENDENCE = (
    "dictum-binder is an independent tool for Dictum binding maps. "
    "It is not part of the official Dictum project and is not endorsed or certified by it."
)


def _read(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


class Naming(unittest.TestCase):
    """DICT: LEGAL-DICTUM-NAMING / POLICY-NAMING-ENFORCEMENT"""

    def test_clause_1_independence_sentence_verbatim(self) -> None:
        self.assertIn(INDEPENDENCE, _read("README.md").replace("\n", " "))

    def test_clause_2_versioned_conformance_phrase_and_no_forbidden_claims(self) -> None:
        readme = _read("README.md").replace("\n", " ").replace(INDEPENDENCE, "")
        help_text = run_cli(["--help"]).stdout
        phrase = re.compile(r"targets\s+Dictum v\d+\.\d+\.\d+ binding maps", re.IGNORECASE)
        self.assertRegex(readme, phrase)
        self.assertRegex(help_text, phrase)
        authored_against = re.search(
            r"authored_against:\s*(v\d+\.\d+\.\d+)", _read("docs/manifest.yaml")
        )
        assert authored_against is not None
        self.assertIn(f"Dictum {authored_against.group(1)} binding maps", readme)
        for text, where in ((readme, "README"), (help_text, "--help")):
            for sentence in re.split(r"(?<=[.!?])\s+", text):
                if "Dictum" in sentence:
                    self.assertNotRegex(
                        sentence, r"\b(certified|official|endorsed)\b", f"{where}: {sentence}"
                    )

    def test_clause_3_no_normative_text_reproduced_in_product_artifacts(self) -> None:
        sources = [os.path.join(ROOT, "dictum", "STANDARD.md")] + [
            os.path.join(ROOT, "dictum", "concerns", f)
            for f in os.listdir(os.path.join(ROOT, "dictum", "concerns"))
        ]
        paragraphs: set[str] = set()
        for path in sources:
            with open(path, encoding="utf-8") as handle:
                for para in handle.read().split("\n\n"):
                    flat = " ".join(para.split())
                    if len(re.findall(r"[.!?](\s|$)", flat)) > 2 and len(flat) > 200:
                        paragraphs.add(flat)
        product: list[str] = [os.path.join(ROOT, "README.md")]
        for tree in ("docs", "src", "tests", "tools"):
            for dirpath, _, files in os.walk(os.path.join(ROOT, tree)):
                product += [
                    os.path.join(dirpath, f)
                    for f in files
                    if f.endswith((".md", ".py", ".yaml", ".yml", ".json"))
                ]
        for path in product:
            with open(path, encoding="utf-8") as handle:
                flat = " ".join(handle.read().split())
            for para in paragraphs:
                self.assertNotIn(
                    para, flat, f"{os.path.relpath(path, ROOT)} reproduces a normative paragraph"
                )

    def test_clause_4_license_file(self) -> None:
        license_text = _read("LICENSE")
        self.assertTrue(license_text.startswith("MIT License"))
        self.assertIn("Copyright (c) 2026 David H. Jung", license_text)
        self.assertIn("Permission is hereby granted, free of charge", license_text)


class LicenceAndContributionSentences(unittest.TestCase):
    """DICT: POLICY-OUTBOUND-MIT / POLICY-CONTRIBUTIONS-MIT"""

    def test_readme_names_mit_and_contribution_terms_and_attribution(self) -> None:
        readme = _read("README.md")
        self.assertIn("MIT licence", readme)
        self.assertIn(
            "Contributions are accepted under the same MIT terms; no CLA and no sign-off",
            readme.replace("\n", " "),
        )
        self.assertIn("David H. Jung and the Dictum contributors", readme.replace("\n", " "))
        self.assertIn('license = "MIT"', _read("pyproject.toml"))


class PinsAndWorkflow(unittest.TestCase):
    """DICT: DEP-RUAMEL-YAML / TOOL-* / ENV-CI.

    Operations acceptance 1–2, Integrations acceptance 1.
    """

    def test_pyproject_pins(self) -> None:
        text = _read("pyproject.toml")
        self.assertIn('dependencies = ["ruamel.yaml>=0.19,<0.20"]', text)
        self.assertIn('dev = ["ruff>=0.16,<0.17", "pyrefly>=1.3,<1.4"]', text)
        self.assertIn('requires = ["setuptools>=84,<85"]', text)
        self.assertIn('dbind = "dbind.cli:main"', text)
        self.assertIn('requires-python = ">=3.11"', text)
        version = re.search(r'^version = "(\d+)\.', text, re.M)
        assert version is not None
        self.assertEqual(int(version.group(1)), schema.SCHEMA_VERSION)

    def test_workflow(self) -> None:
        text = _read(".github/workflows/ci.yml")
        self.assertIn("actions/checkout@v7", text)
        self.assertIn("actions/setup-python@v7", text)
        self.assertIn('python-version: "3.11"', text)
        for gate in ("gate 1:", "gate 2:", "gate 3:", "gate 4:", "gate 5:", "gate 6:", "gate 7:"):
            self.assertIn(gate, text)
        self.assertIn("pip wheel . --no-deps", text)
        self.assertIn("python -m venv e2e", text)
        self.assertIn("fetch-depth: 0", text)


class SchemaFile(unittest.TestCase):
    """Architecture acceptance 6 / Quality gate 5 / SUCCESS-SCHEMA-MATCH (partial: README value)."""

    def test_shipped_file_equals_embedded_schema_and_readme_checksum(self) -> None:
        with open(os.path.join(ROOT, "dbind.schema.json"), "rb") as handle:
            shipped = handle.read()
        self.assertEqual(shipped, schema.schema_json())
        self.assertEqual(hashlib.sha256(shipped).hexdigest(), schema.checksum())
        self.assertIn(schema.checksum(), _read("README.md"))
        for key in ("token", "secret", "password", "credential"):
            self.assertNotIn(key, shipped.decode("utf-8").lower())


class LicenceGate(unittest.TestCase):
    """DICT: POLICY-INBOUND-MIT-ONLY — the matching rule and its run over this environment."""

    def test_matching_rule(self) -> None:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        try:
            import licence_gate
        finally:
            sys.path.pop(0)
        v = licence_gate.verdict
        self.assertEqual(v("MIT", [], None), (True, "MIT via License-Expression"))
        self.assertEqual(
            v(None, ["License :: OSI Approved :: MIT License"], None), (True, "MIT via classifier")
        )
        self.assertEqual(v(None, [], "MIT License"), (True, "MIT via License"))
        self.assertFalse(v("BSD-3-Clause", [], None)[0])
        self.assertFalse(v(None, ["License :: OSI Approved :: BSD License"], None)[0])
        self.assertFalse(v(None, [], "Apache 2.0")[0])
        self.assertEqual(v(None, [], None), (False, "missing: no licence metadata"))
        self.assertTrue(v("MIT", [], "BSD")[1].startswith("ambiguous"))
        self.assertFalse(
            v("MIT", ["License :: OSI Approved :: MIT License", "License :: Other"], None)[0]
        )
        self.assertEqual(licence_gate.normalise_license_field("  MIT   license "), "mit")

        class Fake:
            def __init__(self, name: str, meta: dict[str, object]) -> None:
                self.version = "1"
                self._meta = {"Name": name, **meta}

            @property
            def metadata(self) -> object:
                meta = self._meta

                class M:
                    def __getitem__(self, key: str) -> object:
                        return meta[key]

                    def __contains__(self, key: object) -> bool:
                        return key in meta

                    def get(self, key: str, default: object = None) -> object:
                        return meta.get(key, default)

                    def get_all(self, key: str) -> object:
                        return meta.get(key)

                return M()

        fakes = [
            Fake("bsdpkg", {"License": "BSD"}),
            Fake("pip", {}),
            Fake("nometa", {}),
            Fake("good", {"License-Expression": "MIT"}),
        ]
        lines, failures = licence_gate.run(cast(list[metadata.Distribution], fakes))
        self.assertEqual(failures, ["bsdpkg", "nometa"])
        self.assertEqual(len(lines), 4)

    def test_gate_passes_in_this_environment(self) -> None:
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "licence_gate.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ruamel.yaml", proc.stdout)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
