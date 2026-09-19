---
artifact: product-doc
role: concern
concern-id: domain-and-data
behavior: core
trigger: always
in-scope-subaspects: [domain-entities-relationships, identifiers, business-invariants-rules, lifecycle-states, persistence-storage-schema, consistency-transactions, migrations-versioning]
current-rung: contract-grade
status: published
version: 1.2.0
---

# Domain & Data — dictum-binder

> One-line: the binding map as a closed data model — the file, its bindings, locators, assertions, coverage declaration, and anchored comments — with the invariants that make one canonical style checkable and the canonical layout that *is* the storage schema.

## Purpose & Scope

Owns the canonical model of everything inside `bindings.yaml` and the rules `CAP-VALIDATE` enforces on it. The **shape** comes from Dictum's `templates/binding-map.template.md` (vendored under `dictum/`); the **rigidity** — closed key sets, canonical layout, comment anchors, the numeric-ID prohibition, `schema_version` — is this product's own. The domain is deliberately closed: what this doc does not define, the map cannot contain.

Enforcement classes used below, because *enforced ≠ checkable* (spec bar): **by-construction** — the store cannot represent the violation; **write-gated** — every `lspd` write refuses to produce the violating state, and every read reports it (a hand edit can still create it, so reads are the backstop); **advisory** — reported as a warning, never blocks.

## Non-goals / Out-of-scope

- `data-classification-tags` — `absent`: the map holds repository-relative paths, code symbols, test titles, and run selectors; no PII, secrets, or sensitive data exist in the product.
- `reference-seed-data` — `absent`: no seed data; test fixtures are Quality & Testing's `test-data-strategy`.
- The manifest, the concern docs, and the code tree are **not** entities of this product (never read). `absent` by the product boundary.
- Which contract **kinds** are code-realisable is not modelled: the tool accepts any kind silently (Product constraint). `absent`.
- No semantic validation of `symbol`, `run`, `compare_via`, or `wire` values: all are opaque non-empty strings. `absent` by decision (Product).
- No schema migration in v1: a `schema_version` other than the binary's is an error, never auto-converted. `deferred` — re-entry at the first `lspd` major bump.

## Requirements

### Domain entities & relationships

One document (`ENTITY-MAP`) holds a mapping of contract ID → binding (`ENTITY-BINDING`). A binding holds zero or more locators (`ENTITY-LOCATOR`), an optional map of field locators (`ENTITY-FIELD-LOCATOR`), an optional wire contract (`ENTITY-WIRE`), zero or more assertions (`ENTITY-ASSERTION`), and an optional `compare_via` string. The document may hold one coverage declaration (`ENTITY-COVERAGE`). Comments (`ENTITY-COMMENT`) attach to anchors: the file header, a binding, a locator, a field locator, an assertion, the coverage block, or one curated entry. Validation produces findings (`ENTITY-FINDING`) whose code is the violated invariant's ID.

Two value types carry the identifier contracts: `ENTITY-CONTRACT-ID` (the map key) and `ENTITY-PATH` (a locator path).

### Identifiers

- **Contract ID** — Dictum's grammar `[A-Z][A-Z0-9]+(-[A-Z0-9]+)+` (Part 5), **narrowed**: no segment may consist entirely of digits. `CAP-003` is rejected; `API-V2-USERS` and `SCREEN-3D` are accepted. Full regex in `INV-ID-GRAMMAR`. The **kind** is the first segment. A dotted member suffix (`ENTITY-ORDER.status`) is never a key; members live under `fields`.
- **Locator identity** within a binding: the pair (`path`, `symbol`), where `symbol` may be absent. Ordinal position is never an identity.
- **Assertion identity** within a binding: (`path`, `symbol`, `arm`) for a bound assertion; (`owed`, `arm`) for an owed one.
- **Field identity**: the field name (mapping key).
- **Comment identity**: its anchor.
- No UUIDs, no surrogate keys, no derived keys exist in this product.

### Business invariants / rules

Stated as checkable conditions in Contracts (`INV-*`). Summary by theme: identity and grammar (`INV-ID-GRAMMAR`, `INV-ID-UNIQUE`), version (`INV-SCHEMA-VERSION`), closed shape (`INV-CLOSED-KEYS`, `INV-NO-LINE-NUMBERS`, `INV-PATH-FORM`, `INV-SYMBOL-NONEMPTY`, `INV-ROLE-VALUES`, `INV-WIRE-SUBSET`, `INV-ASSERTION-SHAPE`, `INV-FIELD-NAME`, `INV-COVERAGE-WELLFORMED`), uniqueness inside a binding (`INV-LOCATOR-UNIQUE`, `INV-ASSERTION-UNIQUE`), comments (`INV-COMMENT-ANCHORED`, `INV-COMMENT-TEXT`), bytes (`INV-BYTES`), the opt-in path check (`INV-PATH-EXISTS`), the two template hygiene rules kept advisory (`INV-ROLE-REQUIRES-WIRE`, `INV-OWNED-TWICE`), and the tool's behavioural guarantees over the data (`INV-CANONICAL-FIXPOINT`, `INV-ORDER-PRESERVED`, `INV-ATOMIC-WRITE`).

