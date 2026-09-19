"""COMPONENT-EMITTER — the only producer of file bytes.

Serialises a Map to the canonical layout of Domain & Data's *Persistence*
section, byte for byte, and performs the atomic replace
(PATTERN-ATOMIC-REPLACE).

DICT: COMPONENT-EMITTER
"""

from __future__ import annotations

import os
import re
import stat
import tempfile

from dbind.errors import FileIOError
from dbind.model import Assertion, Binding, Coverage, FieldLocator, Locator, Map

_INDICATORS = set("-?:,[]{}#&*!|>'\"%@`")
_FLOW_CHARS = set(",[]{}#:")
_CORE_NON_STRING = re.compile(
    r"^(?:true|True|TRUE|false|False|FALSE|null|Null|NULL|~"
    r"|[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+"
    r"|[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?"
    r"|[-+]?(?:\.inf|\.Inf|\.INF)|\.nan|\.NaN|\.NAN)$"
)


def needs_quotes(value: str) -> bool:
    """The closed quoting-trigger set of the canonical layout."""
    if value == "":
        return True
    if " " in value:
        return True
    if any(ch in _FLOW_CHARS for ch in value):
        return True
    first = value[0]
    if first in _INDICATORS:
        return True
    if _CORE_NON_STRING.match(value):
        return True
    # a leading "-" (digit or not) is already caught above: "-" is a YAML c-indicator
    return first.isdigit() or first in "._+"


def scalar(value: str) -> str:
    if not needs_quotes(value):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _comment_block(text: str, column: int) -> list[str]:
    pad = " " * column
    return [f"{pad}# {line}" if line != "" else f"{pad}#" for line in text.split("\n")]


def _entry_lines(flow: str, comment: str | None, column: int) -> list[str]:
    """A flow-style entry line with its comment as trailing (single-line) or block above."""
    pad = " " * column
    if comment is None:
        return [f"{pad}{flow}"]
    if "\n" in comment:
        return _comment_block(comment, column) + [f"{pad}{flow}"]
    return [f"{pad}{flow} # {comment}"]


def _flow(pairs: list[tuple[str, str | None]]) -> str:
    inner = ", ".join(f"{k}: {scalar(v)}" for k, v in pairs if v is not None)
    return "{ " + inner + " }"


def _locator_flow(loc: Locator) -> str:
    return _flow([("path", loc.path), ("symbol", loc.symbol), ("role", loc.role)])


def _field_flow(name: str, fl: FieldLocator) -> str:
    return f"{scalar(name)}: " + _flow([("path", fl.path), ("symbol", fl.symbol)])


def _assertion_flow(a: Assertion) -> str:
    return _flow(
        [("path", a.path), ("symbol", a.symbol), ("run", a.run), ("arm", a.arm), ("owed", a.owed)]
    )


def _binding_lines(b: Binding) -> list[str]:
    lines: list[str] = []
    if b.comment is not None:
        lines += _comment_block(b.comment, 2)
    lines.append(f"  {b.id}:")
    if b.locators:
        lines.append("    locators:")
        for loc in b.locators:
            lines += _entry_lines("- " + _locator_flow(loc), loc.comment, 6)
    else:
        lines.append("    locators: []")
    if b.compare_via is not None:
        lines.append(f"    compare_via: {scalar(b.compare_via)}")
    if b.fields is not None:
        lines.append("    fields:")
        for name, fl in b.fields.items():
            lines += _entry_lines(_field_flow(name, fl), fl.comment, 6)
    if b.wire is not None:
        lines.append("    wire:")
        for key, val in (
            ("casing", b.wire.casing),
            ("enums", b.wire.enums),
            ("dates", b.wire.dates),
        ):
            if val is not None:
                lines.append(f"      {key}: {scalar(val)}")
    if b.asserted_by is not None:
        lines.append("    asserted_by:")
        for a in b.asserted_by:
            lines += _entry_lines("- " + _assertion_flow(a), a.comment, 6)
    return lines


def _coverage_lines(cov: Coverage) -> list[str]:
    lines: list[str] = []
    if cov.comment is not None:
        lines += _comment_block(cov.comment, 0)
    lines.append("coverage:")
    if cov.fully_bound is not None:
        lines.append("  fully_bound: [" + ", ".join(cov.fully_bound) + "]")
    if cov.curated is not None:
        lines.append("  curated:")
        for kind, entry in cov.curated.items():
            if entry.comment is not None:
                lines += _comment_block(entry.comment, 4)
            lines.append(f"    {kind}: {scalar(entry.reason)}")
    return lines


def emit(m: Map) -> bytes:
    """The canonical bytes of ``m``. DICT: INV-CANONICAL-FIXPOINT"""
    lines: list[str] = []
    if m.header_comment is not None:
        lines += _comment_block(m.header_comment, 0)
    lines.append(f"schema_version: {m.schema_version}")
    lines.append("")
    if m.bindings:
        lines.append("bindings:")
        for b in m.bindings.values():
            lines.append("")
            lines += _binding_lines(b)
    else:
        lines.append("bindings: {}")
    if m.coverage is not None:
        lines.append("")
        lines += _coverage_lines(m.coverage)
    return ("\n".join(lines) + "\n").encode("utf-8")


def _umask() -> int:
    current = os.umask(0)
    os.umask(current)
    return current


def write(m: Map, target: str, *, create: bool = False) -> bytes:
    """Atomically replace (or create) the resolved ``target`` with ``emit(m)``.

    DICT: PATTERN-ATOMIC-REPLACE
    """
    data = emit(m)
    directory = os.path.dirname(target) or "."
    name = os.path.basename(target)
    fd = -1
    tmp: str | None = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=f"{name}.", suffix=".tmp", dir=directory)
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if create:
            os.chmod(tmp, 0o666 & ~_umask())
        else:
            os.chmod(tmp, stat.S_IMODE(os.stat(target).st_mode))
        os.replace(tmp, target)
        tmp = None
    except OSError as exc:
        raise FileIOError(target, f"{exc.strerror or exc}") from exc
    finally:
        if fd != -1:  # pragma: no cover — only reached if fdopen itself fails
            os.close(fd)
        if tmp is not None and os.path.exists(tmp):
            os.remove(tmp)
    return data
