"""CLI-SET — upsert a whole binding. DICT: CLI-SET"""

from __future__ import annotations

from typing import Any

from dbind.commands import query
from dbind.model import Binding, Map


def apply(m: Map, b: Binding) -> Binding:
    """Unknown ID → appended last; known ID → replaced in place (INV-ORDER-PRESERVED)."""
    m.bindings[b.id] = b
    return b


def result(b: Binding) -> dict[str, Any]:
    """DICT: OUT-WRITE-RESULT"""
    return {"binding": query.binding(b)}
