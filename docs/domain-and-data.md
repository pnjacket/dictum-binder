---
artifact: product-doc
role: concern
concern-id: domain-and-data
behavior: core
trigger: always
in-scope-subaspects: [domain-entities-relationships, identifiers, business-invariants-rules, lifecycle-states, persistence-storage-schema, consistency-transactions, migrations-versioning]
current-rung: contract-grade
status: draft
version: 1.1.0
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

Stated as checkable conditions in Contracts (`INV-*`). Summary by theme: identity and grammar (`INV-ID-GRAMMAR`, `INV-ID-UNIQUE`), version (`INV-SCHEMA-VERSION`), closed shape (`INV-CLOSED-KEYS`, `INV-NO-LINE-NUMBERS`, `INV-PATH-FORM`, `INV-SYMBOL-NONEMPTY`, `INV-ROLE-VALUES`, `INV-WIRE-SUBSET`, `INV-ASSERTION-SHAPE`, `INV-FIELD-NAME`, `INV-COVERAGE-WELLFORMED`), uniqueness inside a binding (`INV-LOCATOR-UNIQUE`, `INV-ASSERTION-UNIQUE`), comments (`INV-COMMENT-ANCHORED`), bytes (`INV-BYTES`), the opt-in path check (`INV-PATH-EXISTS`), the two template hygiene rules kept advisory (`INV-ROLE-REQUIRES-WIRE`, `INV-OWNED-TWICE`), and the tool's behavioural guarantees over the data (`INV-CANONICAL-FIXPOINT`, `INV-ORDER-PRESERVED`, `INV-ATOMIC-WRITE`).

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
      - { owed: slice-9, arm: c }

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

