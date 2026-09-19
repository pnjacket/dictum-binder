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

    def test_cap_query(self) -> None:
        """DICT: CAP-QUERY"""
        shutil.copyfile(
            os.path.join(FIXTURES, "carriers.yaml"), os.path.join(self.tmp, "bindings.yaml")
        )
        got = lspd(["get", "ENTITY-A"], self.tmp)
        self.assertEqual(got.code, 0, got.stdout)
        (b,) = got.envelope["result"]["bindings"]
        self.assertEqual((b["id"], b["comment"]), ("ENTITY-A", "binding block\nsecond line"))
        listed = lspd(["list"], self.tmp)
        self.assertEqual(
            [r["id"] for r in listed.envelope["result"]["bindings"]], ["ENTITY-A", "ENTITY-B"]
        )
        self.assertEqual(lspd(["list", "--kind", "ENTITY"], self.tmp).code, 0)
        full = lspd(["list", "--full"], self.tmp)
        self.assertIn("locators", full.envelope["result"]["bindings"][0])
        missing = lspd(["get", "ENTITY-NOPE"], self.tmp)
        self.assertEqual((missing.code, missing.envelope["error"]["code"]), (1, "ERR-NOT-FOUND"))
        with open(os.path.join(self.tmp, "bindings.yaml"), "rb") as handle:
            self.assertEqual(
                handle.read(), open(os.path.join(FIXTURES, "carriers.yaml"), "rb").read()
            )

    def _seed(self) -> str:
        target = os.path.join(self.tmp, "bindings.yaml")
        shutil.copyfile(os.path.join(FIXTURES, "canonical.yaml"), target)
        return target

    def test_cap_set(self) -> None:
        """DICT: CAP-SET"""
        target = self._seed()
        doc = '{"locators": [{"path": "src/x.py", "symbol": "X", "comment": "c"}], "comment": "b"}'
        run = lspd(["set", "INV-X", "--json", doc], self.tmp)
        self.assertEqual(run.code, 0, run.stdout)
        self.assertEqual(run.envelope["result"]["binding"]["comment"], "b")
        text = open(target, encoding="utf-8").read()
        self.assertIn(
            "  # b\n  INV-X:\n    locators:\n      - { path: src/x.py, symbol: X } # c\n", text
        )
        self.assertEqual(lspd(["set", "INV-X", "--json", '{"locators": []}'], self.tmp).code, 0)
        self.assertEqual(lspd(["set", "INV-X", "--json", "nope"], self.tmp).code, 1)
        self.assertEqual(lspd(["validate"], self.tmp).code, 0)

    def test_cap_add(self) -> None:
        """DICT: CAP-ADD"""
        self._seed()
        loc = lspd(
            [
                "add-locator",
                "ROUTE-HOME",
                "--path",
                "web/h.ts",
                "--symbol",
                "H",
                "--role",
                "producer",
                "--comment",
                "c",
            ],
            self.tmp,
        )
        self.assertEqual(loc.code, 0, loc.stdout)
        self.assertEqual(
            lspd(
                ["add-locator", "ROUTE-HOME", "--path", "web/h.ts", "--symbol", "H"], self.tmp
            ).envelope["error"]["code"],
            "ERR-DUPLICATE",
        )
        fld = lspd(
            [
                "add-field",
                "ROUTE-HOME",
                "title",
                "--path",
                "web/h.ts",
                "--symbol",
                "H.title",
                "--comment",
                "c",
            ],
            self.tmp,
        )
        self.assertEqual(fld.code, 0, fld.stdout)
        self.assertEqual(
            lspd(["add-field", "ROUTE-HOME", "title", "--path", "web/h2.ts"], self.tmp).code, 0
        )
        bound = lspd(
            [
                "add-assertion",
                "ROUTE-HOME",
                "--path",
                "t.py",
                "--symbol",
                "t_h",
                "--run",
                "python3 -m unittest t",
                "--arm",
                "a",
                "--comment",
                "c",
            ],
            self.tmp,
        )
        self.assertEqual(bound.code, 0, bound.stdout)
        self.assertEqual(
            lspd(["add-assertion", "ROUTE-HOME", "--owed", "slice-4"], self.tmp).code, 0
        )
        self.assertEqual(
            lspd(["add-assertion", "ROUTE-HOME", "--path", "t.py"], self.tmp).envelope["error"][
                "code"
            ],
            "ERR-USAGE",
        )
        self.assertEqual(lspd(["add-locator", "ENTITY-NOPE", "--path", "x.py"], self.tmp).code, 1)
        self.assertEqual(lspd(["validate"], self.tmp).code, 0)

    def test_cap_remove(self) -> None:
        """DICT: CAP-REMOVE"""
        self._seed()
        self.assertEqual(lspd(["remove", "ENTITY-USER", "--field", "config"], self.tmp).code, 0)
        self.assertEqual(
            lspd(
                ["remove", "ENTITY-USER", "--assertion", "--owed", "slice-9", "--arm", "c"],
                self.tmp,
            ).code,
            0,
        )
        self.assertEqual(
            lspd(
                [
                    "remove",
                    "ENTITY-USER",
                    "--assertion",
                    "--path",
                    "tests/test_user.py",
                    "--symbol",
                    "test_email_case",
                    "--arm",
                    "b",
                ],
                self.tmp,
            ).code,
            0,
        )
        stub = lspd(
            ["remove", "ROUTE-HOME", "--locator", "--path", "web/src/app.routes.ts"], self.tmp
        )
        self.assertEqual(stub.envelope["result"]["binding"]["locators"], [])
        whole = lspd(["remove", "SCREEN-STUB"], self.tmp)
        self.assertEqual(whole.envelope["result"], {"binding": None, "removed": "SCREEN-STUB"})
        self.assertEqual(
            lspd(["remove", "SCREEN-STUB"], self.tmp).envelope["error"]["code"], "ERR-NOT-FOUND"
        )
        self.assertEqual(lspd(["validate"], self.tmp).code, 0)

    def test_cap_coverage(self) -> None:
        """DICT: CAP-COVERAGE"""
        self._seed()
        self.assertEqual(
            lspd(["coverage", "get"], self.tmp).envelope["result"]["coverage"]["fully_bound"],
            ["ENTITY", "INV", "ROUTE"],
        )
        self.assertEqual(lspd(["coverage", "fully-bound", "add", "SCREEN"], self.tmp).code, 0)
        self.assertEqual(lspd(["coverage", "fully-bound", "add", "API"], self.tmp).code, 1)
        self.assertEqual(lspd(["coverage", "fully-bound", "remove", "SCREEN"], self.tmp).code, 0)
        self.assertEqual(
            lspd(
                ["coverage", "curated", "set", "CAP", "--reason", "r", "--comment", "c"], self.tmp
            ).code,
            0,
        )
        self.assertEqual(
            lspd(["coverage", "curated", "set", "CAP", "--reason", "r2"], self.tmp).code, 0
        )
        self.assertEqual(lspd(["coverage", "curated", "unset", "CAP"], self.tmp).code, 0)
        self.assertEqual(lspd(["coverage", "curated", "unset", "CAP"], self.tmp).code, 1)
        self.assertEqual(lspd(["coverage"], self.tmp).envelope["error"]["code"], "ERR-USAGE")
        self.assertEqual(lspd(["validate"], self.tmp).code, 0)

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
        for argv in (
            ["--help"],
            ["init", "--help"],
            ["validate", "--help"],
            ["schema", "--help"],
            ["get", "--help"],
            ["list", "--help"],
            ["set", "--help"],
            ["add-locator", "--help"],
            ["add-field", "--help"],
            ["add-assertion", "--help"],
            ["remove", "--help"],
            ["coverage", "--help"],
            ["coverage", "get", "--help"],
            ["coverage", "fully-bound", "--help"],
            ["coverage", "fully-bound", "add", "--help"],
            ["coverage", "curated", "--help"],
            ["coverage", "curated", "set", "--help"],
        ):
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
        for element in (("init",), ("validate",), ("schema",), ("get", "ENTITY-A"), ("list",)):
            self.assertIn(element, positional, element)
        self.assertTrue(any(argv == ["schema", "--checksum"] for argv in argvs))
        self.assertTrue(any(argv[:2] == ["list", "--kind"] for argv in argvs))
        self.assertTrue(any(argv == ["list", "--full"] for argv in argvs))
        heads = {tuple(argv[:1]) for argv in argvs} | {tuple(argv[:2]) for argv in argvs}
        for head in (
            ("set",),
            ("add-locator",),
            ("add-field",),
            ("add-assertion",),
            ("remove",),
            ("coverage", "get"),
            ("coverage", "fully-bound"),
            ("coverage", "curated"),
        ):
            self.assertIn(head, heads, head)
        flags = {(argv[0], flag) for argv in argvs for flag in argv[1:] if flag.startswith("--")}
        for pair in (
            ("add-locator", "--symbol"),
            ("add-locator", "--role"),
            ("add-locator", "--comment"),
            ("add-field", "--symbol"),
            ("add-field", "--comment"),
            ("add-assertion", "--owed"),
            ("add-assertion", "--arm"),
            ("add-assertion", "--comment"),
            ("remove", "--locator"),
            ("remove", "--field"),
            ("remove", "--assertion"),
            ("remove", "--arm"),
            ("coverage", "--comment"),
        ):
            self.assertIn(pair, flags, pair)
        self.assertTrue(any(argv == ["--help"] for argv in argvs))
        self.assertTrue(any(argv == ["--version"] for argv in argvs))
        flat = {a for argv in argvs for a in argv}
        for option in ("--file", "--human", "--check-paths", "--no-size-limit", "--debug"):
            self.assertIn(option, flat)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
