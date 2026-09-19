"""E2E journeys per capability, through the real installed binary (E2E-STANDARD)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from tests.e2e import _runner
from tests.e2e._runner import lspd

FIXTURES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")


class Journeys(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="lspd-e2e-")
        self.assertTrue(os.path.exists(_runner.LSPD), _runner.LSPD)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cap_init(self) -> None:
        """DICT: CAP-INIT"""
        run = lspd(["init"], self.tmp)
        self.assertEqual(run.code, 0, run.stdout)
        with open(os.path.join(self.tmp, "bindings.yaml"), "rb") as handle:
            self.assertEqual(handle.read(), b"schema_version: 1\n\nbindings: {}\n")
        self.assertEqual(lspd(["init"], self.tmp).envelope["error"]["code"], "ERR-FILE-EXISTS")
        self.assertEqual(lspd(["init", "--file", "other.yaml"], self.tmp).code, 0)
        self.assertEqual(lspd(["--human", "init", "--file", "third.yaml"], self.tmp).code, 0)
        self.assertEqual(lspd(["--debug", "init", "--file", "fourth.yaml"], self.tmp).stderr, "")

    def test_cap_validate_and_pathcheck(self) -> None:
        """DICT: CAP-VALIDATE / CAP-PATHCHECK"""
        shutil.copyfile(
            os.path.join(FIXTURES, "canonical.yaml"), os.path.join(self.tmp, "bindings.yaml")
        )
        run = lspd(["validate"], self.tmp)
        self.assertEqual(
            (run.code, run.envelope["result"]),
            (0, {"errors": 0, "warnings": 0, "paths_checked": False}),
        )
        self.assertEqual(lspd(["validate", "--no-size-limit"], self.tmp).code, 0)
        shutil.copyfile(
            os.path.join(FIXTURES, "inv-path-exists.yaml"), os.path.join(self.tmp, "bindings.yaml")
        )
        missing = lspd(["--check-paths", "validate"], self.tmp)
        self.assertEqual(
            (missing.code, missing.envelope["findings"]["pre"][0]["code"]), (1, "INV-PATH-EXISTS")
        )
        os.makedirs(os.path.join(self.tmp, "no", "such"))
        with open(os.path.join(self.tmp, "no", "such", "file.py"), "w", encoding="utf-8") as handle:
            handle.write("")
        self.assertEqual(lspd(["validate", "--check-paths"], self.tmp).code, 0)
        human = lspd(["validate", "--human"], self.tmp)
        self.assertEqual(human.code, 0)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(human.stdout)
        self.assertEqual(lspd(["validate", "--file", "nope.yaml"], self.tmp).code, 2)

    def test_cap_schema(self) -> None:
        """DICT: CAP-SCHEMA"""
        raw = lspd(["schema"], self.tmp)
        self.assertEqual(raw.code, 0)
        self.assertEqual(
            json.loads(raw.stdout)["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        checksum = lspd(["schema", "--checksum"], self.tmp)
        self.assertRegex(checksum.stdout, r"^[0-9a-f]{64}\n$")

    def test_cap_help(self) -> None:
        """DICT: CAP-HELP"""
        for argv in (["--help"], ["init", "--help"], ["validate", "--help"], ["schema", "--help"]):
            run = lspd(argv, self.tmp)
            self.assertEqual(run.code, 0)
            self.assertTrue(run.stdout.startswith("usage: lspd"))
        self.assertRegex(lspd(["--version"], self.tmp).stdout, r"^lspd \S+\n$")
        bare = lspd([], self.tmp)
        self.assertEqual((bare.code, bare.envelope["error"]["code"]), (1, "ERR-USAGE"))


class MetaInvocations(unittest.TestCase):
    """Quality acceptance 3 — every slice-1 element in default state and per element-specific flag;
    every global option once.
    """

    def test_every_built_element_was_driven(self) -> None:
        argvs = _runner.INVOCATIONS
        positional = {
            tuple(
                a
                for a in argv
                if not a.startswith("--")
                and a not in ("nope.yaml", "other.yaml", "third.yaml", "fourth.yaml")
            )
            for argv in argvs
        }
        for element in (("init",), ("validate",), ("schema",)):
            self.assertIn(element, positional, element)
        self.assertTrue(any(argv == ["schema", "--checksum"] for argv in argvs))
        self.assertTrue(any(argv == ["--help"] for argv in argvs))
        self.assertTrue(any(argv == ["--version"] for argv in argvs))
        flat = {a for argv in argvs for a in argv}
        for option in ("--file", "--human", "--check-paths", "--no-size-limit", "--debug"):
            self.assertIn(option, flat)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
