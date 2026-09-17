---
artifact: product-doc
role: concern
concern-id: domain-and-data
behavior: core
trigger: always
in-scope-subaspects: [domain-entities-relationships, identifiers, business-invariants-rules, lifecycle-states, persistence-storage-schema, consistency-transactions, migrations-versioning]
current-rung: sketch
status: draft
version: 0.1.0
---

# Domain & Data — dictum-binder

> One-line: the binding map as a data model — the file, its bindings, locators, assertions, coverage declaration, and anchored comments — with the invariants that make one canonical style checkable.
<!-- BUILD: Read ../dictum/concerns/11.2-domain-and-data.md. Next rung: Specified — full entity prose + identifier rules; Contract-grade — ENTITY-### and INV-### register lines with checkable predicates. -->

## Purpose & Scope

Owns the canonical model of everything inside `bindings.yaml` and the rules the tool enforces on it. The **shape** comes from Dictum's `templates/binding-map.template.md` (vendored under `dictum/`); the **rigidity** — closed key sets, canonical layout, comment anchors — is this product's own contribution. The domain is deliberately closed: what the template does not have, the map does not have.

## Non-goals / Out-of-scope

- `data-classification-tags` — `absent`: the map holds repository-relative paths, code symbols, test titles, and run selectors; no PII, secrets, or sensitive data exist in the product.
- `reference-seed-data` — `absent`: no seed data; test fixtures are Quality & Testing's `test-data-strategy`.
- The manifest, the concern docs, and the code tree are **not** entities of this product (they are never read). `absent` by the product boundary.

## Requirements

<!-- BUILD: Sketch outline. -->

**Entities (candidates)**
- *Binding map* — one file, one document: a `bindings` mapping plus an optional `coverage` declaration, plus comments.
- *Contract ID* — value type; the map key. Grammar is normative (Dictum Part 5): `[A-Z][A-Z0-9]+(-[A-Z0-9]+)+`, case-significant; **kind** = first segment.
- *Binding* — keyed by contract ID; holds `locators` (list), optional `fields` (name → locator), optional `wire`, optional `asserted_by` (list), optional `compare_via`. The stub form `locators: []` is legal (the planner's build-new signal).
- *Locator* — `path` + `symbol`, optional `role` ∈ {`producer`, `consumer`}.
- *Field locator* — `path` + `symbol`, keyed by field name under `fields`.
- *Wire contract* — `casing`, `enums`, `dates`.
- *Assertion* — `path` + `symbol` (verbatim test title) + `run` (selector string), optional `arm` (verbatim arm token), optional `owed` (slice reference for a deferred assertion).
- *Coverage declaration* — `fully_bound` (list of kinds) and `curated` (kind → reason naming a locus).
- *Comment* — text attached to exactly one **anchor**: file header, a binding, a single locator or assertion line, or a coverage entry.
- *Finding* — the output of validation: severity (error | warning), a stable code, the location (ID, anchor), a message.

**Identifiers**
- A binding is identified by its contract ID; a locator by (binding, ordinal position) and by (path, symbol) for owned-twice detection; a field by (binding, field name); an assertion by (binding, ordinal); a comment by its anchor.

**Invariants (candidates, checkable at Contract-grade)**
- Every key under `bindings` conforms to the ID grammar; exactly one binding per ID.
- Every mapping uses only its closed key set; unknown keys are errors.
- `path` and `symbol` are non-empty strings; `path` is repository-relative with forward slashes.
- **No line numbers**: no `lines`/`line` key, and no `path` or `symbol` carrying a `:NNN` line suffix.
- A `role` on any locator requires a `wire` block on that binding (else a hygiene warning, per the template).
- Every assertion has `run`; a deferred assertion carries `owed` and may omit nothing else the schema requires. <!-- BUILD: decide at Specified whether an owed assertion may omit run/symbol. -->
- One (path, symbol) realising two different contract IDs is an owned-twice warning.
- Comments exist only at anchors.
- `format` is idempotent; every other write preserves existing order and appends new entries at the end.

**Lifecycle & states**
- Map: absent → initialised (empty) → populated → formatted; deletion is the user's, not the tool's.
- Binding: stubbed (`locators: []`) → bound → removed (on contract retirement, by the caller's instruction).
- Assertion: owed → bound.

**Persistence / storage schema**
- A single UTF-8 YAML file; the canonical layout follows the template's key order (`bindings` then `coverage`; within a binding `locators`, `compare_via`, `fields`, `wire`, `asserted_by`). Locators and assertions are written in flow style on one line as the template shows.

**Consistency & transactions**
- Single writer, single file: a write is validate → mutate in memory → validate → atomic replace (write to a temporary file, then rename). A failed post-validation never leaves a partial file.

**Migrations & versioning**
- The schema tracks the Dictum template. `[GAP]` whether the file carries a schema-version field is unanswered (see Product).

## Open Questions

- `[GAP]` Schema-version field in the file (see above).
- `[GAP]` `wire` and `compare_via` value vocabularies: open or pinned (owned by Product until decided).
- `[GAP]` Exact comment relocation rule for a comment found between anchors on read: nearest preceding anchor, nearest following, or reject?
- `[GAP]` May an `owed` assertion omit `run` and `symbol` (nothing to run yet), or must it carry placeholders?

## Dependencies & Cross-references
<!-- BUILD: rung Specified — Product capabilities; Interfaces consumes ENTITY/INV for I/O projections and the finding envelope. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified — a dual-realisation binding with wire; a multi-arm INV with one asserted_by per arm plus one owed. -->

## Design Decisions
<!-- BUILD: rung Specified — closed domain; comment as first-class entity; no line numbers. -->

## Contracts
<!-- BUILD: rung Contract-grade — ENTITY-### and INV-### register lines. -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade — one assertion per INV. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
