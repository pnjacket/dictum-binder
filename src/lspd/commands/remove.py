"""CLI-REMOVE — a whole binding, or one locator, field or assertion inside it. DICT: CLI-REMOVE"""

from __future__ import annotations

from typing import Any

from lspd.errors import NotFoundError
from lspd.model import Anchor, Binding, Map


def _require(m: Map, binding_id: str) -> Binding:
    b = m.bindings.get(binding_id)
    if b is None:
        raise NotFoundError(
            f"no binding `{binding_id}`", binding_id, Anchor("binding", id=binding_id)
        )
    return b


def binding(m: Map, binding_id: str) -> dict[str, Any]:
    """The whole binding goes, with every comment it carried."""
    _require(m, binding_id)
    del m.bindings[binding_id]
    return {"binding": None, "removed": binding_id}


def locator(m: Map, binding_id: str, path: str, symbol: str | None) -> Binding:
    """Removing the last locator leaves the stub form."""
    b = _require(m, binding_id)
    for index, loc in enumerate(b.locators):
        if loc.identity() == (path, symbol):
            del b.locators[index]
            return b
    raise NotFoundError(
        f"no locator {path}#{symbol or ''} on `{binding_id}`",
        binding_id,
        Anchor("locator", id=binding_id, path=path, symbol=symbol),
    )


def field(m: Map, binding_id: str, name: str) -> Binding:
    """Removing the last field removes the `fields` key."""
    b = _require(m, binding_id)
    if b.fields is None or name not in b.fields:
        raise NotFoundError(
            f"no field `{name}` on `{binding_id}`",
            binding_id,
            Anchor("field", id=binding_id, field=name),
        )
    del b.fields[name]
    if not b.fields:
        b.fields = None
    return b


def assertion(m: Map, binding_id: str, identity: tuple[Any, ...]) -> Binding:
    """Removing the last assertion removes the `asserted_by` key."""
    b = _require(m, binding_id)
    for index, a in enumerate(b.asserted_by or []):
        if a.identity() == identity:
            assert b.asserted_by is not None
            del b.asserted_by[index]
            if not b.asserted_by:
                b.asserted_by = None
            return b
    shape, *rest = identity
    anchor = (
        Anchor("assertion", id=binding_id, owed=rest[0], arm=rest[1])
        if shape == "owed"
        else Anchor("assertion", id=binding_id, path=rest[0], symbol=rest[1], arm=rest[2])
    )
    raise NotFoundError(f"no assertion {identity!r} on `{binding_id}`", binding_id, anchor)
