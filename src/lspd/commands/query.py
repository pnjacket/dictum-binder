"""CLI-GET / CLI-LIST — read-only projections of bindings. DICT: CLI-GET"""

from __future__ import annotations

from typing import Any

from lspd.errors import NotFoundError
from lspd.model import Anchor, Assertion, Binding, FieldLocator, Locator, Map


def locator(loc: Locator) -> dict[str, Any]:
    """DICT: OUT-LOCATOR"""
    return {"path": loc.path, "symbol": loc.symbol, "role": loc.role, "comment": loc.comment}


def field_locator(fl: FieldLocator) -> dict[str, Any]:
    """DICT: OUT-FIELD-LOCATOR"""
    return {"path": fl.path, "symbol": fl.symbol, "comment": fl.comment}


def assertion(a: Assertion) -> dict[str, Any]:
    """DICT: OUT-ASSERTION"""
    return {
        "path": a.path,
        "symbol": a.symbol,
        "run": a.run,
        "arm": a.arm,
        "owed": a.owed,
        "comment": a.comment,
    }


def binding(b: Binding) -> dict[str, Any]:
    """DICT: OUT-BINDING"""
    return {
        "id": b.id,
        "kind": b.kind,
        "comment": b.comment,
        "locators": [locator(loc) for loc in b.locators],
        "compare_via": b.compare_via,
        "fields": None
        if b.fields is None
        else {name: field_locator(fl) for name, fl in b.fields.items()},
        "wire": None
        if b.wire is None
        else {"casing": b.wire.casing, "enums": b.wire.enums, "dates": b.wire.dates},
        "asserted_by": None if b.asserted_by is None else [assertion(a) for a in b.asserted_by],
    }


def has_comment(b: Binding) -> bool:
    return (
        b.comment is not None
        or any(loc.comment is not None for loc in b.locators)
        or any(fl.comment is not None for fl in (b.fields or {}).values())
        or any(a.comment is not None for a in b.asserted_by or [])
    )


def summary(b: Binding) -> dict[str, Any]:
    """DICT: OUT-BINDING-SUMMARY"""
    return {
        "id": b.id,
        "kind": b.kind,
        "stub": not b.locators,
        "locators": len(b.locators),
        "fields": len(b.fields or {}),
        "assertions": len(b.asserted_by or []),
        "has_comment": has_comment(b),
    }


def get(m: Map, ids: list[str]) -> dict[str, Any]:
    """CLI-GET: the requested bindings in argument order; the first unknown ID is ERR-NOT-FOUND."""
    out: list[dict[str, Any]] = []
    for contract_id in ids:
        b = m.bindings.get(contract_id)
        if b is None:
            raise NotFoundError(
                f"no binding `{contract_id}`", contract_id, Anchor("binding", id=contract_id)
            )
        out.append(binding(b))
    return {"bindings": out}


def list_bindings(m: Map, kinds: list[str], *, full: bool) -> dict[str, Any]:
    """File-order summaries (or full bindings) whose kind is in the union. DICT: CLI-LIST"""
    wanted = set(kinds)
    selected = [b for b in m.bindings.values() if not wanted or b.kind in wanted]
    return {"bindings": [binding(b) if full else summary(b) for b in selected]}
