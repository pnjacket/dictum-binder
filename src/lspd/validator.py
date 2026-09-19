"""COMPONENT-VALIDATOR — findings from a Model (rule pass) or a candidate input.

The shape pass lives in the Model/Schema rule table; this module runs the
remaining INV-* rules over the Model and orders the result.

DICT: COMPONENT-VALIDATOR
"""

from __future__ import annotations

import os
from typing import Any

from lspd.model import (
    KIND_RE,
    LINE_SUFFIX_RE,
    Anchor,
    Assertion,
    Binding,
    FieldLocator,
    Finding,
    Locator,
    Map,
    from_input,
    has_control_chars,
    is_contract_id,
    path_form_problem,
)
from lspd.schema import SCHEMA_VERSION


def finalize(findings: list[Finding]) -> list[Finding]:
    """Document order (file anchors first), then code; identical (code, anchor) once."""
    seen: set[tuple[str, tuple[object, ...]]] = set()
    out: list[Finding] = []
    for f in sorted(findings, key=lambda f: f.sort_key()):
        key = (f.code, f.anchor.key())
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def _locator_anchor(b: Binding, loc: Locator) -> Anchor:
    return Anchor("locator", id=b.id, path=loc.path, symbol=loc.symbol)


def _field_anchor(b: Binding, name: str) -> Anchor:
    return Anchor("field", id=b.id, field=name)


def _assertion_anchor(b: Binding, a: Assertion) -> Anchor:
    return Anchor("assertion", id=b.id, path=a.path, symbol=a.symbol, arm=a.arm, owed=a.owed)


