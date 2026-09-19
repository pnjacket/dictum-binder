"""E2E journeys per capability, through the real installed binary (E2E-STANDARD)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from tests.e2e import _runner
from tests.e2e._runner import dbind

FIXTURES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")


class Journeys(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="dbind-e2e-")
        self.assertTrue(os.path.exists(_runner.DBIND), _runner.DBIND)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cap_init(self) -> None:
        """DICT: CAP-INIT"""
        run = dbind(["init"], self.tmp)
        self.assertEqual(run.code, 0, run.stdout)
        with open(os.path.join(self.tmp, "bindings.yaml"), "rb") as handle:
            self.assertEqual(handle.read(), b"schema_version: 1\n\nbindings: {}\n")
        self.assertEqual(dbind(["init"], self.tmp).envelope["error"]["code"], "ERR-FILE-EXISTS")
        self.assertEqual(dbind(["init", "--file", "other.yaml"], self.tmp).code, 0)
        self.assertEqual(dbind(["--human", "init", "--file", "third.yaml"], self.tmp).code, 0)
        self.assertEqual(dbind(["--debug", "init", "--file", "fourth.yaml"], self.tmp).stderr, "")

    def test_cap_validate_and_pathcheck(self) -> None:
        """DICT: CAP-VALIDATE / CAP-PATHCHECK"""
        shutil.copyfile(
            os.path.join(FIXTURES, "canonical.yaml"), os.path.join(self.tmp, "bindings.yaml")
        )
        run = dbind(["validate"], self.tmp)
        self.assertEqual(
            (run.code, run.envelope["result"]),
            (0, {"errors": 0, "warnings": 0, "paths_checked": False}),
        )
        self.assertEqual(dbind(["validate", "--no-size-limit"], self.tmp).code, 0)
        shutil.copyfile(
            os.path.join(FIXTURES, "inv-path-exists.yaml"), os.path.join(self.tmp, "bindings.yaml")
        )
        missing = dbind(["--check-paths", "validate"], self.tmp)
        self.assertEqual(
            (missing.code, missing.envelope["findings"]["pre"][0]["code"]), (1, "INV-PATH-EXISTS")
        )
        os.makedirs(os.path.join(self.tmp, "no", "such"))
        with open(os.path.join(self.tmp, "no", "such", "file.py"), "w", encoding="utf-8") as handle:
            handle.write("")
        self.assertEqual(dbind(["validate", "--check-paths"], self.tmp).code, 0)
        human = dbind(["validate", "--human"], self.tmp)
        self.assertEqual(human.code, 0)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(human.stdout)
        self.assertEqual(dbind(["validate", "--file", "nope.yaml"], self.tmp).code, 2)

    def test_cap_query(self) -> None:
        """DICT: CAP-QUERY"""
        shutil.copyfile(
            os.path.join(FIXTURES, "carriers.yaml"), os.path.join(self.tmp, "bindings.yaml")
        )
        got = dbind(["get", "ENTITY-A"], self.tmp)
        self.assertEqual(got.code, 0, got.stdout)
        (b,) = got.envelope["result"]["bindings"]
        self.assertEqual((b["id"], b["comment"]), ("ENTITY-A", "binding block\nsecond line"))
        listed = dbind(["list"], self.tmp)
        self.assertEqual(
            [r["id"] for r in listed.envelope["result"]["bindings"]], ["ENTITY-A", "ENTITY-B"]
        )
        self.assertEqual(dbind(["list", "--kind", "ENTITY"], self.tmp).code, 0)
        full = dbind(["list", "--full"], self.tmp)
        self.assertIn("locators", full.envelope["result"]["bindings"][0])
        missing = dbind(["get", "ENTITY-NOPE"], self.tmp)
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
        run = dbind(["set", "INV-X", "--json", doc], self.tmp)
        self.assertEqual(run.code, 0, run.stdout)
        self.assertEqual(run.envelope["result"]["binding"]["comment"], "b")
        text = open(target, encoding="utf-8").read()
        self.assertIn(
            "  # b\n  INV-X:\n    locators:\n      - { path: src/x.py, symbol: X } # c\n", text
        )
        self.assertEqual(dbind(["set", "INV-X", "--json", '{"locators": []}'], self.tmp).code, 0)
        self.assertEqual(dbind(["set", "INV-X", "--json", "nope"], self.tmp).code, 1)
        self.assertEqual(dbind(["validate"], self.tmp).code, 0)

    def test_cap_add(self) -> None:
        """DICT: CAP-ADD"""
        self._seed()
        loc = dbind(
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
            dbind(
                ["add-locator", "ROUTE-HOME", "--path", "web/h.ts", "--symbol", "H"], self.tmp
            ).envelope["error"]["code"],
            "ERR-DUPLICATE",
        )
        fld = dbind(
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
            dbind(["add-field", "ROUTE-HOME", "title", "--path", "web/h2.ts"], self.tmp).code, 0
        )
        bound = dbind(
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
            dbind(["add-assertion", "ROUTE-HOME", "--owed", "slice-4"], self.tmp).code, 0
        )
        self.assertEqual(
            dbind(["add-assertion", "ROUTE-HOME", "--path", "t.py"], self.tmp).envelope["error"][
                "code"
            ],
            "ERR-USAGE",
        )
        self.assertEqual(dbind(["add-locator", "ENTITY-NOPE", "--path", "x.py"], self.tmp).code, 1)
        self.assertEqual(dbind(["validate"], self.tmp).code, 0)

    def test_cap_remove(self) -> None:
        """DICT: CAP-REMOVE"""
        self._seed()
        self.assertEqual(dbind(["remove", "ENTITY-USER", "--field", "config"], self.tmp).code, 0)
        self.assertEqual(
            dbind(
                ["remove", "ENTITY-USER", "--assertion", "--owed", "slice-9", "--arm", "c"],
                self.tmp,
            ).code,
            0,
        )
        self.assertEqual(
            dbind(
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
        stub = dbind(
            ["remove", "ROUTE-HOME", "--locator", "--path", "web/src/app.routes.ts"], self.tmp
        )
        self.assertEqual(stub.envelope["result"]["binding"]["locators"], [])
        whole = dbind(["remove", "SCREEN-STUB"], self.tmp)
        self.assertEqual(whole.envelope["result"], {"binding": None, "removed": "SCREEN-STUB"})
        self.assertEqual(
            dbind(["remove", "SCREEN-STUB"], self.tmp).envelope["error"]["code"], "ERR-NOT-FOUND"
        )
        self.assertEqual(dbind(["validate"], self.tmp).code, 0)

    def test_cap_coverage(self) -> None:
        """DICT: CAP-COVERAGE"""
        self._seed()
        self.assertEqual(
            dbind(["coverage", "get"], self.tmp).envelope["result"]["coverage"]["fully_bound"],
            ["ENTITY", "INV", "ROUTE"],
        )
        self.assertEqual(dbind(["coverage", "fully-bound", "add", "SCREEN"], self.tmp).code, 0)
        self.assertEqual(dbind(["coverage", "fully-bound", "add", "API"], self.tmp).code, 1)
        self.assertEqual(dbind(["coverage", "fully-bound", "remove", "SCREEN"], self.tmp).code, 0)
        self.assertEqual(
            dbind(
                ["coverage", "curated", "set", "CAP", "--reason", "r", "--comment", "c"], self.tmp
            ).code,
            0,
        )
        self.assertEqual(
            dbind(["coverage", "curated", "set", "CAP", "--reason", "r2"], self.tmp).code, 0
        )
        self.assertEqual(dbind(["coverage", "curated", "unset", "CAP"], self.tmp).code, 0)
        self.assertEqual(dbind(["coverage", "curated", "unset", "CAP"], self.tmp).code, 1)
        self.assertEqual(dbind(["coverage"], self.tmp).envelope["error"]["code"], "ERR-USAGE")
        self.assertEqual(dbind(["validate"], self.tmp).code, 0)

    def test_cap_comment(self) -> None:
        """DICT: CAP-COMMENT — Quality's E2E example 3, bytes asserted at each step."""
        target = os.path.join(self.tmp, "bindings.yaml")
        self.assertEqual(dbind(["init"], self.tmp).code, 0)
        doc = '{"locators": [{"path": "src/x.py", "symbol": "X"}]}'
        self.assertEqual(dbind(["set", "ENTITY-X", "--json", doc], self.tmp).code, 0)
        base = (
            "schema_version: 1\n\nbindings:\n\n  ENTITY-X:\n    locators:\n"
            "      - { path: src/x.py, symbol: X }\n"
        )
        self.assertEqual(open(target, "rb").read(), base.encode("utf-8"))
        run = dbind(["comment", "set", "binding", "ENTITY-X", "--text", "why"], self.tmp)
        self.assertEqual(run.code, 0, run.stdout)
        self.assertEqual(
            open(target, "rb").read(),
            base.replace("  ENTITY-X:", "  # why\n  ENTITY-X:").encode("utf-8"),
        )
        got = dbind(["comment", "get", "binding", "ENTITY-X"], self.tmp)
        self.assertEqual((got.code, got.envelope["result"]["text"]), (0, "why"))
        self.assertEqual(
            dbind(
                [
                    "comment",
                    "set",
                    "locator",
                    "ENTITY-X",
                    "--path",
                    "src/x.py",
                    "--symbol",
                    "X",
                    "--text",
                    "l",
                ],
                self.tmp,
            ).code,
            0,
        )
        self.assertEqual(
            dbind(
                ["comment", "unset", "locator", "ENTITY-X", "--path", "src/x.py", "--symbol", "X"],
                self.tmp,
            ).code,
            0,
        )
        self.assertEqual(dbind(["comment", "unset", "binding", "ENTITY-X"], self.tmp).code, 0)
        self.assertEqual(open(target, "rb").read(), base.encode("utf-8"))
        missing = dbind(["comment", "get", "binding", "ENTITY-X"], self.tmp)
        self.assertEqual((missing.code, missing.envelope["error"]["code"]), (1, "ERR-NOT-FOUND"))
        self.assertEqual(dbind(["comment", "set", "header", "--text", "h"], self.tmp).code, 0)
        self.assertEqual(
            dbind(["comment", "set", "field", "ENTITY-X", "f", "--text", "t"], self.tmp).code, 1
        )
        self.assertEqual(
            dbind(
                [
                    "comment",
                    "set",
                    "assertion",
                    "ENTITY-X",
                    "--owed",
                    "s",
                    "--arm",
                    "a",
                    "--text",
                    "t",
                ],
                self.tmp,
            ).code,
            1,
        )
        self.assertEqual(dbind(["comment", "get", "coverage"], self.tmp).code, 1)
        self.assertEqual(dbind(["comment", "get", "curated", "API"], self.tmp).code, 1)
        self.assertEqual(dbind(["comment"], self.tmp).envelope["error"]["code"], "ERR-USAGE")
        self.assertEqual(dbind(["validate"], self.tmp).code, 0)

    def test_cap_format(self) -> None:
        """DICT: CAP-FORMAT"""
        target = os.path.join(self.tmp, "bindings.yaml")
        shutil.copyfile(os.path.join(FIXTURES, "noncanonical.yaml"), target)
        before = open(target, "rb").read()
        check = dbind(["format", "--check"], self.tmp)
        self.assertEqual(
            (check.code, check.envelope["result"]), (1, {"changed": True, "checked_only": True})
        )
        self.assertEqual(open(target, "rb").read(), before)
        run = dbind(["format"], self.tmp)
        self.assertEqual(
            (run.code, run.envelope["result"]), (0, {"changed": True, "checked_only": False})
        )
        self.assertEqual(
            open(target, "rb").read(),
            b"schema_version: 1\n\nbindings:\n\n  ENTITY-A:\n    locators:\n"
            b"      - { path: src/a.py, symbol: A }\n\n  ROUTE-B:\n    locators:\n"
            b"      - { path: web/b.ts, symbol: B }\n\ncoverage:\n  fully_bound: [ENTITY, ROUTE]\n",
        )
        self.assertEqual(dbind(["format", "--check"], self.tmp).code, 0)
        self.assertEqual(dbind(["format"], self.tmp).envelope["result"]["changed"], False)
        shutil.copyfile(os.path.join(FIXTURES, "inv-path-form.yaml"), target)
        self.assertEqual(dbind(["format"], self.tmp).envelope["error"]["code"], "ERR-FILE-INVALID")

    def test_cap_schema(self) -> None:
        """DICT: CAP-SCHEMA"""
        raw = dbind(["schema"], self.tmp)
        self.assertEqual(raw.code, 0)
        self.assertEqual(
            json.loads(raw.stdout)["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        checksum = dbind(["schema", "--checksum"], self.tmp)
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
            ["coverage", "curated", "--help"],
            ["comment", "--help"],
            ["comment", "set", "--help"],
            ["format", "--help"],
        ):
            run = dbind(argv, self.tmp)
            self.assertEqual(run.code, 0)
            self.assertTrue(run.stdout.startswith("usage: dbind"))
        self.assertRegex(dbind(["--version"], self.tmp).stdout, r"^dbind \S+\n$")
        bare = dbind([], self.tmp)
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
        for element in (
            ("init",),
            ("validate",),
            ("schema",),
            ("get", "ENTITY-A"),
            ("list",),
            ("format",),
        ):
            self.assertIn(element, positional, element)
        self.assertTrue(any(argv == ["schema", "--checksum"] for argv in argvs))
        self.assertTrue(any(argv == ["format", "--check"] for argv in argvs))
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
            ("comment", "get"),
            ("comment", "set"),
            ("comment", "unset"),
        ):
            self.assertIn(head, heads, head)
        anchors = {
            argv[2]
            for argv in argvs
            if argv[:1] == ["comment"] and len(argv) > 2 and not argv[2].startswith("--")
        }
        self.assertEqual(
            anchors,
            {"header", "binding", "locator", "field", "assertion", "coverage", "curated"},
        )
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
            ("comment", "--symbol"),
            ("comment", "--arm"),
        ):
            self.assertIn(pair, flags, pair)
        self.assertTrue(any(argv == ["--help"] for argv in argvs))
        self.assertTrue(any(argv == ["--version"] for argv in argvs))
        flat = {a for argv in argvs for a in argv}
        for option in ("--file", "--human", "--check-paths", "--no-size-limit", "--debug"):
            self.assertIn(option, flat)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