### Lifecycle & states

- **Map**: *nonexistent* → `init` → *initialised* (empty `bindings`) → writes → *populated*. Any state → `format` → *canonical* (a fixpoint). Deletion is the owner's, never the tool's.
- **Binding**: created by `set` as *stub* (`locators: []`) or *bound*; *stub* ↔ *bound* via `add-locator` / `remove --locator` (removing the last locator yields the stub, not an error); *removed* by `remove <ID>` (the retirement path).
- **Assertion**: *owed* (has `owed`, no triple) → *bound* (has `path`, `symbol`, `run`, no `owed`). The transition is `remove` of the owed entry plus `add-assertion` of the bound one; there is no in-place promotion.
- **Comment**: *absent* → `comment set` → *present* → `comment unset` → *absent*. Setting an empty string is an error, not a removal.
- **Coverage**: *absent* (key omitted) ↔ *declared*; each kind entry set or unset individually.

### Persistence / storage schema

The storage is one UTF-8 YAML file; its **canonical layout** is the schema. `format` produces exactly this; every other write preserves the existing order and appends.

```yaml
# Optional header comment block (anchor: header). Any number of lines, each "# ".
schema_version: 1

bindings:

  ENTITY-PROJECT:
    locators:
      - { path: src/models/project.py, symbol: Project, role: producer }
      - { path: web/src/types/project.ts, symbol: Project, role: consumer }
    wire:
      casing: camelCase
      enums: string-names
      dates: iso-8601-utc

  # Optional comment block above a binding (anchor: binding ENTITY-USER).
  ENTITY-USER:
    locators:
      - { path: src/models/user.py, symbol: User } # trailing single-line comment (anchor: locator)
      - { path: db/schema.sql, symbol: users }
    compare_via: openapi
    fields:
      email: { path: src/models/user.py, symbol: User.email }
      config: { path: config/user.toml } # path-only field locator is legal
    wire:
      casing: camelCase
    asserted_by:
      - { path: tests/test_user.py, symbol: test_email_unique, run: "python3 -m pytest tests/test_user.py::test_email_unique" }
      - { path: tests/test_user.py, symbol: test_email_case, run: "python3 -m pytest -k test_email_case", arm: b }
      - { owed: slice-9 } # owed assertion: no path/symbol/run
      - { arm: c, owed: slice-9 }

  ROUTE-HOME:
    locators:
      - { path: web/src/app.routes.ts } # path-only locator is legal

  # A stub binding (the planner's build-new signal).
  SCREEN-STUB:
    locators: []

# Optional comment block above coverage (anchor: coverage).
coverage:
  fully_bound: [ENTITY, INV, ROUTE]
  curated:
    # Optional comment above a curated entry (anchor: curated API).
    API: "state-changing endpoints bound; simple reads realised but not indexed (locus: src/routes/)"
```

Layout rules (all part of the contract):

