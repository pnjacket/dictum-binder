"""COMPONENT-LOADER — file bytes to Model, comments included.

Resolves the target (SEC-SYMLINK-FINAL-TARGET), enforces the size cap
(SEC-FAIL-CLOSED), checks the byte layer, parses with ruamel.yaml's
round-trip loader (imported lazily, the only importer in the package),
converts through the Model's own checks, and attaches every comment to
its anchor by line adjacency in the source bytes.

DICT: COMPONENT-LOADER
"""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping
from typing import Any

from dbind.errors import FileIOError, FileMissingError, FileTooLargeError, ParseError
from dbind.model import Anchor, Finding, Map, from_plain

SIZE_CAP = 10 * 1024 * 1024
_BOM = b"\xef\xbb\xbf"


def resolve_target(path: str) -> str:
    return os.path.realpath(path)


def read_bytes(target: str, *, size_limit: bool = True) -> bytes:
    """Resolve, stat, cap and read the target. Raises the file-access ERR-* codes."""
    try:
        st = os.stat(target)
    except FileNotFoundError as exc:
        raise FileMissingError(target, "no such file") from exc
    except OSError as exc:
        raise FileIOError(target, exc.strerror or str(exc)) from exc
    if stat.S_ISDIR(st.st_mode):
        raise FileIOError(target, "is a directory")
    if size_limit and st.st_size > SIZE_CAP:
        raise FileTooLargeError(target, st.st_size, SIZE_CAP)
    try:
        with open(target, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise FileIOError(target, exc.strerror or str(exc)) from exc


def decode(target: str, data: bytes) -> tuple[str, list[Finding]]:
    """The byte layer: unloadable forms are ERR-PARSE, loadable deviations INV-BYTES warnings."""
    if data.startswith(_BOM):
        raise ParseError(target, "file starts with a UTF-8 BOM")
    if b"\r" in data:
        raise ParseError(target, "file contains CR (CRLF line endings)")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ParseError(
            target, f"file is not valid UTF-8 ({exc.reason} at byte {exc.start})"
        ) from exc
    problems: list[str] = []
    trailing = [i + 1 for i, line in enumerate(text.split("\n")) if line != line.rstrip(" \t")]
    if trailing:
        problems.append("trailing whitespace on line(s) " + ", ".join(str(n) for n in trailing))
    if not text.endswith("\n"):
        problems.append("no newline at end of file")
    elif text.endswith("\n\n"):
        problems.append("blank line(s) at end of file")
    findings: list[Finding] = []
    if problems:
        findings.append(
            Finding(
                "INV-BYTES",
                "warning",
                Anchor("file"),
                "; ".join(problems) + " (repaired by any write)",
            )
        )
    return text, findings


def _line_of(container: Any, key: Any) -> int | None:
    lc = getattr(container, "lc", None)
    if lc is None:
        return None
    try:
        if isinstance(container, Mapping):
            return int(lc.key(key)[0]) + 1
        return int(lc.item(key)[0]) + 1
    except (KeyError, IndexError, AttributeError, TypeError):
        return None


def parse(
    target: str, text: str
) -> tuple[Any, list[tuple[int, int, int, int]], set[int], int | None]:
    """Parse with ruamel.yaml (lazy import). Returns (data, scalar spans, transparent lines, first
    content line).
    """
    from ruamel.yaml import YAML  # the only third-party import in the package
    from ruamel.yaml.error import YAMLError
    from ruamel.yaml.tokens import (
        DirectiveToken,
        DocumentStartToken,
        ScalarToken,
        StreamEndToken,
        StreamStartToken,
    )

    yaml = YAML(typ="rt")
    spans: list[tuple[int, int, int, int]] = []
    transparent: set[int] = set()
    first_content: int | None = None
    try:
        for tok in yaml.scan(text):
            if isinstance(tok, ScalarToken):
                spans.append(
                    (
                        tok.start_mark.line + 1,
                        tok.start_mark.column,
                        tok.end_mark.line + 1,
                        tok.end_mark.column,
                    )
                )
            if isinstance(tok, (DocumentStartToken, DirectiveToken)):
                transparent.add(tok.start_mark.line + 1)
            elif not isinstance(tok, (StreamStartToken, StreamEndToken)) and first_content is None:
                first_content = tok.start_mark.line + 1
        data = yaml.load(text)
    except YAMLError as exc:
        raise ParseError(target, _yaml_reason(exc)) from exc
    if data is None:
        raise ParseError(target, "empty document")
    if not isinstance(data, Mapping):
        raise ParseError(target, "top level is not a mapping")
    return data, spans, transparent, first_content


def _yaml_reason(exc: Exception) -> str:
    name = type(exc).__name__
    if name == "DuplicateKeyError":
        return "duplicate key"
    first = str(exc).strip().split("\n", 1)[0]
    return f"{name}: {first}" if first else name


# --- comments ----------------------------------------------------------------


def _in_scalar(line: int, col: int, spans: list[tuple[int, int, int, int]]) -> bool:
    for sl, sc, el, ec in spans:
        if (sl, sc) <= (line, col) < (el, ec):
            return True
    return False


def find_comments(
    text: str, spans: list[tuple[int, int, int, int]]
) -> tuple[dict[int, str], dict[int, str]]:
    """Comments by line: (full-line comments, trailing comments), raw text from the ``#``."""
    full: dict[int, str] = {}
    trailing: dict[int, str] = {}
    for index, raw in enumerate(text.split("\n")):
        line = index + 1
        col = raw.find("#")
        while col != -1:
            if (col == 0 or raw[col - 1] in " \t") and not _in_scalar(line, col, spans):
                if raw[:col].strip() == "":
                    full[line] = raw[col:]
                else:
                    trailing[line] = raw[col:]
                break
            col = raw.find("#", col + 1)
    return full, trailing


def _strip_leader(raw: str) -> str:
    body = raw[1:]
    if body.startswith(" "):
        body = body[1:]
    return body


class _Anchors:
    """Line → anchor tables built from the Model's recorded source lines."""

    def __init__(self, m: Map) -> None:
        self.start: dict[int, tuple[Any, Anchor]] = {}
        self.end: dict[int, tuple[Any, Anchor]] = {}
        self.inner: set[int] = set()
        for b in m.bindings.values():
            self._add(b, Anchor("binding", id=b.id), b.line, b.line)
            for loc in b.locators:
                self._add(
                    loc,
                    Anchor("locator", id=b.id, path=loc.path, symbol=loc.symbol),
                    loc.line,
                    loc.end_line,
                )
            for name, fl in (b.fields or {}).items():
                self._add(fl, Anchor("field", id=b.id, field=name), fl.line, fl.end_line)
            for a in b.asserted_by or []:
                self._add(
                    a,
                    Anchor(
                        "assertion", id=b.id, path=a.path, symbol=a.symbol, arm=a.arm, owed=a.owed
                    ),
                    a.line,
                    a.end_line,
                )
        if m.coverage is not None:
            self._add(m.coverage, Anchor("coverage"), m.coverage.line, m.coverage.line)
            for kind, entry in (m.coverage.curated or {}).items():
                self._add(entry, Anchor("curated", kind=kind), entry.line, entry.line)

    def _add(self, obj: Any, anchor: Anchor, start: int | None, end: int | None) -> None:
        if start is None:
            return
        self.start[start] = (obj, anchor)
        last = end if end is not None else start
        self.end[last] = (obj, anchor)
        for inner in range(start + 1, last):
            self.inner.add(inner)


def attach_comments(
    m: Map,
    text: str,
    target: str,
    spans: list[tuple[int, int, int, int]],
    transparent: set[int],
    first_content: int | None,
) -> list[Finding]:
    """Attach every comment to its anchor by line adjacency; unattachable → ERR-PARSE."""
    full, trailing = find_comments(text, spans)
    anchors = _Anchors(m)
    findings: list[Finding] = []
    carriers: dict[int, list[tuple[str, str]]] = {}  # id(obj) -> [(form, text)]
    objects: dict[int, tuple[Any, Anchor]] = {}

    def record(obj: Any, anchor: Anchor, form: str, body: str, line: int) -> None:
        objects[id(obj)] = (obj, anchor)
        carriers.setdefault(id(obj), []).append((form, body))
        stripped = body.rstrip(" \t")
        if stripped != body:
            findings.append(
                Finding(
                    "INV-COMMENT-TEXT",
                    "warning",
                    anchor,
                    f"comment on line {line} has trailing whitespace (repaired by any write)",
                    line,
                )
            )

    for line, raw in sorted(trailing.items()):
        hit = anchors.end.get(line)
        if hit is None:
            raise ParseError(
                target,
                f"comment on line {line} has no anchor (a trailing comment on a non-anchor line)",
            )
        record(hit[0], hit[1], "trailing", _strip_leader(raw), line)

    header_lines: list[int] = []
    lines_sorted = sorted(full)
    index = 0
    while index < len(lines_sorted):
        block = [lines_sorted[index]]
        while index + 1 < len(lines_sorted) and lines_sorted[index + 1] == block[-1] + 1:
            index += 1
            block.append(lines_sorted[index])
        index += 1
        nxt = block[-1] + 1
        while nxt in transparent:
            nxt += 1
        body = "\n".join(_strip_leader(full[ln]) for ln in block)
        if (
            first_content is not None
            and nxt == first_content
            and m.header_comment is None
            and not header_lines
        ):
            header_lines = block
            m.header_comment = (
                body.rstrip(" \t")
                if "\n" not in body
                else "\n".join(s.rstrip(" \t") for s in body.split("\n"))
            )
            if any(full[ln] != full[ln].rstrip(" \t") for ln in block):
                findings.append(
                    Finding(
                        "INV-COMMENT-TEXT",
                        "warning",
                        Anchor("header"),
                        "header comment has trailing whitespace (repaired by any write)",
                        block[0],
                    )
                )
            continue
        hit = anchors.start.get(nxt)
        if hit is None:
            raise ParseError(
                target,
                f"comment block ending on line {block[-1]} has no anchor (no entry starts on line "
                f"{nxt})",
            )
        record(hit[0], hit[1], "block", body, block[0])

    for key, forms in carriers.items():
        obj, anchor = objects[key]
        texts = {form: "\n".join(s.rstrip(" \t") for s in body.split("\n")) for form, body in forms}
        if len(forms) > 1:
            findings.append(
                Finding(
                    "INV-COMMENT-ANCHORED",
                    "error",
                    anchor,
                    "two comment carriers on one anchor (a block above and a trailing comment); "
                    "delete one by hand",
                    obj.line,
                )
            )
            chosen = texts.get("block", texts.get("trailing", ""))
        else:
            chosen = texts[forms[0][0]]
        obj.comment = chosen
    return findings


def load(path: str, *, size_limit: bool = True) -> tuple[Map, list[Finding]]:
    """Load ``path`` into a Map plus the findings the Loader itself raises."""
    target = resolve_target(path)
    data = read_bytes(target, size_limit=size_limit)
    text, findings = decode(target, data)
    plain, spans, transparent, first_content = parse(target, text)
    m, model_findings = from_plain(plain, _line_of)
    findings.extend(model_findings)
    findings.extend(attach_comments(m, text, target, spans, transparent, first_content))
    return m, findings


__all__ = ["SIZE_CAP", "load", "resolve_target", "read_bytes", "decode", "parse", "attach_comments"]
