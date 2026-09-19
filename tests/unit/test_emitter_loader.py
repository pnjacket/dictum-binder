"""Emitter bytes (quoting, layout, atomic write) and Loader edges (bytes, parse, carriers)."""

from __future__ import annotations

import os
import stat
import unittest
from unittest import mock

from lspd import emitter, loader
from lspd.errors import FileIOError, FileMissingError, FileTooLargeError, ParseError
from lspd.model import Assertion, Binding, Coverage, CuratedEntry, FieldLocator, Locator, Map, Wire
from tests._helpers import TempDir, fixture, read_bytes


class Quoting(unittest.TestCase):
    """The closed quoting-trigger set of Domain's layout rules."""

    def test_plain_and_quoted_cases(self) -> None:
        plain = [
            "User",
            "src/models/user.py",
            "camelCase",
            "iso-8601-utc",
            "slice-9",
            "b",
            "User.email",
            "abc-1",
            "x=y",
            "a'b",
        ]
        quoted = [
            "",
            "-1",
            "-1x",
            "has space",
            "a,b",
            "a[b",
            "a]b",
            "a{b",
            "a}b",
            "a#b",
            "a:b",
            "-lead",
            "?q",
            ":c",
            "&anchor",
            "*alias",
            "!tag",
            "|lit",
            ">fold",
            "'sq",
            '"dq',
            "%pct",
            "@at",
            "`bt",
            "true",
            "False",
            "null",
            "~",
            "42",
            "0x1F",
            "1e3",
            ".inf",
            ".nan",
            "2026-09-18",
            "1_000",
            "0b101",
            "-1x",
            ".hidden",
            "+plus",
            "_under",
        ]
        for value in plain:
            with self.subTest(value=value):
                self.assertEqual(emitter.scalar(value), value)
        for value in quoted:
            with self.subTest(value=value):
                self.assertEqual(
                    emitter.scalar(value),
                    '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"',
                )
        self.assertEqual(emitter.scalar('a"b\\c d'), '"a\\"b\\\\c d"')


class Layout(unittest.TestCase):
    def test_empty_map_bytes(self) -> None:
        self.assertEqual(
            emitter.emit(Map(schema_version=1)), b"schema_version: 1\n\nbindings: {}\n"
        )

    def test_empty_bindings_with_coverage(self) -> None:
        m = Map(schema_version=1, coverage=Coverage(fully_bound=["A"]))
        self.assertEqual(
            emitter.emit(m), b"schema_version: 1\n\nbindings: {}\n\ncoverage:\n  fully_bound: [A]\n"
        )

    def test_every_construct_and_comment_carrier(self) -> None:
        b = Binding(
            "ENTITY-A",
            locators=[
                Locator("a.py", "A", "producer", comment="one"),
                Locator("b.py", comment="two\nlines"),
            ],
            compare_via="openapi",
            fields={"my field": FieldLocator("a.py", "A.f", comment="fc")},
            wire=Wire(casing="camelCase", dates="iso-8601-utc"),
            asserted_by=[
                Assertion("t.py", "t x", "run it", arm="a", comment="ac"),
                Assertion(owed="s9"),
            ],
            comment="binding\ncomment",
        )
        m = Map(
            schema_version=1,
            bindings={"ENTITY-A": b, "SCREEN-STUB": Binding("SCREEN-STUB")},
            coverage=Coverage(
                fully_bound=["ENTITY", "INV"],
                curated={"API": CuratedEntry("why", comment="cc")},
                comment="cov",
            ),
            header_comment="h1\n\nh3",
        )
        expected = (
            "# h1\n#\n# h3\nschema_version: 1\n\nbindings:\n\n  # binding\n  # comment\n"
            "  ENTITY-A:\n    locators:\n"
            "      - { path: a.py, symbol: A, role: producer } # one\n      # two\n      # lines\n"
            "      - { path: b.py }\n"
            "    compare_via: openapi\n    fields:\n"
            '      "my field": { path: a.py, symbol: A.f } # fc\n'
            "    wire:\n      casing: camelCase\n      dates: iso-8601-utc\n    asserted_by:\n"
            '      - { path: t.py, symbol: "t x", run: "run it", arm: a } # ac\n'
            "      - { owed: s9 }\n\n"
            "  SCREEN-STUB:\n    locators: []\n\n# cov\ncoverage:\n  fully_bound: [ENTITY, INV]\n"
            "  curated:\n    # cc\n    API: why\n"
        )
        self.assertEqual(emitter.emit(m).decode("utf-8"), expected)