class _Rules:
    def __init__(self, check_paths: bool, root: str, *, input_mode: bool = False) -> None:
        self.check_paths = check_paths
        self.root = root
        self.input_mode = input_mode
        self.findings: list[Finding] = []

    def add(
        self, code: str, anchor: Anchor, message: str, line: int | None, severity: str = "error"
    ) -> None:
        self.findings.append(Finding(code, severity, anchor, message, line))

    # -- scalar rules -------------------------------------------------------------

    def scalar(
        self,
        value: str | None,
        what: str,
        anchor: Anchor,
        line: int | None,
        *,
        empty_owned_elsewhere: bool = False,
    ) -> None:
        """INV-SYMBOL-NONEMPTY on one scalar. DICT: INV-SYMBOL-NONEMPTY"""
        if value is None:
            return
        if value == "" and not empty_owned_elsewhere:
            self.add("INV-SYMBOL-NONEMPTY", anchor, f"{what} is empty", line)
        if has_control_chars(value):
            self.add(
                "INV-SYMBOL-NONEMPTY",
                anchor,
                f"{what} contains a control character; scalars are single-line",
                line,
            )

    def path(self, value: str, anchor: Anchor, line: int | None) -> None:
        """DICT: INV-PATH-FORM / INV-NO-LINE-NUMBERS / INV-PATH-EXISTS"""
        if LINE_SUFFIX_RE.search(value):
            self.add(
                "INV-NO-LINE-NUMBERS",
                anchor,
                f"path `{value}` ends in a line number; use a symbol instead",
                line,
            )
            return
        problem = path_form_problem(value)
        if problem is not None:
            self.add("INV-PATH-FORM", anchor, f"`{value}`: {problem}", line)
            return
        self.scalar(value, "path", anchor, line, empty_owned_elsewhere=True)
        if self.check_paths and not has_control_chars(value):
            if not os.path.exists(os.path.join(self.root, value)):
                self.add(
                    "INV-PATH-EXISTS",
                    anchor,
                    f"path `{value}` does not exist relative to the working directory",
                    line,
                )

    def symbol(self, value: str | None, anchor: Anchor, line: int | None) -> None:
        if value is None:
            return
        if LINE_SUFFIX_RE.search(value):
            self.add("INV-NO-LINE-NUMBERS", anchor, f"symbol `{value}` ends in a line number", line)
        self.scalar(value, "symbol", anchor, line)

    # -- comments --------------------------------------------------------------------

    def comment(self, text: str | None, anchor: Anchor, line: int | None) -> None:
        """DICT: INV-COMMENT-TEXT"""
        if text is None:
            return
        lines = text.split("\n")
        if all(s == "" for s in lines):
            self.add("INV-COMMENT-TEXT", anchor, "comment is empty", line)
        elif lines[0] == "" or lines[-1] == "":
            self.add("INV-COMMENT-TEXT", anchor, "comment begins or ends with an empty line", line)
        if has_control_chars(text.replace("\n", "")):
            self.add("INV-COMMENT-TEXT", anchor, "comment contains a control character", line)
        elif self.input_mode and any(s != s.rstrip(" ") for s in lines):
            self.add("INV-COMMENT-TEXT", anchor, "comment line has trailing whitespace", line)

    # -- entities ----------------------------------------------------------------------

    def locator(self, b: Binding, loc: Locator) -> None:
        anchor = _locator_anchor(b, loc)
        self.path(loc.path, anchor, loc.line)
        self.symbol(loc.symbol, anchor, loc.line)
        self.comment(loc.comment, anchor, loc.line)

    def field(self, b: Binding, name: str, fl: FieldLocator) -> None:
        anchor = _field_anchor(b, name)
        if name == "":
            self.add("INV-FIELD-NAME", anchor, "field name is empty", fl.line)
        elif has_control_chars(name):
            self.add(
                "INV-SYMBOL-NONEMPTY",
                anchor,
                f"field name `{name!r}` contains a control character",
                fl.line,
            )
        self.path(fl.path, anchor, fl.line)
        self.symbol(fl.symbol, anchor, fl.line)
        self.comment(fl.comment, anchor, fl.line)

    def assertion(self, b: Binding, a: Assertion) -> None:
        """DICT: INV-ASSERTION-SHAPE"""
        anchor = _assertion_anchor(b, a)
        bound = [a.path is not None, a.symbol is not None, a.run is not None]
        if a.owed is not None and any(bound):
            self.add(
                "INV-ASSERTION-SHAPE",
                anchor,
                "assertion mixes the owed shape with path/symbol/run",
                a.line,
            )
        elif a.owed is None and not all(bound):
            missing = [
                k
                for k, present in zip(("path", "symbol", "run"), bound, strict=True)
                if not present
            ]
            self.add(
                "INV-ASSERTION-SHAPE",
                anchor,
                "bound assertion is missing " + ", ".join(f"`{k}`" for k in missing),
                a.line,
            )
        if a.path is not None:
            self.path(a.path, anchor, a.line)
        self.symbol(a.symbol, anchor, a.line)
        self.scalar(a.run, "run", anchor, a.line)
        self.scalar(a.arm, "arm", anchor, a.line)
        self.scalar(a.owed, "owed", anchor, a.line)
        self.comment(a.comment, anchor, a.line)

    def binding(self, b: Binding) -> None:
        anchor = Anchor("binding", id=b.id)
        self.comment(b.comment, anchor, b.line)
        self.scalar(b.compare_via, "compare_via", anchor, b.line)
        seen_loc: set[tuple[str, str | None]] = set()
        for loc in b.locators:
            self.locator(b, loc)
            if loc.identity() in seen_loc:
                self.add(
                    "INV-LOCATOR-UNIQUE",
                    _locator_anchor(b, loc),
                    f"duplicate locator {loc.path}#{loc.symbol or ''}",
                    loc.line,
                )
            seen_loc.add(loc.identity())
        if b.fields is not None:
            if not b.fields:
                self.add("INV-FIELD-NAME", anchor, "`fields` is present but empty", b.line)
            for name, fl in b.fields.items():
                self.field(b, name, fl)
        if b.wire is not None:
            if b.wire.is_empty():
                self.add(
                    "INV-WIRE-SUBSET",
                    anchor,
                    "`wire` is present but has none of casing/enums/dates",
                    b.wire.line,
                )
            for key, val in (
                ("casing", b.wire.casing),
                ("enums", b.wire.enums),
                ("dates", b.wire.dates),
            ):
                self.scalar(val, f"wire.{key}", anchor, b.wire.line)
        elif any(loc.role is not None for loc in b.locators):
            self.add(
                "INV-ROLE-REQUIRES-WIRE",
                anchor,
                "a locator carries `role` but the binding has no `wire` block",
                b.line,
                "warning",
            )
        if b.asserted_by is not None:
            if not b.asserted_by:
                self.add(
                    "INV-ASSERTION-SHAPE", anchor, "`asserted_by` is present but empty", b.line
                )
            seen_a: set[tuple[object, ...]] = set()
            for a in b.asserted_by:
                self.assertion(b, a)
                if a.identity() in seen_a:
                    self.add(
                        "INV-ASSERTION-UNIQUE",
                        _assertion_anchor(b, a),
                        "duplicate assertion identity",
                        a.line,
                    )
                seen_a.add(a.identity())

    def coverage(self, m: Map) -> None:
        """DICT: INV-COVERAGE-WELLFORMED"""
        cov = m.coverage
        if cov is None:
            return
        anchor = Anchor("coverage")
        self.comment(cov.comment, anchor, cov.line)
        if cov.fully_bound is None and cov.curated is None:
            self.add(
                "INV-COVERAGE-WELLFORMED",
                anchor,
                "`coverage` is present but has neither fully_bound nor curated",
                cov.line,
            )
        fb = cov.fully_bound or []
        if cov.fully_bound is not None and not fb:
            self.add(
                "INV-COVERAGE-WELLFORMED", anchor, "`fully_bound` is present but empty", cov.line
            )
        seen: set[str] = set()
        for kind in fb:
            if not KIND_RE.match(kind):
                self.add(
                    "INV-COVERAGE-WELLFORMED",
                    anchor,
                    f"`{kind}` is not a kind (expected `[A-Z][A-Z0-9]+`)",
                    cov.line,
                )
            if kind in seen:
                self.add(
                    "INV-COVERAGE-WELLFORMED",
                    anchor,
                    f"`{kind}` is listed twice in fully_bound",
                    cov.line,
                )
            seen.add(kind)
        if cov.curated is not None:
            if not cov.curated:
                self.add(
                    "INV-COVERAGE-WELLFORMED", anchor, "`curated` is present but empty", cov.line
                )
            for kind, entry in cov.curated.items():
                entry_anchor = Anchor("curated", kind=kind)
                self.comment(entry.comment, entry_anchor, entry.line)
                if not KIND_RE.match(kind):
                    self.add(
                        "INV-COVERAGE-WELLFORMED",
                        entry_anchor,
                        f"`{kind}` is not a kind (expected `[A-Z][A-Z0-9]+`)",
                        entry.line,
                    )
                if entry.reason == "":
                    self.add(
                        "INV-COVERAGE-WELLFORMED",
                        entry_anchor,
                        f"curated reason for `{kind}` is empty",
                        entry.line,
                    )
                else:
                    self.scalar(
                        entry.reason,
                        "curated reason",
                        entry_anchor,
                        entry.line,
                        empty_owned_elsewhere=True,
                    )
                if kind in seen:
                    self.add(
                        "INV-COVERAGE-WELLFORMED",
                        entry_anchor,
                        f"`{kind}` appears in both fully_bound and curated",
                        entry.line,
                    )

    def owned_twice(self, m: Map) -> None:
        """DICT: INV-OWNED-TWICE"""
        owners: dict[tuple[str, str | None], list[tuple[Binding, Locator]]] = {}
        for b in m.bindings.values():
            for loc in b.locators:
                owners.setdefault(loc.identity(), []).append((b, loc))
        for members in owners.values():
            ids = [b.id for b, _ in members]
            if len(set(ids)) < 2:
                continue
            for b, loc in members:
                others = ", ".join(i for i in dict.fromkeys(ids) if i != b.id)
                self.add(
                    "INV-OWNED-TWICE",
                    _locator_anchor(b, loc),
                    f"{loc.path}#{loc.symbol or ''} is also a locator of {others} (possible "
                    "owned-twice)",
                    loc.line,
                    "warning",
                )

    def document(self, m: Map) -> None:
        file_anchor = Anchor("file")
        self.comment(m.header_comment, Anchor("header"), 1)
        if m.schema_version != SCHEMA_VERSION:
            found = "missing" if m.schema_version is None else str(m.schema_version)
            self.add(
                "INV-SCHEMA-VERSION",
                file_anchor,
                f"schema_version is {found}; this lspd expects {SCHEMA_VERSION}",
                None,
            )
        for binding_id, b in m.bindings.items():
            if not is_contract_id(binding_id):  # pragma: no cover — the Model screens keys
                self.add(
                    "INV-ID-GRAMMAR", Anchor("binding", id=binding_id), "not a contract ID", b.line
                )
            self.binding(b)
        self.coverage(m)
        self.owned_twice(m)