- **Top-level order**: header comment, `schema_version`, `bindings`, `coverage`. `coverage` is omitted when it would be empty. `bindings` is `{}` when empty. **Blank lines**: exactly one after the `schema_version` line, one after `bindings:` when it has entries, one between bindings and one before `coverage:` (when the anchor carries a comment block, the blank line precedes the block, since the block must be contiguous with its anchor); none after `bindings: {}` (so an empty map with coverage reads `bindings: {}`, blank line, `coverage:`); the file ends with exactly one LF and no blank line. The canonical empty map is therefore the bytes `schema_version: 1\n\nbindings: {}\n`.
- **Key order in a binding**: `locators`, `compare_via`, `fields`, `wire`, `asserted_by`; absent keys are omitted, never written empty (except `locators: []`, the stub).
- **Key order in a locator**: `path`, `symbol`, `role`. In an assertion: `path`, `symbol`, `run`, `arm`, `owed`. In `wire`: `casing`, `enums`, `dates`. In `coverage`: `fully_bound`, `curated`.
- **Flow style** for every locator, field locator, and assertion: one line, `{ ` … ` }` with a space inside each brace, `, ` between pairs, no line-width wrapping. `fully_bound` is a flow sequence `[ENTITY, INV]` — `[`, items joined by `, `, `]`, no inner padding. Block style for everything else.
- **Indentation** two spaces; one blank line between bindings; no trailing whitespace.
- **Quoting** (applies to values **and mapping keys** alike, so a field name like `my field` is quoted): a scalar is written plain unless any trigger holds, then double-quoted with JSON-style escapes: it contains whitespace; it contains any of `, [ ] { } # :` anywhere; its first character is any YAML c-indicator (`- ? : , [ ] { } # & * ! | > ' " % @ \``); it is empty; or, written plain, it would resolve to a non-string in the YAML 1.2 core schema (`true`, `false`, `null`, `~`, integers incl. `0x`/`0o` forms, floats incl. `1e3`/`.inf`/`.nan`, and any all-digit token such as an `arm: 1`); or — the deterministic superset that also covers ruamel.yaml's round-trip resolver (dates `2026-09-18`, timestamps, `1_000`, `0b101`, verified on 0.19.1) — its first character is a digit, `.`, `+`, `_`, or a `-` followed by a digit. Inside double quotes the only escapes are `\"` and `\\`; every other character, non-ASCII included, is written raw. "Whitespace" means U+0020 (tab and other control characters are banned outright). Binding IDs and kinds never trigger. `run` selectors and multi-word test titles are therefore quoted; a bare symbol or path is not. Scalars are single-line by invariant (`INV-SYMBOL-NONEMPTY`), so no folding or escaping of newlines ever occurs in the file.
- **Trailing-comment padding**: exactly one space between the entry's closing `}` (or the value) and the `#` of a trailing comment; no column alignment. A block comment above a flow-line anchor (locator, field, assertion) is indented to that anchor's own column; a block comment above a binding, coverage, or curated line likewise takes that line's column. A comment line is `#` followed by one space and the text, or a bare `#` for an empty line of a multi-line comment.
- **Canonical order** (applied by `format` only): bindings sorted lexically by the full ID string in byte order; `fully_bound` sorted lexically; `curated` entries sorted lexically by kind. Locators, assertions, and `fields` keep the author's order under `format` (locator order can carry meaning, e.g. producer before consumer) — confirmed by the operator 2026-09-17.
- **Comment carriers** (how a comment attaches; the Loader derives anchors from **line adjacency in the source bytes** using the parser's comment tokens and positions, never the YAML library's own attachment): a **header** comment is the block contiguous with the first content line, whatever that line is (a `---` document marker or a `%YAML` directive line is transparent for contiguity and is never emitted); a **binding**, **coverage**, or **curated** comment is either a block contiguous above its anchor line **or** a trailing comment on that anchor line itself (both accepted on read; written as a block above); a **locator**, **field**, or **assertion** comment is either trailing on the entry's line or a block contiguous above it (both accepted; on write a single-line comment is emitted trailing, a multi-line one above — so `comment set` with single-line text on an entry that had a block moves it trailing). A block-style entry written by hand (`- path: x` / `  symbol: y`) is loadable; a trailing comment on its **last** line attaches to the entry; a comment on an inner line, or between an entry's lines, is unattachable. **Unattachable** — a trailing comment on any non-anchor line (`schema_version:`, `locators:`, `compare_via:`, `wire:`, `casing:`, `fully_bound:` …), a block separated from the next line by a blank line, or a block after the last content line — makes the file unloadable (`ERR-PARSE`); the Loader never relocates a comment. Two carriers on one anchor is the error-level finding `INV-COMMENT-ANCHORED`; the Model then carries the block-above text (so `get` and `comment get` show it) and no write can persist it. Column is ignored on read. Comment text is stored without the leader: `#` and **at most one** following space are stripped (`#  x` → ` x`), a `#text` line is accepted as `text` (the one deliberate mild default, 2026-09-17), and an empty line in a block is stored as an empty line and emitted as a bare `#`. Text never carries trailing whitespace and never begins or ends with an empty line (`INV-COMMENT-TEXT`). Any YAML the Model can represent — block or flow style, `---` markers, aliases, tags — is loadable and canonicalised by `format`; only what the Model cannot hold is a finding, and only what cannot be parsed or anchored is `ERR-PARSE`.
- **Layout-class deviations** (loadable, harmless to meaning): block instead of flow style, quoting choices, padding, blank-line pattern, missing or extra EOF newline, `#text` leaders, non-canonical binding order, and trailing whitespace. None is an error. Trailing whitespace and EOF-newline deviations are the advisory `INV-BYTES` warning; the rest raise no finding at all. `validate` therefore passes such a file (exit 0 with the warnings), `format --check` reports `changed: true`, and every write — `format` being the one a caller runs when nothing else needs changing — repairs all of them, because the Emitter is the only producer of file bytes. Repairing layout on write is contracted here, not a default: content and order are never touched by it.

