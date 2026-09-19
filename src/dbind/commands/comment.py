"""CLI-COMMENT-GET / CLI-COMMENT-SET / CLI-COMMENT-UNSET — the comment at one anchor.

DICT: CLI-COMMENT-GET
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dbind.errors import NotFoundError
from dbind.model import Anchor, Map


@dataclass
class Target:
    """The object that carries the comment for an anchor, and the attribute holding it."""

    anchor: Anchor
    obj: Any
    attr: str = "comment"

    @property
    def text(self) -> str | None:
        return getattr(self.obj, self.attr)

    @text.setter
    def text(self, value: str | None) -> None:
        setattr(self.obj, self.attr, value)


def _not_found(anchor: Anchor, what: str) -> NotFoundError:
    return NotFoundError(f"{what} at anchor {anchor.type}", anchor.id, anchor)


def resolve(
    m: Map,
    kind: str,
    target: str | None,
    name: str | None,
    *,
    path: str | None,
    symbol: str | None,
    owed: str | None,
    arm: str | None,
) -> Target:
    """Locate the anchor's carrier; an absent target is ERR-NOT-FOUND."""
    if kind == "header":
        return Target(Anchor("header"), m, "header_comment")
    if kind == "coverage":
        anchor = Anchor("coverage")
        if m.coverage is None:
            raise _not_found(anchor, "no coverage block")
        return Target(anchor, m.coverage)
    if kind == "curated":
        anchor = Anchor("curated", kind=target)
        entry = (
            None
            if m.coverage is None or m.coverage.curated is None
            else m.coverage.curated.get(target or "")
        )
        if entry is None:
            raise _not_found(anchor, f"no curated entry `{target}`")
        return Target(anchor, entry)
    binding_id = target or ""
    b = m.bindings.get(binding_id)
    if b is None:
        raise NotFoundError(
            f"no binding `{binding_id}`", binding_id, Anchor("binding", id=binding_id)
        )
    if kind == "binding":
        return Target(Anchor("binding", id=binding_id), b)
    if kind == "locator":
        anchor = Anchor("locator", id=binding_id, path=path, symbol=symbol)
        for loc in b.locators:
            if loc.identity() == (path, symbol):
                return Target(anchor, loc)
        raise _not_found(anchor, f"no locator {path}#{symbol or ''}")
    if kind == "field":
        anchor = Anchor("field", id=binding_id, field=name)
        fl = None if b.fields is None else b.fields.get(name or "")
        if fl is None:
            raise _not_found(anchor, f"no field `{name}`")
        return Target(anchor, fl)
    identity = ("owed", owed, arm) if owed is not None else ("bound", path, symbol, arm)
    anchor = Anchor("assertion", id=binding_id, path=path, symbol=symbol, arm=arm, owed=owed)
    for a in b.asserted_by or []:
        if a.identity() == identity:
            return Target(anchor, a)
    raise _not_found(anchor, f"no assertion {identity!r}")


def result(target: Target) -> dict[str, Any]:
    """DICT: OUT-COMMENT"""
    return {"anchor": target.anchor.to_plain(), "text": target.text}


def get(target: Target) -> dict[str, Any]:
    if target.text is None:
        raise _not_found(target.anchor, "no comment")
    return result(target)


def set_text(target: Target, text: str) -> dict[str, Any]:
    """Replaces any comment; the carrier form follows the new text. DICT: CLI-COMMENT-SET"""
    target.text = text
    return result(target)


def unset(target: Target) -> dict[str, Any]:
    """DICT: CLI-COMMENT-UNSET"""
    if target.text is None:
        raise _not_found(target.anchor, "no comment")
    target.text = None
    return result(target)
