"""CLI-FORMAT — canonical layout and order; the only command that reorders. DICT: CLI-FORMAT"""

from __future__ import annotations

from typing import Any

from lspd.model import Map


def canonicalise(m: Map) -> Map:
    """Bindings sorted by ID in byte order; fully_bound and curated sorted lexically; locators,
    fields and assertions keep the author's order (Domain, canonical order).

    DICT: ADR-FORMAT-ONLY-REORDERS
    """
    m.bindings = dict(sorted(m.bindings.items(), key=lambda item: item[0].encode("utf-8")))
    cov = m.coverage
    if cov is not None:
        if cov.fully_bound is not None:
            cov.fully_bound = sorted(cov.fully_bound, key=lambda k: k.encode("utf-8"))
        if cov.curated is not None:
            cov.curated = dict(
                sorted(cov.curated.items(), key=lambda item: item[0].encode("utf-8"))
            )
    return m


def result(*, changed: bool, checked_only: bool) -> dict[str, Any]:
    """DICT: OUT-FORMAT-RESULT"""
    return {"changed": changed, "checked_only": checked_only}