### Consistency & transactions

Single writer, single file. A write is: read → pre-validate → **refuse if any error-level finding exists** (`ERR-FILE-INVALID`; warnings are tolerated and reported) → mutate in memory → post-validate → serialise → write to a temporary file in the same directory → `rename` over the target. The original is untouched until the rename; a failure anywhere leaves it byte-identical (`INV-ATOMIC-WRITE`). The temporary file takes the original's permission bits; a file created by `init` takes the process umask default. Concurrent writers are not coordinated (Product non-goal). Because a write never starts from an invalid map, the Model never has to carry shape-violating content: on a read-only command the Loader drops what the Model cannot represent and the findings report it, and nothing lost that way can ever be persisted.

### Migrations & versioning

`schema_version` is a required top-level integer equal to the `lspd` major version that owns the layout; v1 writes `1`. A file whose value differs from the running binary's major fails validation (`INV-SCHEMA-VERSION`, exit 1); every command other than `validate` refuses to proceed with `ERR-SCHEMA-VERSION` (Interfaces), so nothing is ever read from or written to a map of another major. The binary's major is the constant `SCHEMA_VERSION` in `COMPONENT-SCHEMA`, asserted equal to the package version's major by a fitness test; before the first release the package version is `1.0.0.dev0`, so the major is already 1. No migration exists in v1; a future major bump owes one (deferred, Non-goals).

## Open Questions

None open.

## Dependencies & Cross-references

- Consumes `CAP-INIT`, `CAP-VALIDATE`, `CAP-FORMAT`, `CAP-SET`, `CAP-ADD`, `CAP-REMOVE`, `CAP-COVERAGE`, `CAP-COMMENT` (Product) — each lifecycle transition above names the capability that performs it.
- Referenced by Interfaces (the JSON projection of every entity; the command-level `ERR-*` catalog is distinct from finding codes, which are `INV-*` IDs), Quality (one assertion per `INV-*`; golden fixtures realise the canonical layout), Architecture (the Model and Validator components realise these entities).
- The Dictum template (`dictum/templates/binding-map.template.md`) is the upstream shape; the `role`/`wire` forms and the *concepts* of arm-labelled and owed assertions are its (it describes them in comment prose), the `arm:` and `owed:` key forms are ours, and the narrowing is ours.

## Examples / Worked scenarios

1. **Reading a hand-edited file.** A model added `- { path: src/x.py, symbol: f, lines: 40-52 }`. `validate` reports `INV-CLOSED-KEYS` (unknown key `lines`) and `INV-NO-LINE-NUMBERS`, both errors, anchored at `ENTITY-X` locator 2; exit 1. Both findings are error-level, so every `lspd` write is refused (`ERR-FILE-INVALID`) until the model deletes the `lines:` key **by hand**; it then re-runs `validate` (clean) and continues through `lspd`.
2. **Promoting an owed assertion.** `INV-EMAIL-UNIQUE` carries `{ owed: slice-9 }`. Slice 9 lands its test. The agent runs `remove INV-EMAIL-UNIQUE --assertion --owed slice-9` then `add-assertion INV-EMAIL-UNIQUE` with path, symbol, run. A single entry carrying both `owed` and the triple would have been rejected (`INV-ASSERTION-SHAPE`).
3. **Format as a fixpoint.** A populated map in insertion order is formatted: bindings re-sorted, `fields` untouched, every comment still on its anchor, trailing comments re-emitted trailing. A second `format` is a byte-identical no-op (`INV-CANONICAL-FIXPOINT`).
4. **Numeric ID.** A converter emits `CAP-003`. `validate` reports `INV-ID-GRAMMAR` with the message naming the all-digit segment; `API-V2-USERS` in the same file passes.
5. **Two carriers.** A locator has `# old` above it and `# new` trailing. `validate` reports `INV-COMMENT-ANCHORED`; the maintainer deletes one **by hand** — the finding is error-level, so every write, `comment set` included, is refused with `ERR-FILE-INVALID` until it is gone.

## Design Decisions

