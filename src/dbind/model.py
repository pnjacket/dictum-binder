"""COMPONENT-MODEL — the plain in-memory form of Domain & Data's entities.

No library types. The ``SHAPE`` table is the single description of the
closed shape (keys, required keys, types, enums, patterns); ``from_plain``
converts a plain (parsed) value into Model objects and reports everything
the Model cannot represent, and ``COMPONENT-SCHEMA`` derives the JSON
Schema from the same table.

DICT: COMPONENT-MODEL
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

# --- value grammars ---------------------------------------------------------

# DICT: INV-ID-GRAMMAR — Dictum's grammar with no all-digit segment.
ID_PATTERN = r"^[A-Z][A-Z0-9]+(-(?![0-9]+(-|$))[A-Z0-9]+)+$"
ID_RE = re.compile(ID_PATTERN)
KIND_PATTERN = r"^[A-Z][A-Z0-9]+$"
KIND_RE = re.compile(KIND_PATTERN)
# Single-line, no control characters: C0, DEL, C1 (INV-SYMBOL-NONEMPTY).
CONTROL_RE = re.compile("[\\x00-\\x1f\\x7f-\\x9f]")
LINE_SUFFIX_RE = re.compile(r":[0-9]+$")


def is_contract_id(value: str) -> bool:
    """DICT: ENTITY-CONTRACT-ID"""
    return ID_RE.match(value) is not None


def kind_of(contract_id: str) -> str:
    return contract_id.split("-", 1)[0]


def has_control_chars(value: str) -> bool:
    return CONTROL_RE.search(value) is not None


def path_form_problem(path: str) -> str | None:
    """Return why ``path`` violates ENTITY-PATH, or None. DICT: ENTITY-PATH

    The trailing ``:digits`` case is reported under INV-NO-LINE-NUMBERS by the
    validator, never here.
    """
    if path == "" or path.strip() == "":
        return "path is empty"
    if "\\" in path:
        return "path contains a backslash"
    if path.startswith("/"):
        return "path is absolute"
    if re.match(r"^[A-Za-z]:", path):
        return "path has a drive-letter prefix"
    if "~" in path:
        return "path contains `~`"
    for segment in path.split("/"):
        if segment == "":
            return "path has an empty segment"
        if segment in (".", ".."):
            return f"path has a `{segment}` segment"
    return None


# --- entities ----------------------------------------------------------------


@dataclass
class Anchor:
    """Where a comment or finding attaches. DICT: ENTITY-COMMENT"""

    type: str
    id: str | None = None
    path: str | None = None
    symbol: str | None = None
    arm: str | None = None
    owed: str | None = None
    field: str | None = None
    kind: str | None = None

    def to_plain(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "path": self.path,
            "symbol": self.symbol,
            "arm": self.arm,
            "owed": self.owed,
            "field": self.field,
            "kind": self.kind,
        }

    def key(self) -> tuple[Any, ...]:
        return (
            self.type,
            self.id,
            self.path,
            self.symbol,
            self.arm,
            self.owed,
            self.field,
            self.kind,
        )


@dataclass
class Finding:
    """DICT: ENTITY-FINDING"""

    code: str
    severity: str
    anchor: Anchor
    message: str
    line: int | None = None

    def sort_key(self) -> tuple[int, str]:
        return (-1 if self.line is None else self.line, self.code)


@dataclass
class Locator:
    """DICT: ENTITY-LOCATOR"""

    path: str
    symbol: str | None = None
    role: str | None = None
    comment: str | None = None
    line: int | None = None
    end_line: int | None = None

    def identity(self) -> tuple[str, str | None]:
        return (self.path, self.symbol)


@dataclass
class FieldLocator:
    """DICT: ENTITY-FIELD-LOCATOR"""

    path: str
    symbol: str | None = None
    comment: str | None = None
    line: int | None = None
    end_line: int | None = None


@dataclass
class Wire:
    """DICT: ENTITY-WIRE"""

    casing: str | None = None
    enums: str | None = None
    dates: str | None = None
    line: int | None = None

    def is_empty(self) -> bool:
        return self.casing is None and self.enums is None and self.dates is None


@dataclass
class Assertion:
    """DICT: ENTITY-ASSERTION"""

    path: str | None = None
    symbol: str | None = None
    run: str | None = None
    arm: str | None = None
    owed: str | None = None
    comment: str | None = None
    line: int | None = None
    end_line: int | None = None

    def identity(self) -> tuple[Any, ...]:
        if self.owed is not None and self.path is None:
            return ("owed", self.owed, self.arm)
        return ("bound", self.path, self.symbol, self.arm)


@dataclass
class Binding:
    """DICT: ENTITY-BINDING"""

    id: str
    locators: list[Locator] = field(default_factory=list)
    compare_via: str | None = None
    fields: dict[str, FieldLocator] | None = None
    wire: Wire | None = None
    asserted_by: list[Assertion] | None = None
    comment: str | None = None
    line: int | None = None

    @property
    def kind(self) -> str:
        return kind_of(self.id)


@dataclass
class CuratedEntry:
    reason: str
    comment: str | None = None
    line: int | None = None


@dataclass
class Coverage:
    """DICT: ENTITY-COVERAGE"""

    fully_bound: list[str] | None = None
    curated: dict[str, CuratedEntry] | None = None
    comment: str | None = None
    line: int | None = None


@dataclass
class Map:
    """DICT: ENTITY-MAP"""

    schema_version: int | None = None
    bindings: dict[str, Binding] = field(default_factory=dict)
    coverage: Coverage | None = None
    header_comment: str | None = None


# --- the closed shape ----------------------------------------------------------
#
# Each node: keys -> spec; spec: type in {str, int, list, map, enum}; optional
# child node name, enum values, key pattern (for maps), item node (for lists).

SHAPE: dict[str, dict[str, Any]] = {
    "document": {
        "keys": {
            "schema_version": {"type": "int"},
            "bindings": {
                "type": "map",
                "item": "binding",
                "key_pattern": ID_PATTERN,
                "key_code": "INV-ID-GRAMMAR",
            },
            "coverage": {"type": "node", "node": "coverage"},
        },
        "required": ["schema_version", "bindings"],
    },
    "binding": {
        "keys": {
            "locators": {"type": "list", "item": "locator"},
            "compare_via": {"type": "str"},
            "fields": {"type": "map", "item": "field_locator"},
            "wire": {"type": "node", "node": "wire"},
            "asserted_by": {"type": "list", "item": "assertion"},
        },
        "required": ["locators"],
    },
    "locator": {
        "keys": {
            "path": {"type": "str"},
            "symbol": {"type": "str"},
            "role": {"type": "enum", "values": ["producer", "consumer"], "code": "INV-ROLE-VALUES"},
        },
        "required": ["path"],
    },
    "field_locator": {
        "keys": {"path": {"type": "str"}, "symbol": {"type": "str"}},
        "required": ["path"],
    },
    "wire": {
        "keys": {"casing": {"type": "str"}, "enums": {"type": "str"}, "dates": {"type": "str"}},
        "required": [],
    },
    "assertion": {
        "keys": {
            "path": {"type": "str"},
            "symbol": {"type": "str"},
            "run": {"type": "str"},
            "arm": {"type": "str"},
            "owed": {"type": "str"},
        },
        "required": [],
    },
    "coverage": {
        "keys": {
            "fully_bound": {"type": "list", "item": "kind"},
            "curated": {"type": "map", "item": "reason", "key_pattern": KIND_PATTERN},
        },
        "required": [],
    },
}

LineOf = Callable[[Any, Any], int | None]


def _no_line(_container: Any, _key: Any) -> int | None:
    return None


def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, Mapping):
        return "mapping"
    if isinstance(value, Sequence):
        return "list"
    if value is None:
        return "null"
    return type(value).__name__


def _is_str(value: Any) -> bool:
    return isinstance(value, str)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class _Converter:
    """Walks a plain value against SHAPE, building Model objects and findings."""

    def __init__(self, line_of: LineOf) -> None:
        self.line_of = line_of
        self.findings: list[Finding] = []

    def finding(self, code: str, anchor: Anchor, message: str, line: int | None) -> None:
        self.findings.append(Finding(code, "error", anchor, message, line))

    def _line(self, container: Any, key: Any) -> int | None:
        return self.line_of(container, key)

    def closed_keys(
        self, mapping: Mapping[Any, Any], node: str, anchor: Anchor, line: int | None
    ) -> None:
        spec = SHAPE[node]
        for key in mapping:
            if key not in spec["keys"]:
                key_line = self._line(mapping, key) or line
                self.finding("INV-CLOSED-KEYS", anchor, f"unknown key `{key}` in {node}", key_line)
                if key in ("lines", "line"):
                    self.finding(
                        "INV-NO-LINE-NUMBERS",
                        anchor,
                        f"key `{key}` is a line reference; a stale line number fails silently — "
                        "use a symbol",
                        key_line,
                    )
        for key in spec["required"]:
            if key not in mapping:
                self.finding(
                    "INV-CLOSED-KEYS", anchor, f"missing required key `{key}` in {node}", line
                )

    def scalar(
        self, mapping: Mapping[Any, Any], key: str, anchor: Anchor, line: int | None
    ) -> str | None:
        if key not in mapping:
            return None
        value = mapping[key]
        if not _is_str(value):
            self.finding(
                "INV-CLOSED-KEYS",
                anchor,
                f"`{key}` must be a string, found {_type_name(value)}",
                self._line(mapping, key) or line,
            )
            return None
        return value

    def enum(
        self,
        mapping: Mapping[Any, Any],
        key: str,
        spec: dict[str, Any],
        anchor: Anchor,
        line: int | None,
    ) -> str | None:
        value = self.scalar(mapping, key, anchor, line)
        if value is None:
            return None
        if value not in spec["values"]:
            self.finding(
                spec["code"],
                anchor,
                f"`{key}` must be one of {', '.join(spec['values'])}, found `{value}`",
                self._line(mapping, key) or line,
            )
            return None
        return value

    def mapping_or_none(
        self, value: Any, what: str, anchor: Anchor, line: int | None
    ) -> Mapping[Any, Any] | None:
        if not isinstance(value, Mapping):
            self.finding(
                "INV-CLOSED-KEYS",
                anchor,
                f"{what} must be a mapping, found {_type_name(value)}",
                line,
            )
            return None
        return value

    def list_or_none(
        self, value: Any, what: str, anchor: Anchor, line: int | None
    ) -> Sequence[Any] | None:
        if not isinstance(value, Sequence) or isinstance(value, str):
            self.finding(
                "INV-CLOSED-KEYS", anchor, f"{what} must be a list, found {_type_name(value)}", line
            )
            return None
        return value

    # -- entries ---------------------------------------------------------------

    def locator(
        self, value: Any, binding_id: str, container: Any, index: int, anchor_line: int | None
    ) -> Locator | None:
        anchor = Anchor("locator", id=binding_id)
        line = self._line(container, index) or anchor_line
        mapping = self.mapping_or_none(value, "a locator", anchor, line)
        if mapping is None:
            return None
        self.closed_keys(mapping, "locator", anchor, line)
        path = self.scalar(mapping, "path", anchor, line)
        symbol = self.scalar(mapping, "symbol", anchor, line)
        role = self.enum(mapping, "role", SHAPE["locator"]["keys"]["role"], anchor, line)
        if path is None:
            return None
        anchor.path, anchor.symbol = path, symbol
        return Locator(
            path=path,
            symbol=symbol,
            role=role,
            line=line,
            end_line=_end_line(mapping, self.line_of, line),
        )

    def field_locator(
        self, value: Any, binding_id: str, name: str, container: Any, anchor_line: int | None
    ) -> FieldLocator | None:
        anchor = Anchor("field", id=binding_id, field=name)
        line = self._line(container, name) or anchor_line
        mapping = self.mapping_or_none(value, f"field `{name}`", anchor, line)
        if mapping is None:
            return None
        self.closed_keys(mapping, "field_locator", anchor, line)
        path = self.scalar(mapping, "path", anchor, line)
        symbol = self.scalar(mapping, "symbol", anchor, line)
        if path is None:
            return None
        return FieldLocator(
            path=path, symbol=symbol, line=line, end_line=_end_line(mapping, self.line_of, line)
        )

    def assertion(
        self, value: Any, binding_id: str, container: Any, index: int, anchor_line: int | None
    ) -> Assertion | None:
        anchor = Anchor("assertion", id=binding_id)
        line = self._line(container, index) or anchor_line
        mapping = self.mapping_or_none(value, "an assertion", anchor, line)
        if mapping is None:
            return None
        self.closed_keys(mapping, "assertion", anchor, line)
        a = Assertion(
            path=self.scalar(mapping, "path", anchor, line),
            symbol=self.scalar(mapping, "symbol", anchor, line),
            run=self.scalar(mapping, "run", anchor, line),
            arm=self.scalar(mapping, "arm", anchor, line),
            owed=self.scalar(mapping, "owed", anchor, line),
            line=line,
            end_line=_end_line(mapping, self.line_of, line),
        )
        return a

    def wire(
        self, value: Any, binding_id: str, container: Any, anchor_line: int | None
    ) -> Wire | None:
        anchor = Anchor("binding", id=binding_id)
        line = self._line(container, "wire") or anchor_line
        mapping = self.mapping_or_none(value, "`wire`", anchor, line)
        if mapping is None:
            return None
        self.closed_keys(mapping, "wire", anchor, line)
        return Wire(
            casing=self.scalar(mapping, "casing", anchor, line),
            enums=self.scalar(mapping, "enums", anchor, line),
            dates=self.scalar(mapping, "dates", anchor, line),
            line=line,
        )

    def binding(self, binding_id: str, value: Any, container: Any) -> Binding | None:
        anchor = Anchor("binding", id=binding_id)
        line = self._line(container, binding_id)
        mapping = self.mapping_or_none(value, f"binding `{binding_id}`", anchor, line)
        if mapping is None:
            return None
        self.closed_keys(mapping, "binding", anchor, line)
        if "locators" not in mapping:
            return None
        locators_raw = self.list_or_none(
            mapping["locators"], "`locators`", anchor, self._line(mapping, "locators") or line
        )
        if locators_raw is None:
            return None
        b = Binding(id=binding_id, line=line)
        for index, item in enumerate(locators_raw):
            loc = self.locator(item, binding_id, locators_raw, index, line)
            if loc is not None:
                b.locators.append(loc)
        b.compare_via = self.scalar(mapping, "compare_via", anchor, line)
        if "fields" in mapping:
            fields_raw = self.mapping_or_none(
                mapping["fields"], "`fields`", anchor, self._line(mapping, "fields") or line
            )
            if fields_raw is not None:
                b.fields = {}
                for name, item in fields_raw.items():
                    key = str(name)
                    fl = self.field_locator(item, binding_id, key, fields_raw, line)
                    if fl is not None:
                        b.fields[key] = fl
        if "wire" in mapping:
            b.wire = self.wire(mapping["wire"], binding_id, mapping, line)
        if "asserted_by" in mapping:
            asserted_raw = self.list_or_none(
                mapping["asserted_by"],
                "`asserted_by`",
                anchor,
                self._line(mapping, "asserted_by") or line,
            )
            if asserted_raw is not None:
                b.asserted_by = []
                for index, item in enumerate(asserted_raw):
                    a = self.assertion(item, binding_id, asserted_raw, index, line)
                    if a is not None:
                        b.asserted_by.append(a)
        return b

    def coverage(self, value: Any, container: Any) -> Coverage | None:
        anchor = Anchor("coverage")
        line = self._line(container, "coverage")
        mapping = self.mapping_or_none(value, "`coverage`", anchor, line)
        if mapping is None:
            return None
        self.closed_keys(mapping, "coverage", anchor, line)
        cov = Coverage(line=line)
        if "fully_bound" in mapping:
            fb = self.list_or_none(
                mapping["fully_bound"],
                "`fully_bound`",
                anchor,
                self._line(mapping, "fully_bound") or line,
            )
            if fb is not None:
                cov.fully_bound = []
                for index, item in enumerate(fb):
                    if _is_str(item):
                        cov.fully_bound.append(item)
                    else:
                        self.finding(
                            "INV-CLOSED-KEYS",
                            anchor,
                            f"`fully_bound` entries must be strings, found {_type_name(item)}",
                            self._line(fb, index) or line,
                        )
        if "curated" in mapping:
            cur = self.mapping_or_none(
                mapping["curated"], "`curated`", anchor, self._line(mapping, "curated") or line
            )
            if cur is not None:
                cov.curated = {}
                for kind, reason in cur.items():
                    k = str(kind)
                    entry_anchor = Anchor("curated", kind=k)
                    entry_line = self._line(cur, kind) or line
                    if _is_str(reason):
                        cov.curated[k] = CuratedEntry(reason=reason, line=entry_line)
                    else:
                        self.finding(
                            "INV-CLOSED-KEYS",
                            entry_anchor,
                            f"curated reason for `{k}` must be a string, found "
                            f"{_type_name(reason)}",
                            entry_line,
                        )
        return cov

    def document(self, value: Any) -> Map:
        anchor = Anchor("file")
        m = Map()
        mapping = self.mapping_or_none(value, "the document", anchor, None)
        if mapping is None:
            return m
        self.closed_keys(mapping, "document", anchor, None)
        if "schema_version" in mapping:
            sv = mapping["schema_version"]
            if _is_int(sv):
                m.schema_version = sv
            else:
                self.finding(
                    "INV-CLOSED-KEYS",
                    anchor,
                    f"`schema_version` must be an integer, found {_type_name(sv)}",
                    self._line(mapping, "schema_version"),
                )
        if "bindings" in mapping:
            bindings_raw = self.mapping_or_none(
                mapping["bindings"], "`bindings`", anchor, self._line(mapping, "bindings")
            )
            if bindings_raw is not None:
                for raw_id, raw_binding in bindings_raw.items():
                    binding_id = str(raw_id)
                    if not is_contract_id(binding_id):
                        self.finding(
                            "INV-ID-GRAMMAR",
                            Anchor("binding", id=binding_id),
                            _grammar_message(binding_id),
                            self._line(bindings_raw, raw_id),
                        )
                        continue
                    b = self.binding(binding_id, raw_binding, bindings_raw)
                    if b is not None:
                        m.bindings[binding_id] = b
        if "coverage" in mapping:
            m.coverage = self.coverage(mapping["coverage"], mapping)
        return m


def _end_line(mapping: Mapping[Any, Any], line_of: LineOf, start: int | None) -> int | None:
    """The last source line an entry occupies (block-style entries span several)."""
    end = start
    for key in mapping:
        line = line_of(mapping, key)
        if line is not None and (end is None or line > end):
            end = line
    return end


def _grammar_message(binding_id: str) -> str:
    segments = binding_id.split("-")
    digits = [s for s in segments if s.isdigit()]
    if len(segments) >= 2 and digits and re.match(r"^[A-Z][A-Z0-9]+(-[A-Z0-9]+)+$", binding_id):
        return (
            f"`{binding_id}` has an all-digit segment ({', '.join(digits)}); dictum-binder accepts "
            "semantic IDs only "
            "(digits inside a segment such as V2 are fine)"
        )
    return f"`{binding_id}` is not a contract ID: expected `{ID_PATTERN}` with no all-digit segment"


def from_plain(value: Any, line_of: LineOf = _no_line) -> tuple[Map, list[Finding]]:
    """Convert a parsed plain value into a Map, reporting what cannot be represented."""
    conv = _Converter(line_of)
    m = conv.document(value)
    return m, conv.findings


def check_node(value: Any, node: str, line_of: LineOf = _no_line) -> list[Finding]:
    """Shape-check a plain value as ``node`` (binding, locator, …) without keeping the result."""
    conv = _Converter(line_of)
    if node == "document":
        conv.document(value)
    elif node == "binding":
        conv.binding("INPUT-BINDING", value, {"INPUT-BINDING": value})
    elif node == "locator":
        conv.locator(value, "INPUT-BINDING", [value], 0, None)
    elif node == "field_locator":
        conv.field_locator(value, "INPUT-BINDING", "input", {"input": value}, None)
    elif node == "assertion":
        conv.assertion(value, "INPUT-BINDING", [value], 0, None)
    elif node == "coverage":
        conv.coverage(value, {"coverage": value})
    else:
        raise ValueError(
            f"unknown node {node}"
        )  # pragma: no cover — programmer error, not a contracted path
    return conv.findings


def binding_to_plain(b: Binding) -> dict[str, Any]:
    """The binding as plain YAML-shaped data in canonical key order (no comments)."""
    out: dict[str, Any] = {"locators": [_locator_plain(loc) for loc in b.locators]}
    if b.compare_via is not None:
        out["compare_via"] = b.compare_via
    if b.fields is not None:
        out["fields"] = {name: _field_plain(fl) for name, fl in b.fields.items()}
    if b.wire is not None:
        out["wire"] = {
            k: v
            for k, v in (
                ("casing", b.wire.casing),
                ("enums", b.wire.enums),
                ("dates", b.wire.dates),
            )
            if v is not None
        }
    if b.asserted_by is not None:
        out["asserted_by"] = [_assertion_plain(a) for a in b.asserted_by]
    return out


def _locator_plain(loc: Locator) -> dict[str, Any]:
    out: dict[str, Any] = {"path": loc.path}
    if loc.symbol is not None:
        out["symbol"] = loc.symbol
    if loc.role is not None:
        out["role"] = loc.role
    return out


def _field_plain(fl: FieldLocator) -> dict[str, Any]:
    out: dict[str, Any] = {"path": fl.path}
    if fl.symbol is not None:
        out["symbol"] = fl.symbol
    return out


def _assertion_plain(a: Assertion) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in (
        ("path", a.path),
        ("symbol", a.symbol),
        ("run", a.run),
        ("arm", a.arm),
        ("owed", a.owed),
    ):
        if val is not None:
            out[key] = val
    return out


def map_to_plain(m: Map) -> dict[str, Any]:
    """The whole map as plain data in canonical key order (no comments)."""
    out: dict[str, Any] = {
        "schema_version": m.schema_version,
        "bindings": {bid: binding_to_plain(b) for bid, b in m.bindings.items()},
    }
    if m.coverage is not None:
        cov: dict[str, Any] = {}
        if m.coverage.fully_bound is not None:
            cov["fully_bound"] = list(m.coverage.fully_bound)
        if m.coverage.curated is not None:
            cov["curated"] = {k: e.reason for k, e in m.coverage.curated.items()}
        out["coverage"] = cov
    return out


# -- input documents (OUT-* projections used as write input) ----------------------------

_INPUT_ANCHOR_TYPE = {
    "binding": "binding",
    "locator": "locator",
    "field_locator": "field",
    "assertion": "assertion",
    "curated": "curated",
}


def _split_comment(
    value: Any, anchor: Anchor, conv: _Converter
) -> tuple[dict[str, Any] | None, str | None]:
    """Copy an input object without its ``null`` keys (absent) and its ``comment`` key."""
    if not isinstance(value, Mapping):
        return None, None
    plain = {str(k): v for k, v in value.items() if v is not None and k != "comment"}
    comment = value.get("comment")
    if comment is not None and not isinstance(comment, str):
        conv.finding(
            "INV-CLOSED-KEYS",
            anchor,
            f"`comment` must be a string or null, found {_type_name(comment)}",
            None,
        )
        comment = None
    return plain, comment


def from_input(
    value: Any, node: str, *, binding_id: str = "", name: str = "", kind: str = ""
) -> tuple[Any, list[Finding]]:
    """An input document (nulls mean absent, ``comment`` keys sit at their anchors, ``id`` and
    ``kind`` may accompany a binding) converted like a file value: the object with its comments
    attached, plus the shape findings. Unrepresentable content yields ``None``."""
    conv = _Converter(_no_line)
    anchor = Anchor(_INPUT_ANCHOR_TYPE[node], id=binding_id or None, field=name or None)
    if node == "curated":
        anchor = Anchor("curated", kind=kind)
    if not isinstance(value, Mapping):
        conv.finding(
            "INV-CLOSED-KEYS",
            anchor,
            f"{node} input must be an object, found {_type_name(value)}",
            None,
        )
        return None, conv.findings
    plain, comment = _split_comment(value, anchor, conv)
    assert plain is not None
    if node == "binding":
        plain.pop("id", None)
        plain.pop("kind", None)
        b = _binding_from_input(plain, binding_id, conv)
        if b is not None:
            b.comment = comment
        return b, conv.findings
    if node == "locator":
        loc = conv.locator(plain, binding_id, [plain], 0, None)
        if loc is not None:
            loc.comment = comment
        return loc, conv.findings
    if node == "field_locator":
        fl = conv.field_locator(plain, binding_id, name, {name: plain}, None)
        if fl is not None:
            fl.comment = comment
        return fl, conv.findings
    if node == "assertion":
        a = conv.assertion(plain, binding_id, [plain], 0, None)
        if a is not None:
            a.comment = comment
        return a, conv.findings
    reason = plain.get("reason")
    if not isinstance(reason, str):
        conv.finding(
            "INV-CLOSED-KEYS",
            anchor,
            f"curated reason must be a string, found {_type_name(reason)}",
            None,
        )
        return None, conv.findings
    for key in plain:
        if key != "reason":
            conv.finding("INV-CLOSED-KEYS", anchor, f"unknown key `{key}` in curated entry", None)
    return CuratedEntry(reason=reason, comment=comment), conv.findings


def _binding_from_input(plain: dict[str, Any], binding_id: str, conv: _Converter) -> Binding | None:
    """Strip nested nulls and comments before the shape pass, then re-attach the comments."""
    anchor = Anchor("binding", id=binding_id)
    loc_comments: list[str | None] = []
    field_comments: dict[str, str | None] = {}
    assertion_comments: list[str | None] = []
    raw_locators = plain.get("locators")
    if isinstance(raw_locators, list):
        stripped = []
        for item in raw_locators:
            item_plain, item_comment = _split_comment(item, anchor, conv)
            stripped.append(item if item_plain is None else item_plain)
            loc_comments.append(item_comment)
        plain["locators"] = stripped
    raw_fields = plain.get("fields")
    if isinstance(raw_fields, Mapping):
        fields: dict[str, Any] = {}
        for key, item in raw_fields.items():
            item_plain, item_comment = _split_comment(item, anchor, conv)
            fields[str(key)] = item if item_plain is None else item_plain
            field_comments[str(key)] = item_comment
        plain["fields"] = fields
    raw_wire = plain.get("wire")
    if isinstance(raw_wire, Mapping):
        plain["wire"] = {str(k): v for k, v in raw_wire.items() if v is not None}
    raw_asserted = plain.get("asserted_by")
    if isinstance(raw_asserted, list):
        stripped = []
        for item in raw_asserted:
            item_plain, item_comment = _split_comment(item, anchor, conv)
            stripped.append(item if item_plain is None else item_plain)
            assertion_comments.append(item_comment)
        plain["asserted_by"] = stripped
    b = conv.binding(binding_id, plain, {binding_id: plain})
    if b is None:
        return None
    if len(loc_comments) == len(b.locators):
        for loc, text in zip(b.locators, loc_comments, strict=True):
            loc.comment = text
    if b.fields is not None:
        for key, fl in b.fields.items():
            fl.comment = field_comments.get(key)
    if b.asserted_by is not None and len(assertion_comments) == len(b.asserted_by):
        for a, text in zip(b.asserted_by, assertion_comments, strict=True):
            a.comment = text
    return b
