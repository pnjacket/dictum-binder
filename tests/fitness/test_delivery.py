"""Fitness tier: the coverage-map meta-test, the build-status record, and docs-never-trail-code."""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import unittest

from tests import coverage_map
from tests._helpers import DOCS, ROOT

ID_TOKEN = re.compile(r"^\| `([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)`")
CONCERN_DOCS = [
    f for f in os.listdir(DOCS) if f.endswith(".md") and f not in ("README.md", "IMPLEMENTATION.md")
]
NON_CODE_PREFIXES = ("PERSONA",)


def minted_ids() -> dict[str, str]:
    """ID → owning doc, from Contracts-section table rows whose first cell starts with the ID."""
    out: dict[str, str] = {}
    for name in CONCERN_DOCS:
        with open(os.path.join(DOCS, name), encoding="utf-8") as handle:
            text = handle.read()
        if "\n## Contracts" not in text:
            continue
        contracts = text.split("\n## Contracts", 1)[1].split("\n## Acceptance criteria", 1)[0]
        for line in contracts.split("\n"):
            m = ID_TOKEN.match(line)
            if m:
                out[m.group(1)] = name
    return out


def build_status() -> dict[int, dict[str, object]]:
    """Slice rows of docs/IMPLEMENTATION.md: number → {built, completes(set), proof}."""
    with open(os.path.join(DOCS, "IMPLEMENTATION.md"), encoding="utf-8") as handle:
        text = handle.read()
    rows: dict[int, dict[str, object]] = {}
    for line in text.split("\n"):
        m = re.match(
            r"^\| (\d) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", line
        )
        if m:
            completes = set(re.findall(r"`([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)`", m.group(5)))
            rows[int(m.group(1))] = {
                "built": "✅" in m.group(6),
                "verified": m.group(7).strip(),
                "completes": completes,
                "proof": m.group(8),
            }
    return rows


def built_ids() -> set[str]:
    return {i for row in build_status().values() if row["built"] for i in row["completes"]}  # type: ignore[union-attr]


def _resolve(test_id: str) -> bool:
    module, cls, method = test_id.rsplit(".", 2)
    mod = importlib.import_module(module)
    return callable(getattr(getattr(mod, cls), method, None))


class CoverageMap(unittest.TestCase):
    """Quality acceptance 1 — every minted ID has a row; non-n/a rows for Built IDs name existing
    tests.
    """

    def test_every_minted_id_has_a_row_and_built_rows_resolve(self) -> None:
        minted = minted_ids()
        self.assertGreater(len(minted), 100)
        missing = sorted(set(minted) - set(coverage_map.MAP) - {"E2E-STANDARD"})
        self.assertEqual(missing, [], "IDs without a coverage-map row")
        extra = sorted(set(coverage_map.MAP) - set(minted) - {"E2E-STANDARD"})
        self.assertEqual(extra, [], "coverage-map rows for unminted IDs")
        built = built_ids() | {"E2E-STANDARD"}
        skipped: list[str] = []
        for contract_id, tests in coverage_map.MAP.items():
            if isinstance(tests, str):
                self.assertTrue(tests.startswith("n/a — "), contract_id)
                continue
            if contract_id not in built:
                skipped.append(contract_id)
                continue
            with self.subTest(id=contract_id):
                self.assertTrue(tests, f"{contract_id} completes in a Built slice but has no test")
                for test_id in tests:
                    self.assertTrue(_resolve(test_id), f"{contract_id}: {test_id} does not exist")
        print(
            f"\ncoverage map: {len(skipped)} ID(s) skipped, their completing slice not yet Built: "
            f"{', '.join(skipped)}"
        )


class BuildStatus(unittest.TestCase):
    """Delivery acceptance 1–3 — the record exists, its Completes union is the code-realisable set,
    proofs resolve.
    """

    def test_record_shape(self) -> None:
        rows = build_status()
        self.assertEqual(sorted(rows), [1, 2, 3, 4, 5, 6])
        with open(os.path.join(DOCS, "IMPLEMENTATION.md"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("## Release-gate checklist", text)
        self.assertIn("## Source-provenance register", text)

    def test_completes_union_is_exactly_the_code_realisable_set(self) -> None:
        minted = minted_ids()
        code_realisable = {
            i
            for i in minted
            if not i.startswith(NON_CODE_PREFIXES)
            and not i.startswith("CAP-")
            and i != "SUCCESS-CROSS-MODEL"
        }
        rows = build_status()
        seen: dict[str, int] = {}
        for number, row in rows.items():
            for contract_id in row["completes"]:  # type: ignore[union-attr]
                if contract_id.startswith("CAP-"):
                    continue
                self.assertNotIn(
                    contract_id,
                    seen,
                    f"{contract_id} completes in slices {seen.get(contract_id)} and {number}",
                )
                seen[contract_id] = number
        self.assertEqual(sorted(set(seen) - code_realisable), [], "completed but not minted")
        self.assertEqual(
            sorted(code_realisable - set(seen)), [], "minted but completed by no slice"
        )

    def test_built_rows_name_existing_proofs(self) -> None:
        for number, row in build_status().items():
            if not row["built"]:
                continue
            with self.subTest(slice=number):
                self.assertIn(row["verified"], ("merge", "release"))
                modules = re.findall(r"`(tests\.[a-z_.]+)`", str(row["proof"]))
                self.assertTrue(modules, f"slice {number} proof names no test module")
                for module in modules:
                    importlib.import_module(module)


class DocsNeverTrailCode(unittest.TestCase):
    """Delivery acceptance 6 — a commit touching src/, tests/ or tools/ never also edits a published
    concern doc.
    """

    def test_commit_range(self) -> None:
        rng = os.environ.get("LSPD_CI_RANGE", "")
        if not rng or rng.startswith("0000000"):
            rng = "HEAD~1..HEAD"
        try:
            log = subprocess.run(
                ["git", "log", "--format=%H", rng],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.split()
        except subprocess.CalledProcessError:
            log = []
        for commit in log:
            files = subprocess.run(
                ["git", "show", "--name-only", "--format=", commit],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.split()
            touches_code = any(f.startswith(("src/", "tests/", "tools/")) for f in files)
            docs_touched = [
                f
                for f in files
                if f.startswith("docs/")
                and f.endswith(".md")
                and f not in ("docs/README.md", "docs/IMPLEMENTATION.md")
            ]
            if not touches_code or not docs_touched:
                continue
            for doc in docs_touched:
                diff = subprocess.run(
                    ["git", "show", "--format=", commit, "--", doc],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                changed = [
                    ln
                    for ln in diff.split("\n")
                    if (ln.startswith("+") or ln.startswith("-"))
                    and not ln.startswith(("+++", "---"))
                ]
                self.assertTrue(
                    all(re.match(r"^[+-](status|version): ", ln) for ln in changed),
                    f"commit {commit[:7]} changes code and the published doc {doc} together",
                )


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
