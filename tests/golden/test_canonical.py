"""Golden tier: the canonical layout and round-trip fidelity. DICT: SUCCESS-ROUNDTRIP"""

from __future__ import annotations

import os
import unittest

from dbind import emitter, loader, validator
from tests._helpers import DOCS, FIXTURES, TempDir, fixture, read_bytes, run_cli


def _emit_after_load(path: str) -> bytes:
    m, _ = loader.load(path)
    return emitter.emit(m)


class Canonical(unittest.TestCase):
    def test_fixture_is_byte_identical_to_domain_example(self) -> None:
        """Quality acceptance 5 / Domain acceptance 8."""
        with open(os.path.join(DOCS, "domain-and-data.md"), encoding="utf-8") as handle:
            doc = handle.read()
        start = doc.index("```yaml\n# Optional header comment block") + len("```yaml\n")
        end = doc.index("\n```", start)
        self.assertEqual(
            read_bytes(fixture("canonical.yaml")), (doc[start:end] + "\n").encode("utf-8")
        )

    def test_canonical_validates_clean_and_round_trips(self) -> None:
        m, loaded = loader.load(fixture("canonical.yaml"))
        self.assertEqual(validator.finalize(loaded + validator.validate(m)), [])
        self.assertEqual(emitter.emit(m), read_bytes(fixture("canonical.yaml")))

    def test_emit_is_a_fixpoint_for_every_loadable_fixture(self) -> None:
        """DICT: INV-CANONICAL-FIXPOINT — emit(load(emit(load(f)))) == emit(load(f))."""
        with TempDir() as tmp:
            for name in sorted(os.listdir(FIXTURES)):
                if name.startswith("err-parse"):
                    continue
                m, loaded = loader.load(fixture(name))
                if any(f.severity == "error" for f in loaded + validator.validate(m)):
                    # format refuses error-level maps, so the fixpoint property does not apply
                    continue
                with self.subTest(fixture=name):
                    first = emitter.emit(m)
                    path = os.path.join(tmp, name)
                    with open(path, "wb") as handle:
                        handle.write(first)
                    self.assertEqual(_emit_after_load(path), first)

    def test_format_applied_twice_equals_format_applied_once(self) -> None:
        """DICT: SUCCESS-ROUNDTRIP / INV-CANONICAL-FIXPOINT — through the format command, for
        every fixture, canonical or not (an error-level map is refused both times)."""
        for name in sorted(os.listdir(FIXTURES)):
            with self.subTest(fixture=name), TempDir() as tmp:
                target = os.path.join(tmp, "bindings.yaml")
                with open(target, "wb") as handle:
                    handle.write(read_bytes(fixture(name)))
                first = run_cli(["format"], cwd=tmp)
                after_first = read_bytes(target)
                second = run_cli(["format"], cwd=tmp)
                self.assertEqual(read_bytes(target), after_first)
                self.assertEqual(second.code, first.code)
                if first.code == 0:
                    self.assertEqual(second.envelope["result"]["changed"], False)
                    self.assertEqual(run_cli(["format", "--check"], cwd=tmp).code, 0)
                else:
                    self.assertEqual(after_first, read_bytes(fixture(name)))

    def test_noncanonical_layout_is_repaired_but_order_kept(self) -> None:
        out = _emit_after_load(fixture("noncanonical.yaml")).decode("utf-8")
        self.assertEqual(
            out,
            "schema_version: 1\n\nbindings:\n\n  ROUTE-B:\n    locators:\n"
            "      - { path: web/b.ts, symbol: B }\n\n"
            "  ENTITY-A:\n    locators:\n      - { path: src/a.py, symbol: A }\n\ncoverage:\n"
            "  fully_bound: [ROUTE, ENTITY]\n",
        )


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