def validate(m: Map, *, check_paths: bool = False, root: str = ".") -> list[Finding]:
    """The rule pass over a Model (unsorted; combine with the Loader's findings, then finalize)."""
    rules = _Rules(check_paths, root)
    rules.document(m)
    return rules.findings


def validate_input(
    value: Any,
    node: str,
    *,
    binding_id: str = "",
    name: str = "",
    kind: str = "",
    check_paths: bool = False,
    root: str = ".",
) -> list[Finding]:
    """Shape pass then rule pass over a candidate input document (unsorted). Input semantics:
    trailing whitespace in a comment is an error, never a repairable warning."""
    obj, findings = from_input(value, node, binding_id=binding_id, name=name, kind=kind)
    if obj is None:
        return findings
    rules = _Rules(check_paths, root, input_mode=True)
    rules.findings = findings
    host = Binding(id=binding_id)
    if node == "binding":
        rules.binding(obj)
    elif node == "locator":
        rules.locator(host, obj)
    elif node == "field_locator":
        rules.field(host, name, obj)
    elif node == "assertion":
        rules.assertion(host, obj)
    else:
        entry_anchor = Anchor("curated", kind=kind)
        rules.comment(obj.comment, entry_anchor, None)
        rules.scalar(obj.reason, "curated reason", entry_anchor, None, empty_owned_elsewhere=True)
        if obj.reason == "":
            rules.add(
                "INV-COVERAGE-WELLFORMED",
                entry_anchor,
                f"curated reason for `{kind}` is empty",
                None,
            )
    return rules.findings
