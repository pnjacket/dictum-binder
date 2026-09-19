"""CLI-COVERAGE-GET / CLI-COVERAGE-FULLY-BOUND / CLI-COVERAGE-CURATED. DICT: CLI-COVERAGE-GET"""

from __future__ import annotations

from typing import Any

from lspd import validator
from lspd.errors import DuplicateError, InputInvalidError, NotFoundError
from lspd.model import Anchor, Coverage, CuratedEntry, Map


def projection(cov: Coverage | None) -> dict[str, Any]:
    """DICT: OUT-COVERAGE — empty list / empty object when absent in the file."""
    if cov is None:
        return {"comment": None, "fully_bound": [], "curated": {}}
    return {
        "comment": cov.comment,
        "fully_bound": list(cov.fully_bound or []),
        "curated": {
            kind: {"reason": entry.reason, "comment": entry.comment}
            for kind, entry in (cov.curated or {}).items()
        },
    }


def result(m: Map) -> dict[str, Any]:
    """DICT: OUT-WRITE-RESULT (coverage arm) and the CLI-COVERAGE-GET result alike."""
    return {"coverage": projection(m.coverage)}


def _ensure(m: Map) -> Coverage:
    if m.coverage is None:
        m.coverage = Coverage()
    return m.coverage


def _prune(m: Map) -> None:
    """An empty coverage block is removed together with its comment."""
    cov = m.coverage
    if cov is not None and cov.fully_bound is None and cov.curated is None:
        m.coverage = None


def _refuse_if_invalid(m: Map) -> None:
    """A mutation that breaks INV-COVERAGE-WELLFORMED (a kind in both lists) is input the
    caller can fix: ERR-INPUT-INVALID carrying the finding. DICT: CLI-COVERAGE-FULLY-BOUND"""
    findings = [f for f in validator.validate(m) if f.severity == "error"]
    if findings:
        raise InputInvalidError(validator.finalize(findings))


def fully_bound_add(m: Map, kind: str) -> Map:
    cov = _ensure(m)
    if kind in (cov.fully_bound or []):
        raise DuplicateError(
            f"`{kind}` is already in fully_bound", None, Anchor("coverage", kind=kind)
        )
    cov.fully_bound = [*(cov.fully_bound or []), kind]
    _refuse_if_invalid(m)
    return m


def fully_bound_remove(m: Map, kind: str) -> Map:
    cov = m.coverage
    if cov is None or cov.fully_bound is None or kind not in cov.fully_bound:
        raise NotFoundError(f"`{kind}` is not in fully_bound", None, Anchor("coverage", kind=kind))
    cov.fully_bound = [k for k in cov.fully_bound if k != kind] or None
    _prune(m)
    return m


def curated_set(m: Map, kind: str, entry: CuratedEntry, *, comment_given: bool) -> Map:
    """DICT: CLI-COVERAGE-CURATED — set replaces the reason in place, keeping the comment
    unless one was given."""
    cov = _ensure(m)
    if cov.curated is None:
        cov.curated = {}
    existing = cov.curated.get(kind)
    if existing is not None and not comment_given:
        entry.comment = existing.comment
    cov.curated[kind] = entry
    _refuse_if_invalid(m)
    return m


def curated_unset(m: Map, kind: str) -> Map:
    cov = m.coverage
    if cov is None or cov.curated is None or kind not in cov.curated:
        raise NotFoundError(f"no curated entry `{kind}`", None, Anchor("curated", kind=kind))
    del cov.curated[kind]
    if not cov.curated:
        cov.curated = None
    _prune(m)
    return m