| Decision | Rationale |
|---|---|
| Finding code = violated `INV-*` ID | One register, owned once; the validator's vocabulary and the domain's rules cannot drift apart |
| Identity by (path, symbol), never ordinal | Ordinals change on every append or remove; a stable identity is what an agent can address after a partial read |
| Path-only locators and field locators allowed | The realising artifact may be any format the interpreter accepts (config, templates, SQL); forcing a symbol would force an invented one |
| `wire` is any non-empty subset of its three keys | A contract with no enum or date field has nothing to declare; a forced `none` is a default in disguise |
| Owed and bound are disjoint assertion shapes | No real case needs both on one entry; a partial test is a bound entry with a comment beside an owed entry |
| Both comment carriers accepted on read, one chosen on write | The template's example uses trailing comments on locator lines, which are accepted; its trailing comments on key lines (`compare_via:`, `wire:`) have no anchor and are rejected as unattachable — a deliberate narrowing of the template, recorded here. Determinism is on the write side |
| Canonical layout fully specified, including quoting and whitespace | The layout is the product; an unspecified byte is a style choice left to the library or the model |
| CRLF or BOM is an error, not normalised | Normalising is a silent default; the operator wants the LLM to fix it explicitly |
| Writes refuse a map with error-level findings | The alternative — carrying shape-violating content opaquely through the Model — would either lose it or make every post-validation re-report it; refusing keeps the Model honest and the write path simple. Warnings never block |
| `#text` accepted as `text` on read | The one mild default: YAML treats `#text` and `# text` as the same comment, so rejecting it would be pedantry, and the rewrite is lossless |

Cross-cutting decisions (single file, structural-only, no line numbers, `schema_version` per major) are ADRs in Architecture.

## Contracts

Register form: table row, ID in the first cell. Types: `str` = non-empty string unless stated; `int`; `list<T>`; `map<K,V>`; `?` = optional.

### Entities

| ID | Definition |
|---|---|
| `ENTITY-MAP` | The document. Fields: `schema_version: int` (required, == binary major); `bindings: map<ENTITY-CONTRACT-ID, ENTITY-BINDING>` (required, may be empty); `coverage: ENTITY-COVERAGE?`; header comment `ENTITY-COMMENT?`. Exactly one per file; one file per invocation |
| `ENTITY-CONTRACT-ID` | Value type. A string matching `INV-ID-GRAMMAR`. Derived property `kind` = the substring before the first `-`. Never carries a dotted member suffix |
| `ENTITY-BINDING` | Keyed by `ENTITY-CONTRACT-ID`. Fields: `locators: list<ENTITY-LOCATOR>` (required; empty list = stub); `compare_via: str?`; `fields: map<str, ENTITY-FIELD-LOCATOR>?` (non-empty when present); `wire: ENTITY-WIRE?`; `asserted_by: list<ENTITY-ASSERTION>?` (non-empty when present); comment `ENTITY-COMMENT?` |
| `ENTITY-LOCATOR` | Fields: `path: ENTITY-PATH` (required); `symbol: str?`; `role: enum{producer, consumer}?`; comment `ENTITY-COMMENT?`. Identity: (`path`, `symbol`) |
| `ENTITY-FIELD-LOCATOR` | Keyed by field name (`str`). Fields: `path: ENTITY-PATH` (required); `symbol: str?`; comment `ENTITY-COMMENT?`. No `role` |
| `ENTITY-WIRE` | Fields: `casing: str?`, `enums: str?`, `dates: str?` — any subset, at least one present, values opaque |
| `ENTITY-ASSERTION` | Exactly one of two shapes. **Bound**: `path: ENTITY-PATH`, `symbol: str` (verbatim test title), `run: str` (selector), `arm: str?`. **Owed**: `owed: str` (slice reference), `arm: str?`. Comment `ENTITY-COMMENT?`. Identity: (`path`, `symbol`, `arm`) or (`owed`, `arm`) |
| `ENTITY-PATH` | Value type. A repository-relative path: one or more segments joined by single `/`; each segment non-empty and neither `.` nor `..`; no leading `/`; no `\`; no drive-letter prefix; no `~`; not whitespace-only; single-line with no control characters (`INV-SYMBOL-NONEMPTY`); no trailing `:digits` (that last case is reported under `INV-NO-LINE-NUMBERS`, never under `INV-PATH-FORM`) |
| `ENTITY-COVERAGE` | Fields: `fully_bound: list<kind>?` (unique members); `curated: map<kind, str>?` (reason, non-empty). `kind` = a string matching the first-segment grammar `[A-Z][A-Z0-9]+`. At least one field present when the block exists |
| `ENTITY-COMMENT` | Fields: `text: str` (one or more lines, stored without the `# ` leader; non-empty, no trailing whitespace on any line — `INV-COMMENT-TEXT`); `anchor: one of header · binding(ID) · locator(ID, path, symbol) · field(ID, name) · assertion(ID, identity) · coverage · curated(kind)`. Identity: the anchor |
| `ENTITY-FINDING` | Output of validation. Fields: `code: INV-* ID`; `severity: enum{error, warning}`; `anchor` (as `ENTITY-COMMENT.anchor`, plus `file` for document-level findings); `message: str`. Not persisted. **Ordering**: findings from the Loader, the shape pass, and the rule pass are merged and sorted by the anchor's source line (document order; `file` anchors first), then by code; identical (code, anchor) pairs are reported once. This order is what the envelope carries |

