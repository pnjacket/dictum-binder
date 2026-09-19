"""Contract tier for the slice-4 elements: comment get / set / unset at each of the seven
anchors, the anchor grammar (ERR-USAGE), the value rule (ERR-INPUT-INVALID), ERR-NOT-FOUND's
`comment get` forcing, and the set-with-comments round trip that closes CLI-SET's owed proof."""

from __future__ import annotations

import json
import unittest
from typing import Any

from dbind import emitter, loader
from tests._helpers import TempDir, copy_fixture, read_bytes, run_cli

CANON = "canonical.yaml"

ANCHORS: list[tuple[list[str], dict[str, Any]]] = [
    (["header"], {"type": "header"}),
    (["binding", "ROUTE-HOME"], {"type": "binding", "id": "ROUTE-HOME"}),
    (
        ["locator", "ENTITY-USER", "--path", "db/schema.sql", "--symbol", "users"],
        {"type": "locator", "id": "ENTITY-USER", "path": "db/schema.sql", "symbol": "users"},
    ),
    (["field", "ENTITY-USER", "email"], {"type": "field", "id": "ENTITY-USER", "field": "email"}),
    (
        ["assertion", "ENTITY-USER", "--owed", "slice-9", "--arm", "c"],
        {"type": "assertion", "id": "ENTITY-USER", "owed": "slice-9", "arm": "c"},
    ),
    (
        [
            "assertion",
            "ENTITY-USER",
            "--path",
            "tests/test_user.py",
            "--symbol",
            "test_email_case",
            "--arm",
            "b",
        ],
        {
            "type": "assertion",
            "id": "ENTITY-USER",
            "path": "tests/test_user.py",
            "symbol": "test_email_case",
            "arm": "b",
        },
    ),
    (["coverage"], {"type": "coverage"}),
    (["curated", "API"], {"type": "curated", "kind": "API"}),
]

FULL_ANCHOR_KEYS = ["type", "id", "path", "symbol", "arm", "owed", "field", "kind"]


def _full(partial: dict[str, Any]) -> dict[str, Any]:
    return {key: partial.get(key) for key in FULL_ANCHOR_KEYS}