class AtomicWrite(unittest.TestCase):
    """DICT: INV-ATOMIC-WRITE / PATTERN-ATOMIC-REPLACE"""

    def test_create_sets_umask_mode_and_replace_keeps_mode(self) -> None:
        with TempDir() as tmp:
            target = os.path.join(tmp, "bindings.yaml")
            old = os.umask(0o027)
            try:
                emitter.write(Map(schema_version=1), target, create=True)
            finally:
                os.umask(old)
            self.assertEqual(stat.S_IMODE(os.stat(target).st_mode), 0o640)
            os.chmod(target, 0o600)
            emitter.write(Map(schema_version=1, coverage=Coverage(fully_bound=["A"])), target)
            self.assertEqual(stat.S_IMODE(os.stat(target).st_mode), 0o600)
            self.assertIn(b"coverage", read_bytes(target))
            self.assertEqual([n for n in os.listdir(tmp) if n.endswith(".tmp")], [])

    def test_failed_rename_leaves_target_and_no_temp_file(self) -> None:
        with TempDir() as tmp:
            target = os.path.join(tmp, "bindings.yaml")
            emitter.write(Map(schema_version=1), target, create=True)
            before = read_bytes(target)
            with mock.patch(
                "lspd.emitter.os.replace", side_effect=OSError(13, "Permission denied")
            ):
                with self.assertRaises(FileIOError):
                    emitter.write(
                        Map(schema_version=1, coverage=Coverage(fully_bound=["A"])), target
                    )
            self.assertEqual(read_bytes(target), before)
            self.assertEqual([n for n in os.listdir(tmp) if n.endswith(".tmp")], [])

    def test_unwritable_directory_is_io_error(self) -> None:
        with TempDir() as tmp:
            with self.assertRaises(FileIOError):
                emitter.write(
                    Map(schema_version=1),
                    os.path.join(tmp, "missing-dir", "bindings.yaml"),
                    create=True,
                )


