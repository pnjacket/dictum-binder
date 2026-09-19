"""CLI-INIT — the canonical empty map. DICT: CLI-INIT"""

from __future__ import annotations

from dbind.model import Map
from dbind.schema import SCHEMA_VERSION


def empty_map() -> Map:
    return Map(schema_version=SCHEMA_VERSION)


def result(target: str) -> dict[str, str]:
    """DICT: OUT-INIT-RESULT"""
    return {"path": target}