class SevenAnchors(unittest.TestCase):
    """DICT: CLI-COMMENT-GET / CLI-COMMENT-SET / CLI-COMMENT-UNSET / OUT-COMMENT"""

    def test_set_get_unset_at_every_anchor_with_exact_bytes(self) -> None:
        for anchor, expected in ANCHORS:
            with self.subTest(anchor=anchor[0]), TempDir() as tmp:
                target = copy_fixture(CANON, tmp)
                for text in ("one line", "two\nlines"):
                    run = run_cli(["comment", "set", *anchor, "--text", text], cwd=tmp)
                    self.assertEqual(
                        (run.code, run.envelope["command"]), (0, "comment set"), run.stdout
                    )
                    self.assertEqual(
                        run.envelope["result"], {"anchor": _full(expected), "text": text}
                    )
                    m, findings = loader.load(target)
                    self.assertEqual(findings, [])
                    self.assertEqual(read_bytes(target), emitter.emit(m))
                    got = run_cli(["comment", "get", *anchor], cwd=tmp)
                    self.assertEqual((got.code, got.envelope["result"]["text"]), (0, text))
                    self.assertEqual(list(got.envelope["result"]), ["anchor", "text"])
                unset = run_cli(["comment", "unset", *anchor], cwd=tmp)
                self.assertEqual(unset.code, 0, unset.stdout)
                self.assertEqual(
                    unset.envelope["result"], {"anchor": _full(expected), "text": None}
                )
                again = run_cli(["comment", "unset", *anchor], cwd=tmp)
                self.assertEqual(again.envelope["error"]["code"], "ERR-NOT-FOUND")
                bare = run_cli(["comment", "get", *anchor], cwd=tmp)
                self.assertEqual((bare.code, bare.envelope["error"]["code"]), (1, "ERR-NOT-FOUND"))
                self.assertEqual(bare.envelope["error"]["details"]["anchor"], _full(expected))
                self.assertEqual(run_cli(["validate"], cwd=tmp).code, 0)

    def test_carrier_form_follows_the_text(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            anchor = ["locator", "ROUTE-HOME", "--path", "web/src/app.routes.ts"]
            run_cli(["comment", "set", *anchor, "--text", "block\nabove"], cwd=tmp)
            text = read_bytes(target).decode("utf-8")
            self.assertIn(
                "      # block\n      # above\n      - { path: web/src/app.routes.ts }\n", text
            )
            self.assertNotIn("# path-only locator is legal", text)
            run_cli(["comment", "set", *anchor, "--text", "trailing"], cwd=tmp)
            text = read_bytes(target).decode("utf-8")
            self.assertIn("      - { path: web/src/app.routes.ts } # trailing\n", text)
            self.assertNotIn("# block", text)
            run_cli(["comment", "set", "header", "--text", "h1\n\nh3"], cwd=tmp)
            self.assertTrue(read_bytes(target).startswith(b"# h1\n#\n# h3\nschema_version: 1\n"))

    def test_untouched_lines_keep_their_order(self) -> None:
        """DICT: INV-ORDER-PRESERVED (comment writes)"""
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = read_bytes(target).decode("utf-8").split("\n")
            run_cli(["comment", "set", "binding", "ROUTE-HOME", "--text", "new"], cwd=tmp)
            after = read_bytes(target).decode("utf-8").split("\n")
            self.assertEqual(len(after), len(before) + 1)
            self.assertEqual([ln for ln in after if ln != "  # new"], before)
            m, _ = loader.load(target)
            self.assertEqual(
                list(m.bindings), ["ENTITY-PROJECT", "ENTITY-USER", "ROUTE-HOME", "SCREEN-STUB"]
            )


class Conditions(unittest.TestCase):
    """DICT: ERR-NOT-FOUND (anchor arm) / ERR-INPUT-INVALID (comment set) / ERR-USAGE.

    The last one is the anchor grammar.
    """

    def test_absent_targets(self) -> None:
        with TempDir() as tmp:
            run_cli(["init"], cwd=tmp)
            for anchor in (
                ["binding", "ENTITY-NOPE"],
                ["coverage"],
                ["curated", "API"],
            ):
                run = run_cli(["comment", "set", *anchor, "--text", "t"], cwd=tmp)
                self.assertEqual(
                    (run.code, run.envelope["error"]["code"]), (1, "ERR-NOT-FOUND"), anchor
                )
            copy_fixture(CANON, tmp)
            for anchor in (
                ["locator", "ROUTE-HOME", "--path", "nope.ts"],
                ["field", "ENTITY-USER", "nope"],
                ["assertion", "ENTITY-USER", "--owed", "nope"],
                ["curated", "SEC"],
            ):
                run = run_cli(["comment", "get", *anchor], cwd=tmp)
                self.assertEqual(
                    (run.code, run.envelope["error"]["code"]), (1, "ERR-NOT-FOUND"), anchor
                )

    def test_value_rule_on_text(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = read_bytes(target)
            for text in ("abc ", "\nabc", "abc\n", "\n\n", "a\x01b", "a\tb"):
                run = run_cli(["comment", "set", "binding", "ROUTE-HOME", "--text", text], cwd=tmp)
                self.assertEqual(run.envelope["error"]["code"], "ERR-INPUT-INVALID", repr(text))
                self.assertEqual(
                    [f["code"] for f in run.envelope["error"]["details"]["findings"]],
                    ["INV-COMMENT-TEXT"],
                )
                self.assertEqual(read_bytes(target), before)
            empty = run_cli(["comment", "set", "binding", "ROUTE-HOME", "--text", ""], cwd=tmp)
            self.assertEqual(empty.envelope["error"]["code"], "ERR-USAGE")

    def test_anchor_grammar(self) -> None:
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            for argv in (
                ["comment"],
                ["comment", "get"],
                ["comment", "get", "bogus"],
                ["comment", "get", "header", "ENTITY-USER"],
                ["comment", "get", "coverage", "--path", "x"],
                ["comment", "get", "binding"],
                ["comment", "get", "binding", "entity-user"],
                ["comment", "get", "binding", "ENTITY-USER", "name"],
                ["comment", "get", "locator", "ENTITY-USER"],
                ["comment", "get", "locator", "ENTITY-USER", "--path", "x", "--owed", "y"],
                ["comment", "get", "field", "ENTITY-USER"],
                ["comment", "get", "field", "ENTITY-USER", "email", "--arm", "a"],
                ["comment", "get", "assertion", "ENTITY-USER", "--path", "x"],
                ["comment", "get", "assertion", "ENTITY-USER", "x"],
                ["comment", "get", "curated", "api"],
                ["comment", "get", "curated", "API", "--arm", "a"],
                ["comment", "set", "header"],
            ):
                run = run_cli(argv, cwd=tmp)
                self.assertEqual((run.code, run.envelope["error"]["code"]), (1, "ERR-USAGE"), argv)
                self.assertTrue(run.envelope["command"].startswith("comment"), argv)
            self.assertEqual(run_cli(["comment"], cwd=tmp).envelope["command"], "comment")

    def test_two_carrier_anchor_refuses_the_write(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture("inv-comment-anchored.yaml", tmp)
            before = read_bytes(target)
            ids = [
                r["id"] for r in json.loads(run_cli(["list"], cwd=tmp).stdout)["result"]["bindings"]
            ]
            run = run_cli(["comment", "set", "binding", ids[0], "--text", "t"], cwd=tmp)
            self.assertEqual(run.envelope["error"]["code"], "ERR-FILE-INVALID")
            self.assertEqual(read_bytes(target), before)


class SetRoundTrip(unittest.TestCase):
    """DICT: CLI-SET (comment clause) / SUCCESS-ROUNDTRIP — `set` with a `get` document is a
    byte-level no-op for every binding of the canonical fixture."""

    def test_get_document_set_back_is_identity(self) -> None:
        with TempDir() as tmp:
            target = copy_fixture(CANON, tmp)
            before = read_bytes(target)
            for row in run_cli(["list"], cwd=tmp).envelope["result"]["bindings"]:
                (doc,) = run_cli(["get", row["id"]], cwd=tmp).envelope["result"]["bindings"]
                run = run_cli(["set", row["id"], "--json", json.dumps(doc)], cwd=tmp)
                self.assertEqual(run.code, 0, run.stdout)
                self.assertEqual(run.envelope["result"]["binding"], doc)
                self.assertEqual(read_bytes(target), before, row["id"])

    def test_set_clears_and_sets_comments_at_every_binding_anchor(self) -> None:
        with TempDir() as tmp:
            copy_fixture(CANON, tmp)
            (doc,) = run_cli(["get", "ENTITY-USER"], cwd=tmp).envelope["result"]["bindings"]
            doc["comment"] = None
            doc["locators"][0]["comment"] = None
            doc["locators"][1]["comment"] = "now here"
            doc["fields"]["config"]["comment"] = None
            doc["asserted_by"][0]["comment"] = "bound\ncomment"
            self.assertEqual(
                run_cli(["set", "ENTITY-USER", "--json", json.dumps(doc)], cwd=tmp).code, 0
            )
            (back,) = run_cli(["get", "ENTITY-USER"], cwd=tmp).envelope["result"]["bindings"]
            self.assertEqual(back, doc)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
