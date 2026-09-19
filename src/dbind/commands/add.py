"""CLI-ADD-LOCATOR / CLI-ADD-FIELD / CLI-ADD-ASSERTION — append one entry. DICT: CLI-ADD-LOCATOR"""

from __future__ import annotations

from dbind.errors import DuplicateError, NotFoundError
from dbind.model import Anchor, Assertion, Binding, FieldLocator, Locator, Map


def require(m: Map, binding_id: str) -> Binding:
    b = m.bindings.get(binding_id)
    if b is None:
        raise NotFoundError(
            f"no binding `{binding_id}`", binding_id, Anchor("binding", id=binding_id)
        )
    return b


def locator(m: Map, binding_id: str, loc: Locator) -> Binding:
    """Appends last; a present path+symbol pair is ERR-DUPLICATE."""
    b = require(m, binding_id)
    if any(existing.identity() == loc.identity() for existing in b.locators):
        raise DuplicateError(
            f"locator {loc.path}#{loc.symbol or ''} is already present on `{binding_id}`",
            binding_id,
            Anchor("locator", id=binding_id, path=loc.path, symbol=loc.symbol),
        )
    b.locators.append(loc)
    return b


def field(m: Map, binding_id: str, name: str, fl: FieldLocator, *, comment_given: bool) -> Binding:
    """An existing NAME is replaced in place, keeping its comment unless one was given; a new
    NAME is appended last. DICT: CLI-ADD-FIELD"""
    b = require(m, binding_id)
    if b.fields is None:
        b.fields = {}
    existing = b.fields.get(name)
    if existing is not None and not comment_given:
        fl.comment = existing.comment
    b.fields[name] = fl
    return b


def assertion(m: Map, binding_id: str, a: Assertion) -> Binding:
    """Appends last; a present identity is ERR-DUPLICATE. DICT: CLI-ADD-ASSERTION"""
    b = require(m, binding_id)
    if any(existing.identity() == a.identity() for existing in b.asserted_by or []):
        raise DuplicateError(
            f"assertion {a.identity()!r} is already present on `{binding_id}`",
            binding_id,
            Anchor(
                "assertion", id=binding_id, path=a.path, symbol=a.symbol, arm=a.arm, owed=a.owed
            ),
        )
    if b.asserted_by is None:
        b.asserted_by = []
    b.asserted_by.append(a)
    return b