class LoaderEdges(unittest.TestCase):
    def test_file_access_errors(self) -> None:
        with TempDir() as tmp:
            with self.assertRaises(FileMissingError):
                loader.load(os.path.join(tmp, "nope.yaml"))
            os.mkdir(os.path.join(tmp, "bindings.yaml"))
            with self.assertRaises(FileIOError):
                loader.load(os.path.join(tmp, "bindings.yaml"))
            with mock.patch(
                "lspd.loader.os.stat", side_effect=PermissionError(13, "Permission denied")
            ):
                with self.assertRaises(FileIOError):
                    loader.load(os.path.join(tmp, "other.yaml"))
            big = os.path.join(tmp, "big.yaml")
            with open(big, "wb") as handle:
                handle.write(b"x" * 65)
            with mock.patch("lspd.loader.SIZE_CAP", 64):
                with self.assertRaises(FileTooLargeError):
                    loader.load(big)
                with self.assertRaises(ParseError):
                    loader.load(big, size_limit=False)
            with mock.patch("builtins.open", side_effect=PermissionError(13, "Permission denied")):
                with self.assertRaises(FileIOError):
                    loader.read_bytes(fixture("canonical.yaml"))

    def test_byte_layer(self) -> None:
        for data, reason in (
            (b"\xef\xbb\xbfschema_version: 1\n", "BOM"),
            (b"schema_version: 1\r\n", "CR"),
            (b"\xff\xfe", "UTF-8"),
        ):
            with self.subTest(reason=reason):
                with self.assertRaises(ParseError) as ctx:
                    loader.decode("t", data)
                self.assertIn(reason, ctx.exception.message)
        text, findings = loader.decode("t", b"schema_version: 1  \n\nbindings: {}\n\n")
        self.assertEqual([f.code for f in findings], ["INV-BYTES"])
        self.assertIn("line(s) 1", findings[0].message)
        self.assertIn("blank line(s) at end", findings[0].message)
        self.assertEqual(loader.decode("t", b"schema_version: 1\n\nbindings: {}\n")[1], [])

    def test_parse_errors(self) -> None:
        for name in (
            "err-parse-duplicate-key",
            "err-parse-syntax",
            "err-parse-not-mapping",
            "err-parse-empty",
            "err-parse-no-anchor-trailing",
            "err-parse-no-anchor-block",
        ):
            with self.subTest(fixture=name):
                with self.assertRaises(ParseError):
                    loader.load(fixture(f"{name}.yaml"))

    def test_carriers_round_trip_and_transparent_markers(self) -> None:
        m, findings = loader.load(fixture("carriers.yaml"))
        self.assertEqual(findings, [])
        self.assertEqual(m.header_comment, "header line one\nheader line two")
        b = m.bindings["ENTITY-A"]
        self.assertEqual(b.comment, "binding block\nsecond line")
        self.assertEqual(
            [loc.comment for loc in b.locators],
            ["trailing locator", "block above locator\ntwo lines"],
        )
        assert b.fields is not None and b.asserted_by is not None
        self.assertEqual(b.fields["name"].comment, "trailing field")
        self.assertEqual(b.asserted_by[0].comment, "trailing assertion")
        self.assertEqual(
            m.bindings["ENTITY-B"].comment, "trailing on the anchor line, read as a block"
        )
        assert m.coverage is not None and m.coverage.curated is not None
        self.assertEqual(m.coverage.comment, "coverage block")
        self.assertEqual(m.coverage.curated["API"].comment, "curated block")
        self.assertEqual(
            emitter.emit(m),
            read_bytes(fixture("carriers.yaml")).replace(
                b"  ENTITY-B: # trailing on the anchor line, read as a block\n",
                b"  # trailing on the anchor line, read as a block\n  ENTITY-B:\n",
            ),
        )
        with TempDir() as tmp:
            path = os.path.join(tmp, "b.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("# h\n%YAML 1.2\n---\nschema_version: 1\n\nbindings: {}\n")
            m, _ = loader.load(path)
            self.assertEqual(m.header_comment, "h")

    def test_block_style_entries_and_inner_comments(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "b.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\nbindings:\n  ENTITY-A:\n    locators:\n"
                    "      - path: a.py\n        symbol: A # last line\n"
                )
            m, _ = loader.load(path)
            self.assertEqual(m.bindings["ENTITY-A"].locators[0].comment, "last line")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\nbindings:\n  ENTITY-A:\n    locators:\n"
                    "      - path: a.py # inner\n        symbol: A\n"
                )
            with self.assertRaises(ParseError):
                loader.load(path)

    def test_leader_stripping_and_trailing_whitespace_in_comments(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "b.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "#  two spaces\n#text\nschema_version: 1\n\nbindings:\n\n  ENTITY-A: # tail \n"
                    "    locators: []\n"
                )
            m, findings = loader.load(path)
            self.assertEqual(m.header_comment, " two spaces\ntext")
            self.assertEqual(m.bindings["ENTITY-A"].comment, "tail")
            self.assertEqual(sorted(f.code for f in findings), ["INV-BYTES", "INV-COMMENT-TEXT"])
            self.assertTrue(all(f.severity == "warning" for f in findings))
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("# head \nschema_version: 1\n\nbindings: {}\n")
            m, findings = loader.load(path)
            self.assertEqual(m.header_comment, "head")
            self.assertEqual({f.code for f in findings}, {"INV-BYTES", "INV-COMMENT-TEXT"})

    def test_quoted_hash_is_not_a_comment(self) -> None:
        with TempDir() as tmp:
            path = os.path.join(tmp, "b.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    "schema_version: 1\n\nbindings:\n\n  ENTITY-A:\n    locators:\n"
                    '      - { path: a.py, symbol: "x #y" }\n'
                )
            m, findings = loader.load(path)
            self.assertEqual(findings, [])
            self.assertEqual(m.bindings["ENTITY-A"].locators[0].symbol, "x #y")
            self.assertIsNone(m.bindings["ENTITY-A"].locators[0].comment)


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