### Invariants

Each row: the checkable condition · enforcement class · mechanism. Severity is **error** unless marked *advisory* (warning).

| ID | Condition | Enforcement |
|---|---|---|
| `INV-ID-GRAMMAR` | Every key of `bindings` matches `^[A-Z][A-Z0-9]+(-(?![0-9]+(-\|$))[A-Z0-9]+)+$` — Dictum's grammar with no all-digit segment | write-gated; checked on every read |
| `INV-ID-UNIQUE` | Exactly one binding per contract ID | by-construction: a YAML mapping cannot hold a duplicate key; the loader rejects a duplicate as unparseable (exit 2) |
| `INV-SCHEMA-VERSION` | `schema_version` is present, an integer, and equals the running binary's major version (a *missing* or non-integer `schema_version` also violates `INV-CLOSED-KEYS`; both findings are reported, as for `lines:`) | write-gated (`init` writes it; every write re-checks); checked on every read |
| `INV-CLOSED-KEYS` | **Closed shape**: every mapping uses only its defined keys — document {`schema_version`, `bindings`, `coverage`}; binding {`locators`, `compare_via`, `fields`, `wire`, `asserted_by`}; locator {`path`, `symbol`, `role`}; field locator {`path`, `symbol`}; wire {`casing`, `enums`, `dates`}; assertion {`path`, `symbol`, `run`, `arm`, `owed`}; coverage {`fully_bound`, `curated`} — **and** every required key is present (`schema_version`, `bindings`; `locators` in a binding; `path` in a locator or field locator) **and** every value has its contracted type (mappings, lists, strings, the integer `schema_version` — a boolean is not an integer). A missing required key or a wrong type is reported under this code with a message naming the key and the expected type | write-gated; checked on every read |
| `INV-NO-LINE-NUMBERS` | No key named `lines` or `line` anywhere (such a key also violates `INV-CLOSED-KEYS`; **both** findings are reported, this one carrying the precise message), and no `path` or `symbol` ending in `:` followed by digits | write-gated; checked on every read |
| `INV-PATH-FORM` | Every `path` satisfies `ENTITY-PATH` | write-gated; checked on every read |
| `INV-PATH-EXISTS` | *opt-in* — with `--check-paths`, every locator and field-locator `path`, and every candidate `path` in write input, exists on disk relative to the working directory (checked by `stat` only, after `INV-PATH-FORM` has passed). Severity **error**. Never evaluated without the flag | write-gated when the flag is on (a write with a missing path is refused); checked on every read with the flag on |
| `INV-SYMBOL-NONEMPTY` | Every present `symbol` is a non-empty string; every `path`, `fields` key, `run`, `compare_via`, `owed`, `arm`, wire value, and curated reason likewise — and every such scalar is **single-line with no control characters** — C0 (U+0000–U+001F incl. `\n`, `\r`, `\t`), DEL (U+007F), and C1 (U+0080–U+009F; the pinned YAML reader rejects DEL and C1 and folds NEL to a space), so a value carrying a newline from the shell is rejected (`ERR-INPUT-INVALID` carrying this code, from a flag value or from JSON alike — an *empty* flag value is the argument rule `ERR-USAGE`) rather than escaped into the file. **Multiplicity**: an *empty* `path`, `fields` key, or curated reason is reported under `INV-PATH-FORM`, `INV-FIELD-NAME`, or `INV-COVERAGE-WELLFORMED` only, never additionally here; this code owns the control-character arm for those three and the whole rule for every other scalar listed | write-gated; checked on every read |
| `INV-ROLE-VALUES` | Every present `role` is `producer` or `consumer` | write-gated; checked on every read |
| `INV-WIRE-SUBSET` | A present `wire` has at least one of its three keys and nothing else | write-gated; checked on every read |
| `INV-ASSERTION-SHAPE` | Each assertion is exactly bound (`path`, `symbol`, `run` all present, `owed` absent) or exactly owed (`owed` present, the three absent); `arm` optional in both; `asserted_by`, when present, is a non-empty list | write-gated; checked on every read |
| `INV-FIELD-NAME` | Every `fields` key is a non-empty string (single-line, no control characters — `INV-SYMBOL-NONEMPTY`); `fields`, when present, is non-empty | write-gated; checked on every read |
| `INV-COVERAGE-WELLFORMED` | Every kind in `fully_bound` and every `curated` key matches `[A-Z][A-Z0-9]+`; `fully_bound` has no duplicates; no kind appears in both; every curated reason is non-empty; `fully_bound`, when present, is a non-empty list; `curated`, when present, is a non-empty mapping; the block, when present, has at least one field (a present-but-empty `fully_bound`, `curated`, or `coverage` is reported here, not under `INV-CLOSED-KEYS`) | write-gated; checked on every read |
| `INV-LOCATOR-UNIQUE` | Within a binding, no two locators share (`path`, `symbol`) | write-gated (`add-locator` refuses a duplicate); checked on every read |
| `INV-ASSERTION-UNIQUE` | Within a binding, no two assertions share their identity | write-gated; checked on every read |
| `INV-COMMENT-ANCHORED` | Every comment belongs to exactly one anchor per the carrier rules, and no anchor has two carriers. **Boundary with the parse layer** (fixability drives the outcome): a comment the Loader cannot attach to any anchor at all (it sits where no anchor exists) makes the file unloadable → `ERR-PARSE`, exit 2; a loadable file with two carriers on one anchor → this finding, exit 1 | write-gated (the tool only writes at anchors); checked on every read |
| `INV-COMMENT-TEXT` | Every comment's text is **non-empty** and every line of it is free of control characters (C0, DEL U+007F, and C1 U+0080–U+009F — the same definition as `INV-SYMBOL-NONEMPTY` — a CR written verbatim would make the file unloadable on the next read) — a bare `#` as a whole comment, a block consisting only of bare `#` lines, or a block whose first or last line is empty all count as empty — whatever channel supplied it: an empty `--text`/`--comment` flag value (rejected as `ERR-USAGE`, the empty-argument rule), a flag value or `set --json` comment string that is empty (`""` in JSON), all empty lines, begins or ends with one, or contains a control character (rejected as `ERR-INPUT-INVALID` carrying this code), or a file. **Error** severity for emptiness. A comment line with trailing whitespace **in the file** is the **advisory** arm of this invariant (a warning, also reported under `INV-BYTES`; any write repairs it); the same text **supplied as input** is rejected (`ERR-INPUT-INVALID` carrying this code), because the Emitter would otherwise have to normalise the caller's input silently | write-gated for emptiness and for control characters (a trailing tab is a control character first, so the write-gated arm wins); advisory for trailing plain whitespace; checked on every read |
| `INV-BYTES` | *advisory* — The file is UTF-8 without BOM, LF line endings only, no trailing whitespace on any line, ending with exactly one LF. **Boundary with the parse layer** (fixability drives the outcome): non-UTF-8 bytes, a BOM, or CRLF make the file unloadable → `ERR-PARSE`, exit 2, never normalised; trailing whitespace or a missing/extra EOF newline on a loadable file → this **warning**, exit 0, repaired by `format` (a layout-class deviation) | advisory: warning on read and after write; the Emitter never produces a violation |
| `INV-ROLE-REQUIRES-WIRE` | *advisory* — a binding with any `role` on a locator has a `wire` block (template hygiene rule) | advisory: warning on read and after write |
| `INV-OWNED-TWICE` | *advisory* — no (`path`, `symbol`) pair appears as a locator under two different contract IDs (template hygiene rule) | advisory: warning on read and after write |
| `INV-CANONICAL-FIXPOINT` | For any loadable map `m`, `format(format(m)) == format(m)` byte-for-byte; for a map already in canonical layout, `dump(load(m)) == m` | tool property, asserted by golden tests (Quality); not a store constraint |
| `INV-ORDER-PRESERVED` | Every write other than `format` leaves the relative order of all existing bindings, locators, fields, assertions, and coverage entries unchanged, and places a new entry last in its list | tool property, asserted by contract tests (Quality) |
| `INV-ATOMIC-WRITE` | After any write attempt the target file is either byte-identical to its pre-write content or the complete post-validated new content; never partial | by-construction: temporary file + `rename` in the same directory |

