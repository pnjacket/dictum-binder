"""COMPONENT-SCHEMA — the JSON Schema of ENTITY-MAP and the shape checker.

Both are derived from the Model's ``SHAPE`` rule table (ADR-SCHEMA-SINGLE-
SOURCE, ADR-OWN-SHAPE-VALIDATOR): ``schema()`` builds the JSON Schema
document, ``check_shape`` runs the same table over a plain value, and the
repository file ``dbind.schema.json`` is generated from ``schema_json()``.

DICT: COMPONENT-SCHEMA
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from dbind.model import ID_PATTERN, KIND_PATTERN, SHAPE, Finding, check_node

# The schema major this binary writes and accepts. DICT: INV-SCHEMA-VERSION
SCHEMA_VERSION = 1

RULES = SHAPE

SCALAR_PATTERN = "^[^\\u0000-\\u001f\\u007f-\\u009f]+$"

_NODE_TITLES = {
    "binding": "Binding — one contract's realisation in code (ENTITY-BINDING)",
    "locator": "Locator — a code site: repository-relative path plus optional symbol "
    "(ENTITY-LOCATOR)",
    "field_locator": "Field locator — where one field of an entity is realised "
    "(ENTITY-FIELD-LOCATOR)",
    "wire": "Wire sub-contract of a dual realisation: any non-empty subset (ENTITY-WIRE)",
    "assertion": "Assertion — a bound test (path, symbol, run) or an owed one (owed), optionally "
    "arm-labelled (ENTITY-ASSERTION)",
    "coverage": "Coverage declaration — fully_bound kinds and curated kinds with reasons "
    "(ENTITY-COVERAGE)",
}


def _string_schema() -> dict[str, Any]:
    return {"type": "string", "minLength": 1, "pattern": SCALAR_PATTERN}


def _spec_schema(spec: dict[str, Any]) -> dict[str, Any]:
    kind = spec["type"]
    if kind == "str":
        return _string_schema()
    if kind == "int":
        return {"type": "integer"}
    if kind == "enum":
        return {"type": "string", "enum": list(spec["values"])}
    if kind == "node":
        return {"$ref": f"#/$defs/{spec['node']}"}
    if kind == "list":
        item = spec["item"]
        if item == "kind":
            return {
                "type": "array",
                "items": {"type": "string", "pattern": KIND_PATTERN},
                "uniqueItems": True,
                "minItems": 1,
            }
        return {"type": "array", "items": {"$ref": f"#/$defs/{item}"}}
    # map
    item = spec["item"]
    if item == "reason":
        return {
            "type": "object",
            "propertyNames": {"pattern": spec["key_pattern"]},
            "additionalProperties": _string_schema(),
            "minProperties": 1,
        }
    out: dict[str, Any] = {"type": "object", "additionalProperties": {"$ref": f"#/$defs/{item}"}}
    if "key_pattern" in spec:
        out["propertyNames"] = {"pattern": spec["key_pattern"]}
    else:
        out["propertyNames"] = {"minLength": 1, "pattern": SCALAR_PATTERN}
        out["minProperties"] = 1
    return out


def _node_schema(node: str) -> dict[str, Any]:
    spec = SHAPE[node]
    out: dict[str, Any] = {
        "type": "object",
        "properties": {key: _spec_schema(s) for key, s in spec["keys"].items()},
        "additionalProperties": False,
    }
    if spec["required"]:
        out["required"] = list(spec["required"])
    if node in _NODE_TITLES:
        out["title"] = _NODE_TITLES[node]
    if node == "wire":
        out["minProperties"] = 1
    if node == "coverage":
        out["minProperties"] = 1
    if node == "binding":
        out["properties"]["asserted_by"]["minItems"] = 1
    return out


def schema() -> dict[str, Any]:
    """The JSON Schema (draft 2020-12) of a canonical bindings.yaml document."""
    doc = _node_schema("document")
    doc.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Dictum binding map (dictum-binder canonical shape)",
            "description": (
                "Shape of bindings.yaml as written and read by dictum-binder. Rules the schema "
                "cannot "
                "express (cross-field invariants, comment carriers, canonical layout) are listed "
                "in the README beside this file's checksum and enforced by `dbind validate`."
            ),
            "$defs": {node: _node_schema(node) for node in SHAPE if node != "document"},
        }
    )
    doc["properties"]["schema_version"]["description"] = (
        "Equal to the dictum-binder major version that owns the layout; this build writes "
        f"{SCHEMA_VERSION}."
    )
    doc["properties"]["bindings"]["description"] = (
        f"Contract ID → binding. IDs follow `{ID_PATTERN}`: Dictum's grammar with no all-digit "
        "segment."
    )
    return doc


def schema_json() -> bytes:
    """Deterministic serialisation: sorted keys, two-space indent, UTF-8, one trailing newline."""
    return (json.dumps(schema(), sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def checksum() -> str:
    return hashlib.sha256(schema_json()).hexdigest()


def check_shape(value: Any, node: str) -> list[Finding]:
    """Shape-check a plain value as ``node`` with the same rules the Loader applies."""
    return check_node(value, node)