- **Top-level order**: header comment, `schema_version`, `bindings`, `coverage`. `coverage` is omitted when it would be empty. `bindings` is `{}` when empty.
- **Key order in a binding**: `locators`, `compare_via`, `fields`, `wire`, `asserted_by`; absent keys are omitted, never written empty (except `locators: []`, the stub).
- **Key order in a locator**: `path`, `symbol`, `role`. In an assertion: `path`, `symbol`, `run`, `arm`, `owed`. In `wire`: `casing`, `enums`, `dates`. In `coverage`: `fully_bound`, `curated`.
- **Flow style** for every locator, field locator, and assertion: one line, `{ ` … ` }` with a space inside each brace, `, ` between pairs, no line-width wrapping. Block style for everything else.
- **Indentation** two spaces; one blank line between bindings; no trailing whitespace.
- **Quoting**: a scalar is written plain unless it contains whitespace or YAML flow-context rules require quoting (it contains `,` `{` `}` `[` `]` `:` followed by space, `#`, leading/trailing space, or starts with a YAML indicator); then double quotes. `run` selectors and multi-word test titles are therefore quoted; a bare symbol or path is not.
- **Trailing-comment padding**: exactly one space between the entry's closing `}` (or the value) and the `#` of a trailing comment; no column alignment. A comment line is `#` followed by one space and the text, or a bare `#` for an empty line of a multi-line comment.
- **Canonical order** (applied by `format` only): bindings sorted lexically by the full ID string in byte order; `fully_bound` sorted lexically; `curated` entries sorted lexically by kind. Locators, assertions, and `fields` keep the author's order under `format` (locator order can carry meaning, e.g. producer before consumer) — confirmed by the operator 2026-09-17.
- **Comment carriers**: a header, binding, coverage, or curated comment is a block of `# ` lines directly above its anchor line. A locator, field, or assertion comment is either trailing on the flow line or a block directly above it — both accepted on read; on write a single-line comment is emitted trailing, a multi-line one above. A comment anywhere else, or two carriers on one anchor, is an error (`INV-COMMENT-ANCHORED`). Comment text is stored without the `# ` leader; an empty line inside a multi-line comment is stored as an empty line and emitted as a bare `#`; text never carries trailing whitespace (`CLI-COMMENT-SET` rejects it). On read, a comment line written `#text` with no space after `#` is accepted as the text `text` and re-emitted as `# text` — the one **deliberate mild default** in the model (operator's call, 2026-09-17), because YAML itself treats both forms as the same comment.

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
2. **Promoting an owed assertion.** `INV-EMAIL-UNIQUE` carries `{ owed: slice-9 }`. Slice 9 lands its test. The agent runs `remove INV-EMAIL-UNIQUE --assertion owed=slice-9` then `add-assertion INV-EMAIL-UNIQUE` with path, symbol, run. A single entry carrying both `owed` and the triple would have been rejected (`INV-ASSERTION-SHAPE`).
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
| Both comment carriers accepted on read, one chosen on write | The template itself uses trailing comments; rejecting them would reject the template. Determinism is on the write side |
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
| `ENTITY-PATH` | Value type. A repository-relative path: non-empty, `/` separators only, no leading `/` or `./`, no `..` segment, no drive letter, no trailing `:digits` (that last case is reported under `INV-NO-LINE-NUMBERS`, never under `INV-PATH-FORM`) |
| `ENTITY-COVERAGE` | Fields: `fully_bound: list<kind>?` (unique members); `curated: map<kind, str>?` (reason, non-empty). `kind` = a string matching the first-segment grammar `[A-Z][A-Z0-9]+`. At least one field present when the block exists |
| `ENTITY-COMMENT` | Fields: `text: str` (one or more lines, stored without the `# ` leader); `anchor: one of header · binding(ID) · locator(ID, path, symbol) · field(ID, name) · assertion(ID, identity) · coverage · curated(kind)`. Identity: the anchor |
| `ENTITY-FINDING` | Output of validation. Fields: `code: INV-* ID`; `severity: enum{error, warning}`; `anchor` (as `ENTITY-COMMENT.anchor`, plus `file` for document-level findings); `message: str`. Not persisted |

### Invariants

Each row: the checkable condition · enforcement class · mechanism. Severity is **error** unless marked *advisory* (warning).

| ID | Condition | Enforcement |
|---|---|---|
| `INV-ID-GRAMMAR` | Every key of `bindings` matches `^[A-Z][A-Z0-9]+(-(?![0-9]+(-\|$))[A-Z0-9]+)+$` — Dictum's grammar with no all-digit segment | write-gated; checked on every read |
| `INV-ID-UNIQUE` | Exactly one binding per contract ID | by-construction: a YAML mapping cannot hold a duplicate key; the loader rejects a duplicate as unparseable (exit 2) |
| `INV-SCHEMA-VERSION` | `schema_version` is present, an integer, and equals the running binary's major version | write-gated (`init` writes it; every write re-checks); checked on every read |
| `INV-CLOSED-KEYS` | Every mapping uses only its defined keys: document {`schema_version`, `bindings`, `coverage`}; binding {`locators`, `compare_via`, `fields`, `wire`, `asserted_by`}; locator {`path`, `symbol`, `role`}; field locator {`path`, `symbol`}; wire {`casing`, `enums`, `dates`}; assertion {`path`, `symbol`, `run`, `arm`, `owed`}; coverage {`fully_bound`, `curated`} | write-gated; checked on every read |
| `INV-NO-LINE-NUMBERS` | No key named `lines` or `line` anywhere (such a key also violates `INV-CLOSED-KEYS`; **both** findings are reported, this one carrying the precise message), and no `path` or `symbol` ending in `:` followed by digits | write-gated; checked on every read |
| `INV-PATH-FORM` | Every `path` satisfies `ENTITY-PATH` | write-gated; checked on every read |
| `INV-PATH-EXISTS` | *opt-in* — with `--check-paths`, every locator and field-locator `path`, and every candidate `path` in write input, exists on disk relative to the working directory (checked by `stat` only, after `INV-PATH-FORM` has passed). Severity **error**. Never evaluated without the flag | write-gated when the flag is on (a write with a missing path is refused); checked on every read with the flag on |
| `INV-SYMBOL-NONEMPTY` | Every present `symbol` is a non-empty string; every `run`, `compare_via`, `owed`, `arm`, wire value, and curated reason likewise | write-gated; checked on every read |
| `INV-ROLE-VALUES` | Every present `role` is `producer` or `consumer` | write-gated; checked on every read |
| `INV-WIRE-SUBSET` | A present `wire` has at least one of its three keys and nothing else | write-gated; checked on every read |
| `INV-ASSERTION-SHAPE` | Each assertion is exactly bound (`path`, `symbol`, `run` all present, `owed` absent) or exactly owed (`owed` present, the three absent); `arm` optional in both | write-gated; checked on every read |
| `INV-FIELD-NAME` | Every `fields` key is a non-empty string; `fields`, when present, is non-empty | write-gated; checked on every read |
| `INV-COVERAGE-WELLFORMED` | Every kind in `fully_bound` and every `curated` key matches `[A-Z][A-Z0-9]+`; `fully_bound` has no duplicates; no kind appears in both; every curated reason is non-empty; the block, when present, has at least one field | write-gated; checked on every read |
| `INV-LOCATOR-UNIQUE` | Within a binding, no two locators share (`path`, `symbol`) | write-gated (`add-locator` refuses a duplicate); checked on every read |
| `INV-ASSERTION-UNIQUE` | Within a binding, no two assertions share their identity | write-gated; checked on every read |
| `INV-COMMENT-ANCHORED` | Every comment belongs to exactly one anchor per the carrier rules, and no anchor has two carriers. **Boundary with the parse layer** (fixability drives the outcome): a comment the Loader cannot attach to any anchor at all (it sits where no anchor exists) makes the file unloadable → `ERR-PARSE`, exit 2; a loadable file with two carriers on one anchor → this finding, exit 1 | write-gated (the tool only writes at anchors); checked on every read |
| `INV-BYTES` | The file is UTF-8 without BOM, LF line endings only, no trailing whitespace on any line. **Boundary with the parse layer** (fixability drives the outcome): non-UTF-8 bytes, a BOM, or CRLF make the file unloadable → `ERR-PARSE`, exit 2, never normalised; trailing whitespace on a loadable file → this finding, exit 1 | write-gated; checked on every read |
| `INV-ROLE-REQUIRES-WIRE` | *advisory* — a binding with any `role` on a locator has a `wire` block (template hygiene rule) | advisory: warning on read and after write |
| `INV-OWNED-TWICE` | *advisory* — no (`path`, `symbol`) pair appears as a locator under two different contract IDs (template hygiene rule) | advisory: warning on read and after write |
| `INV-CANONICAL-FIXPOINT` | For any loadable map `m`, `format(format(m)) == format(m)` byte-for-byte; for a map already in canonical layout, `dump(load(m)) == m` | tool property, asserted by golden tests (Quality); not a store constraint |
| `INV-ORDER-PRESERVED` | Every write other than `format` leaves the relative order of all existing bindings, locators, fields, assertions, and coverage entries unchanged, and places a new entry last in its list | tool property, asserted by contract tests (Quality) |
| `INV-ATOMIC-WRITE` | After any write attempt the target file is either byte-identical to its pre-write content or the complete post-validated new content; never partial | by-construction: temporary file + `rename` in the same directory |

## Acceptance criteria

1. One assertion per `INV-*` (Quality's coverage map): each write-gated invariant has a synthetic fixture that violates it, and `validate` reports exactly that finding code at the expected anchor with exit 1; each advisory one reports a warning with exit 0. The unloadable halves of `INV-BYTES` (BOM, CRLF, non-UTF-8) and `INV-COMMENT-ANCHORED` (no anchor exists) are `ERR-PARSE` forcings with exit 2 instead.
2. Grammar table for `INV-ID-GRAMMAR`: a table-driven test with at least `CAP-003` (reject), `API-V2-USERS` (accept), `SCREEN-3D` (accept), `cap-003` (reject), `CAP` (reject), `ENTITY-ORDER.status` (reject).
3. Duplicate-key fixture for `INV-ID-UNIQUE`: a fixture with a duplicated key fails to load with exit 2.
4. Fixpoint tests for `INV-CANONICAL-FIXPOINT`: for every public fixture and every synthetic fixture, `format` twice equals `format` once; for the canonical golden fixture, load-then-dump is byte-identical.
5. Order-preservation diffs for `INV-ORDER-PRESERVED`: a contract test appends via each `add-*` and `set` on a multi-binding fixture and asserts the diff is limited to the appended lines.
6. Injected-failure test for `INV-ATOMIC-WRITE`: a test that forces a failure after the temporary file is written (a post-validation error injected, or a rename made to fail) and asserts the target is byte-identical to its original.
7. Anchor fixtures for `INV-COMMENT-ANCHORED`: fixtures for each of the seven anchor kinds round-trip; a fixture with two carriers on one anchor produces the finding (exit 1); a fixture with a comment where no anchor exists is `ERR-PARSE` (exit 2).
8. The canonical example in *Persistence* is itself a golden fixture: it validates clean and is a `format` fixpoint (bindings in byte order, comments only at anchors, quoting and padding per the rules above).
9. Opt-in path fixture for `INV-PATH-EXISTS`: a fixture with one missing path passes without `--check-paths` and fails with it; `add-locator` of a missing path is refused only with the flag.