### Finding anchors

Each invariant's finding is anchored as follows (`OUT-ANCHOR` in Interfaces is the projection; unmentioned keys are `null`). Codes sit in the last column: this is a reference table, not a register. A `file` anchor carries no `path` (the target's path is not an `ENTITY-PATH`); a `field` anchor carries `id` and `field` only.

| Anchor | Finding code(s) |
|---|---|
| `binding` with `id` = the offending key string | `INV-ID-GRAMMAR` |
| n/a — `ERR-PARSE` | `INV-ID-UNIQUE` |
| `file` | `INV-SCHEMA-VERSION` |
| the innermost anchor that exists: `locator`/`field`/`assertion` for a key or value inside an entry, `binding` for a key or value directly under the binding (incl. anything under `wire`), `coverage`/`curated(K)` inside the coverage block, `file` at the top level | `INV-CLOSED-KEYS`, `INV-NO-LINE-NUMBERS`, `INV-SYMBOL-NONEMPTY` |
| the `locator` or `field` carrying the path | `INV-PATH-FORM`, `INV-PATH-EXISTS` |
| the `locator` | `INV-ROLE-VALUES` |
| `binding` | `INV-WIRE-SUBSET` |
| the `assertion`, with whichever of `path`/`symbol`/`arm`/`owed` are present and `null` for the rest | `INV-ASSERTION-SHAPE` |
| `field` with the offending name (`""` when empty); `binding` when `fields` itself is empty | `INV-FIELD-NAME` |
| `curated(K)` for a per-entry rule (empty reason, kind in both lists — reported once, at the curated entry); `coverage` for every other rule | `INV-COVERAGE-WELLFORMED` |
| one finding per duplicate occurrence after the first, at that occurrence's anchor | `INV-LOCATOR-UNIQUE`, `INV-ASSERTION-UNIQUE` |
| the anchor the comment belongs to | `INV-COMMENT-ANCHORED`, `INV-COMMENT-TEXT` |
| `binding` | `INV-ROLE-REQUIRES-WIRE` |
| one finding per participating binding, at its `locator`, the message naming every other binding sharing the pair | `INV-OWNED-TWICE` |
| `file` — the message cites the line number (allowed by `ADR-NO-LINE-NUMBERS` for diagnostics) | `INV-BYTES` |
| tool properties; never findings | `INV-CANONICAL-FIXPOINT`, `INV-ORDER-PRESERVED`, `INV-ATOMIC-WRITE` |

## Acceptance criteria

1. One assertion per `INV-*` (Quality's coverage map): each write-gated invariant has a synthetic fixture that violates it, and `validate` reports exactly that finding code at the anchor the *Finding anchors* table names, exit 1; each advisory one (`INV-ROLE-REQUIRES-WIRE`, `INV-OWNED-TWICE`, `INV-BYTES`, the trailing-whitespace arm of `INV-COMMENT-TEXT`) reports a warning with exit 0. The unloadable halves of `INV-BYTES` (BOM, CRLF, non-UTF-8) and `INV-COMMENT-ANCHORED` (no anchor exists) are `ERR-PARSE` forcings with exit 2 instead.
2. Grammar table for `INV-ID-GRAMMAR`: a table-driven test with at least `CAP-003` (reject), `API-V2-USERS` (accept), `SCREEN-3D` (accept), `cap-003` (reject), `CAP` (reject), `ENTITY-ORDER.status` (reject).
3. Duplicate-key fixture for `INV-ID-UNIQUE`: a fixture with a duplicated key fails to load with exit 2.
4. Fixpoint tests for `INV-CANONICAL-FIXPOINT`: for every public fixture and every synthetic fixture, `format` twice equals `format` once; for the canonical golden fixture, load-then-dump is byte-identical.
5. Order-preservation diffs for `INV-ORDER-PRESERVED`: a contract test appends via each `add-*` and `set` on a multi-binding **canonical** fixture and asserts the diff is limited to the appended lines (every write re-emits the whole file, so on a non-canonical fixture the diff also carries the layout repair; order is still preserved and a second test asserts that).
6. Injected-failure test for `INV-ATOMIC-WRITE`: a test that makes the rename fail after the temporary file is written and asserts the target is byte-identical to its original and no temporary file remains.
7. Anchor fixtures for `INV-COMMENT-ANCHORED`: fixtures for each of the seven anchor kinds round-trip; a fixture with two carriers on one anchor produces the finding (exit 1); a fixture with a comment where no anchor exists is `ERR-PARSE` (exit 2).
8. The canonical example in *Persistence* is itself a golden fixture: it validates clean and is a `format` fixpoint (bindings in byte order, comments only at anchors, quoting and padding per the rules above).
9. Opt-in path fixture for `INV-PATH-EXISTS`: a fixture with one missing path passes without `--check-paths` and fails with it; `add-locator` of a missing path is refused only with the flag.

