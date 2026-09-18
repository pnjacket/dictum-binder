---
artifact: product-doc
role: concern
concern-id: product-and-requirements
behavior: core
trigger: always
in-scope-subaspects: [problem-motivation, target-users-personas, goals-success-criteria, capability-register, constraints-assumptions, risks]
current-rung: contract-grade
status: draft
version: 0.3.0
---

# Product & Requirements — dictum-binder

> One-line: a deterministic command-line tool, installed as `lspd`, that is the reader, writer, and validator of a Dictum project's `bindings.yaml`, so that the binding map has one canonical style and a predictable token cost regardless of which LLM or human touches it.
<!-- BUILD: Contract-grade as of 2026-09-17 (doc-levelup, interactive; two rounds beyond Specified). Owns PERSONA-*, CAP-*, SUCCESS-* — minted in Contracts below (register form = table row, ID in first cell). Every other occurrence of those IDs in this set is a reference. Publish once the set reaches the build-ready gate. -->

## Purpose & Scope

Owns the *why* and the capability spine of the tool. Dictum deliberately fixes only the **form** of its machine-readable extension points and blesses no tool. In practice each LLM that maintains a binding map picks its own in-practice layout, and handing a project from one model to another causes setbacks. This tool exists to produce **one battle-tested style** for the binding map, deterministically, so that an LLM never edits the file by hand and never has to read more of it than the answer to its question. If the style succeeds, others can adopt it or write converters between their style and this known-good one, against a published schema.

The tool's remit is **strictly `bindings.yaml`**. It never reads or writes the manifest, the concern docs, or the product code. Validation is **structural to the file alone**. Anything that needs the doc set or the code tree (doc-end resolution, coverage against the ID web, symbol resolution) stays with the Dictum advisory agents.

## Non-goals / Out-of-scope

Product-level non-goals (rules set by the operator, not derivable from the standard):

- **Single file by rule.** One invocation operates on exactly one `bindings.yaml`. The standard models one map per manifest and never describes a split map; the operator has hit a multi-file case in the wild and decided **not** to support it: the hassle of supporting it forever is not worth it, and converting several maps to one is "one LLM query away". `deferred` — re-entry: reassess only if a converter proves insufficient.
- **No doc-end or code-end validation.** Reading the manifest, the docs, or the code tree is out: those artifacts have no fixed style, so a deterministic tool cannot read them reliably. `absent` by design. The one exception is the **opt-in** path-existence check (`CAP-PATHCHECK`).
- **No execution.** The tool never runs an `asserted_by.run` selector or any other command. `absent`.
- **No line numbers, ever.** A line-numbered locator fails silently when code moves; the schema rejects `lines:` or any line reference and the tool never emits one. `absent` by rule.
- **No ingestion of loosely styled maps.** The tool does not convert a template-conforming but non-canonical map into canonical form; it reports findings and leaves the conversion to an LLM, which conforms to the published schema (`CAP-SCHEMA`). `absent` by decision.
- **No backups, no undo.** The target file is version-controlled by its owner; history is not the tool's concern. `absent`.
- **No upward search, no auto-create.** The file is `./bindings.yaml` or the `--file` argument; a missing file requires `init` first. `deferred` — reassess in a later version if needed.
- **No multi-map discovery or merge view.** Follows from single-file. `deferred` with the same re-entry as above.
- **No support for a moved template within one major version.** When a Dictum release changes the binding-map template, that is a **new major version of `lspd`**; a single binary supports exactly one template shape. `absent` by decision.
- **No silent defaults on ambiguous conditions.** Every ambiguous state (an empty file, an empty comment, a kind declared twice, a missing path under the check) is an error the LLM fixes explicitly; the tool never guesses. `absent` by decision.
- **No concurrent-writer handling.** Two processes writing the same file at once are not coordinated; the last write wins. `absent`: single local user is the trait fact.

Scoped-out sub-aspects of this concern (manifest keys):

- `market-competitive-context` — `absent`: non-commercial tool; the "market" is the set of ad-hoc styles it intends to replace, which is the problem statement, not a market.
- `stakeholders-decision-makers` — `absent`: single-maintainer project; the operator is the only decision-maker.

Re-entry note for a scoped-out **concern**: Performance & Scalability is `deferred` at the operator's explicit call — Dictum doc sets can be very large, so no size or latency target is set; the tool goes into the wild and performance is fixed if issues arise. `[FUTURE-SCOPE]` re-entry: the first reported performance issue re-opens 11.13.

## Requirements

### Problem & motivation

A Dictum binding map (`templates/binding-map.template.md`) is the one stored index the standard permits: contract ID → code locators, self-validated on every run. The standard fixes its keys and its rules but, by design, not a house style. Two failures follow when LLMs maintain it directly:

1. **Inconsistent style, not broken files.** In a survey of fourteen real maps at scaffold time, no two models laid the file out the same way: locator shapes varied (`{path, symbol}` beside bare `{path}`, line-numbered forms, `run:` on locators instead of assertions), symbol notations varied, top-level keys were invented, deferrals were recorded as prose comments, and long prose banners carried real information. Nothing was "broken" in the sense of failing the template; the files were merely different enough that the next model re-learned the file instead of continuing it.
2. **Unpredictable token cost on read.** Models read too much or too little. One observed pattern: an agent greps for an ID, reads the single matching line, discovers the entry spans several lines, and reads the region again. Another reads the whole file to answer a one-binding question. The cost of a simple operation depends on the model's habits, not on the operation.

A deterministic tool that owns read, write, and validate removes the LLM from the file's syntax entirely, fixes one style, and makes every operation's output exactly the size of its answer.

### Target users / personas

Three personas, defined in Contracts (`PERSONA-AGENT`, `PERSONA-HUMAN`, `PERSONA-CONVERTER`). There is no fourth. The Dictum tooling itself is not a distinct persona: if the Dictum skills are ever changed to shell out to `lspd`, they act as `PERSONA-AGENT`.

### Goals & success criteria

Goals, in priority order:

1. **One canonical style.** Any map written by the tool is in the same layout, key order, and notation, whoever asked for the write.
2. **Predictable token consumption.** A query returns exactly what was requested — one binding, one list, one comment — never the whole file and never a partial entry. Output carries no prose beyond the fixed envelope.
3. **Complete coverage of the standard's operations.** Every operation Dictum performs on the map is a command, so no situation forces a hand edit.
4. **A conformance artifact for others.** A JSON Schema file, shipped with a SHA-256 checksum, that an LLM or a converter author can conform to.

The measurable criteria are minted in Contracts (`SUCCESS-ROUNDTRIP`, `SUCCESS-COMPLETE-OPS`, `SUCCESS-BOUNDED-OUTPUT`, `SUCCESS-CROSS-MODEL`, `SUCCESS-SCHEMA-MATCH`) and mapped to checks in Acceptance criteria. No non-functional target is referenced: Performance is deferred, and Security's negative assertions are owned there.

### Capability register

Twelve capabilities, all **in scope for v1** (the operator marked nothing out), minted in Contracts (`CAP-INIT` through `CAP-HELP`). Cross-cutting behaviour of every command:

- JSON on stdout by default; `--human` selects the readable rendering. `--help` is plain text at every level.
- Findings from the validation that runs before and after every write ride in the same envelope as the result.
- **Exit codes partition by who can fix the failure.** `0` — clean, or warnings only. `1` — the **caller** can fix it by changing the call or by changing the file through `lspd`: validation errors, an unknown ID or entry, a duplicate entry, rejected input, wrong arguments. `2` — the **environment** must change first: the file is missing (run `init`), unreadable, unparseable, or not writable. Every failure carries a distinct error code inside the envelope; the catalog is minted by Interfaces.
- **Input that breaks the shape is rejected; input that only warns is written.** A binding supplied to `set` or `add-*` with an unknown key or a line number is refused (exit 1, nothing written). One that raises only a warning (a `role` without `wire`) is written and the warning reported.

### Constraints & assumptions

- **Language and runtime.** Python, minimum 3.11 (so the operator's Debian 12 machine runs it on the system interpreter; a venv is used regardless). Supported platforms are whatever Python 3.11+ supports; none is targeted specifically.
- **Licence.** MIT. **Every declared dependency — runtime, transitive, development, and test — must itself be MIT** (Governance's inbound policy); the interpreter, pip, and the build backend are environment infrastructure outside the rule. ruamel.yaml (MIT, zero dependencies) is the only runtime dependency, chosen for comment fidelity; the toolchain is the standard library plus ruff and pyrefly.
- **Distribution.** A GitHub repository that users clone and install into a user-space bin; binary name `lspd`. Private until the first release, public at the first release. Ships alongside Dictum v1.3.0 (pending on Dictum main at scaffold time). `[REVISIT]` this doc set is authored against v1.2.0; run the upgrade walk when v1.3.0 is vendored.
- **Schema.** Exactly the Dictum template's keys plus three additions the operator has decided: `arm:` on an assertion, `owed:` for a deferred assertion, and a required top-level `schema_version:` (integer, equal to the `lspd` major version, written by `init`; a mismatch is a validation error). Anything else is an error. The schema is owned by this project; the operator is the author of the Dictum standard but this project acts as a **third party** and does not contribute the schema back into the template.
- **Numeric IDs are prohibited — a rule tighter than the standard.** Dictum's grammar allows numeric tokens (`CAP-003`); `lspd` rejects them as map keys because LLMs work poorly with numbered IDs. Only semantic IDs (`CAP-MODEL-CREATE`) are accepted: a segment consisting entirely of digits is rejected, while digits inside a segment (`API-V2-USERS`, `SCREEN-3D`) are fine. This is a deliberate compatibility narrowing: a Dictum-conforming map that uses numeric IDs fails `lspd` validation until its IDs are re-minted. `[REVISIT]` the operator, as the standard's author, may introduce this rule in a future major revision of Dictum; until then it is this product's own.
- **Versioning.** A change to the Dictum binding-map template is a new major version of `lspd`. The file's `schema_version` tracks it.
- **Ordering.** Edits preserve existing order and append; only `format` reorders.
- **Writes against an invalid file are allowed.** The rigid schema gives comments a defined place, so the tool can read and rewrite a file that carries findings; pre- and post-write findings are reported.
- **Value vocabularies are open.** `wire.casing`, `wire.enums`, `wire.dates`, and `compare_via` accept any non-empty string; the template's values are examples, not an enumeration.
- **Excluded kinds are silent.** A binding whose kind the template excludes from the map (`CAP`, `POLICY`, `ROLE`, `LICENSE-TIER`, `PERF`) is accepted without a finding; the tool does not know which kinds a given doc set makes code-realisable.
- **Performance.** No target (deferred concern).
- **Test fixtures** come only from public sources (Quality).

### Risks

- **Style lock-in.** The canonical style may not fit a future Dictum template. Mitigated by the major-version rule and by the schema artifact, which makes conversion a bounded job.
- **Compatibility narrowing.** The numeric-ID prohibition rejects some conforming maps. Mitigated by a clear finding naming the rule and by the `[REVISIT]` toward the standard.
- **Comment fidelity.** A comment found between anchors must be relocated deterministically or rejected; a wrong rule loses information the wild maps demonstrably carry. Under the no-silent-defaults rule it is an error (Domain owns the anchor contract).
- **Library formatting drift.** ruamel.yaml output could change across versions and break round-trip fidelity; pinned and guarded by golden tests (Integrations, Quality).
- **Model-authored code** raises the source-provenance obligation (Governance).
- **Performance in the wild** (deferred; re-entry note above).

## Open Questions

None open. The numeric-prohibition grammar was settled on 2026-09-17: a segment consisting **entirely** of digits is rejected (`CAP-003`); digits used as indicators inside a segment (`API-V2-USERS`, `SCREEN-3D`) are allowed. Domain & Data encodes this in the ID invariant.

## Dependencies & Cross-references

This concern is the root of the ID web and consumes nothing minted elsewhere. Forward references it will be tightened against (described here, minted by the named concern):

- The command surface, JSON envelope, error catalog, and exit codes — Interfaces & Contracts (`CLI-###`, `OUT-###`, `ERR-###`).
- The binding-map entities and the structural rules `CAP-VALIDATE` enforces, including `schema_version`, comment anchors, and the ID invariant — Domain & Data (`ENTITY-###`, `INV-###`).
- The single-file, structural-only, no-line-number, embedded-schema, numeric-ID, and major-version decisions as cross-cutting ADRs — Architecture (`ADR-###`).
- The golden-test and E2E definitions that realise the acceptance checks below — Quality & Testing.
- The ruamel.yaml dependency — Integrations (`DEP-###`).
- The Dictum naming constraint — Business & Legal (`LEGAL-###`).

## Examples / Worked scenarios

1. **An agent closes a slice.** A model has just realised `ENTITY-USER` in `src/models/user.py`. It runs `set ENTITY-USER` with the locator, then `add-assertion INV-USER-EMAIL-UNIQUE` with the verbatim test title and the run selector. Each call validates before and after, writes atomically, and returns the affected binding plus findings. The model never saw the file and read only two bindings' worth of output. (`CAP-SET`, `CAP-ADD`, `SUCCESS-BOUNDED-OUTPUT`)
2. **A human tidies up.** After a week of agent edits, bindings sit in insertion order. The maintainer runs `format`; the file is rewritten in canonical order with every comment kept at its anchor. A second `format` changes nothing. (`CAP-FORMAT`, `SUCCESS-ROUNDTRIP`)
3. **A converter author.** Someone with a map in a different style downloads the JSON Schema from the repository, checks its SHA-256 against the README and against `lspd schema --checksum`, and writes a converter. They then run `validate` on the result and fix the findings the schema could not express (a `role` without `wire`; numeric IDs). (`CAP-SCHEMA`, `CAP-VALIDATE`, `SUCCESS-SCHEMA-MATCH`)
4. **A hand-over between models.** The next model starts with `lspd --help`, learns the surface in one call, runs `list --kind INV` to see what is asserted, and `get` on the one binding it needs. Its reads cost the same as the previous model's would have. (`CAP-HELP`, `CAP-QUERY`, `SUCCESS-CROSS-MODEL`)
5. **Retirement.** A contract is tombstoned in the manifest by the doc-change-impact skill. The agent runs `remove <ID>`; the binding is gone, order elsewhere untouched, and the post-write validation confirms nothing else referenced that locator. (`CAP-REMOVE`)
6. **A rejected write.** An agent tries `add-locator` with a `lines:` key copied from an old map. The call exits 1 with the no-line-numbers error code; the file is untouched; the agent resubmits with a symbol. (`CAP-ADD`, exit-code partition)

## Design Decisions

| Decision | Rationale |
|---|---|
| The LLM converts foreign-style maps; the tool only publishes the schema | Ingestion of unbounded styles is exactly the undecidable, style-dependent reading the tool exists to avoid; a schema plus rules is a bounded target a model can hit |
| Schema embedded in the binary; the shipped file is a copy with a checksum | The tool must be self-contained and deterministic; an external file could drift from the validator. The printed checksum makes the copy verifiable |
| Queries return exactly the requested entries | The observed token-waste patterns (grep-then-reread, whole-file reads) disappear when the tool, not the model, does the selection |
| `--help` is plain text at every level | Conventional, readable by both personas, and one bounded call is enough for an agent to learn the surface |
| No backups or undo | The file is version-controlled by its owner; a second history would be a stored duplicate the standard's Part 0.5 warns against |
| A template change is a new major version; `schema_version` in the file tracks it | One binary supports one shape; a version flag would reintroduce style variance inside the tool, and the file must say which shape it is |
| Exit codes partition by who can fix it | An agent needs one bit to decide whether to retry with a changed call or stop and report; finer distinctions live in the envelope's error code |
| No silent defaults; ambiguous states are errors | A default chosen by the tool is a style decision made invisibly — the exact thing the tool exists to eliminate. The LLM fixes explicitly |
| Numeric IDs rejected, tighter than the standard | Numbered IDs are error-prone for LLM reference; the operator applies the tighter rule here first and may promote it to the standard later |
| Excluded kinds accepted silently; `wire`/`compare_via` open | Both would require knowledge of the doc set the tool does not read; a warning it cannot justify is noise |
| Everything discussed is v1 | The operator marked nothing out; the surface is small enough to ship whole |

Cross-cutting decisions (single file, structural-only validation, no line numbers, ruamel.yaml, order preserved except on `format`) are recorded in Architecture's ADR register.

## Contracts

Register form: table row, ID in the first cell. Semantic IDs, one style per register, never renamed.

### Personas

| ID | Who | Why they use the tool |
|---|---|---|
| `PERSONA-AGENT` | An LLM working in a Dictum-adopted repository — running the Dictum skills and agents, closing slices, recording and validating bindings | Never open `bindings.yaml`; perform every binding-map operation the standard describes through commands whose output it can predict; learn the surface from `--help` in one call. **Primary persona.** |
| `PERSONA-HUMAN` | The person who owns the repository and occasionally runs the tool at a terminal — to validate, format, or inspect | A readable rendering (`--human`) of the same operations; confidence that whatever model works next inherits a file in the same style |
| `PERSONA-CONVERTER` | A third party who has a binding map in another style and wants to move to or from the canonical one | A published, checksummed JSON Schema of the canonical shape plus the listed rules the schema cannot express, so a converter can be written without reading the tool's source |

### Capabilities

Each row: description · persona(s) · scope · success-criterion reference · lifecycle notes including failure and conflict paths.

| ID | Name | Description | Persona(s) | Scope | Success ref | Lifecycle, failure and conflict paths |
|---|---|---|---|---|---|---|
| `CAP-INIT` | Initialise a map | Create an empty canonical `bindings.yaml` with `schema_version` set and an empty `bindings` mapping | agent, human | in (v1) | `SUCCESS-COMPLETE-OPS` | Refuses if the file exists (exit 1); no force flag. Required before any other write: a missing file is exit 2 for every other command. Unwritable location: exit 2 |
| `CAP-VALIDATE` | Validate | Structural validation of the file alone; findings with severity error or warning and a stable code | agent, human | in (v1) | `SUCCESS-COMPLETE-OPS`, `SUCCESS-CROSS-MODEL` | Runs on request and automatically before and after every write. Errors: ID grammar, numeric ID, unknown key, missing `schema_version` or mismatch, empty `path`/`symbol`, line number anywhere, dotted member suffix in a key, missing `run` on a non-owed assertion, a kind in both `fully_bound` and `curated`, a comment outside an anchor. Warnings: `role` without `wire`; one locator realising two IDs. Excluded kinds pass silently. Unparseable or empty file: exit 2 |
| `CAP-FORMAT` | Format | Rewrite to canonical layout and order: bindings sorted by ID, keys in template order, flow-style entries; comments kept at their anchors | agent, human | in (v1) | `SUCCESS-ROUNDTRIP` | The only command that reorders. With validation errors present it formats what it can and reports them (exit 1). Idempotent: a second run is a byte-identical no-op. Unparseable file: exit 2 |
| `CAP-QUERY` | Query | `get <ID>` returns one binding with its anchored comments; `list [--kind K]` returns matching bindings in file order | agent, human | in (v1) | `SUCCESS-BOUNDED-OUTPUT` | Unknown ID: exit 1. Empty result for `list`: exit 0 with an empty list. Output contains nothing beyond the selected entries and the envelope |
| `CAP-SET` | Upsert a binding | Replace or create a whole binding from structured input; the stub form `locators: []` is legal | agent | in (v1) | `SUCCESS-COMPLETE-OPS` | Unknown ID creates; known ID replaces in place (order kept). Input that breaks the shape is rejected, nothing written (exit 1); warning-only input is written and reported. A numeric ID is rejected |
| `CAP-ADD` | Append an entry | `add-locator`, `add-field <name>`, `add-assertion` on an existing binding | agent | in (v1) | `SUCCESS-COMPLETE-OPS` | Unknown ID: exit 1. Duplicate locator (same path and symbol): exit 1. `add-field` on an existing name replaces it. New entries append; existing order untouched. Shape-breaking input rejected as for `CAP-SET` |
| `CAP-REMOVE` | Remove | Remove a whole binding, or one locator, field, or assertion inside it | agent | in (v1) | `SUCCESS-COMPLETE-OPS` | Unknown ID or entry: exit 1. Removing the last locator leaves the stub form, not an error. This is the retirement path (tombstoned contract) and the dangling-locator fix path |
| `CAP-COVERAGE` | Declare coverage | Set or unset a kind under `fully_bound`; set or unset a `curated` entry with its reason | agent | in (v1) | `SUCCESS-COMPLETE-OPS` | A kind in both lists: exit 1. Empty reason on `curated`: exit 1. Unset of an absent entry: exit 1 |
| `CAP-COMMENT` | Comments | Get, set, and unset the comment at a defined anchor (file header, a binding, one locator or assertion, a coverage entry); round-tripped byte-for-byte and exposed in JSON | agent, human | in (v1) | `SUCCESS-ROUNDTRIP` | Unknown anchor: exit 1. Setting an empty string: exit 1 (use unset). Unset of an absent comment: exit 1. Anchor syntax is minted by Interfaces |
| `CAP-PATHCHECK` | Path check (opt-in) | With a flag, additionally verify each locator `path` exists relative to the working directory | agent, human | in (v1) | `SUCCESS-COMPLETE-OPS` | Off by default. A missing path is an **error**, not a warning. The only filesystem read outside the target file; paths are stat-ed, never read |
| `CAP-SCHEMA` | Schema artifact | `lspd schema` prints the embedded JSON Schema; `lspd schema --checksum` prints its SHA-256. The same schema ships as a plain file in the repository with its SHA-256 in the README. The executable never reads the external file. The schema covers shape only; rules it cannot express are listed in the README beside the checksum and enforced by `CAP-VALIDATE` | converter, agent | in (v1) | `SUCCESS-SCHEMA-MATCH` | No failure path beyond I/O on stdout (exit 2) |
| `CAP-HELP` | Self-description | Comprehensive plain-text `--help` at every level: `lspd --help`, `lspd <command> --help`, `lspd <command> <subcommand> --help` | agent, human | in (v1) | `SUCCESS-CROSS-MODEL` | `--help` on an unknown command: exit 1 with the usage error |

### Success criteria

| ID | Observable outcome |
|---|---|
| `SUCCESS-ROUNDTRIP` | For every canonical fixture, load then dump is byte-identical to the fixture. For every fixture, canonical or not, `format` applied twice equals `format` applied once |
| `SUCCESS-COMPLETE-OPS` | Every operation the standard performs on the map (table below) is served by a named command, and each row has a passing contract test |
| `SUCCESS-BOUNDED-OUTPUT` | `get` returns exactly one binding and `list` exactly the matching entries; the envelope contains no other file content |
| `SUCCESS-CROSS-MODEL` | At the end of each of the operator's trial sessions with a different model on the same repository, `validate` reports no errors and `format` is a no-op — no model hand-edited the file |
| `SUCCESS-SCHEMA-MATCH` | The shipped schema file's SHA-256 equals `lspd schema --checksum` equals the value in the README |

Operations the standard performs on the map, and the command that serves each (the basis of `SUCCESS-COMPLETE-OPS`):

| Standard operation (source) | Command |
|---|---|
| Mint the map at excavation, or start greenfield (Part 10f, 10d) | `init`, then `set` per binding |
| Stub a new contract as `locators: []` (doc-feature) | `set` with the stub form |
| Record or update a binding as a slice lands (Part 10e) | `set`, `add-locator`, `add-field`, `add-assertion` |
| Record a deferred assertion as owed (template) | `add-assertion` with `owed:` |
| Label a multi-arm assertion (template) | `add-assertion` with `arm:` |
| Declare a dual realisation with its wire contract (template) | `set` with `role` and `wire` |
| Fix or retire a dangling locator (`binding-stale`, Part 10d) | `add-locator` / `remove --locator` |
| Remove a binding on tombstone (Part 10d, 10e) | `remove` |
| Declare `fully_bound` / `curated` coverage (template) | `coverage` |
| Self-validate the map every run (template) | `validate` (structural slice only) |
| Read a binding's locators; check whether an ID is bound (drift-detector, planner) | `get`, `list` |
| Carry prose alongside entries (observed in every real map) | `comment` |

## Acceptance criteria

Each maps to an observable check; Quality owns the test definitions.

1. `SUCCESS-ROUNDTRIP` — a golden test per public fixture: `dump(load(F)) == F` for canonical `F`; `format(format(F)) == format(F)` for every `F`.
2. `SUCCESS-COMPLETE-OPS` — a contract test per row of the operations table above; the test suite fails if a row has no test.
3. `SUCCESS-BOUNDED-OUTPUT` — contract tests on `get` and `list` assert the envelope's payload equals exactly the selected entries; a fixture with many bindings is used so leakage would be visible.
4. `SUCCESS-CROSS-MODEL` — recorded by the operator per trial session: `validate` exit 0 with no errors and `format` producing no diff. Not automated; the record is the check.
5. `SUCCESS-SCHEMA-MATCH` — a CI test computes the shipped file's SHA-256 and asserts equality with `lspd schema --checksum` and with the README value.
6. Every `CAP-*` row's failure paths — each named exit-1 and exit-2 condition has a forced-condition contract test (Interfaces' `ERR-###` catalog names the forcing).
7. Every `PERSONA-*` is referenced by at least one `CAP-*`, and every `CAP-*` by at least one `SUCCESS-*`.

---
<!-- BUILD: legend — subject markers [GAP] [ASSUMPTION] [REVISIT] [FUTURE-SCOPE] stay published; every BUILD comment, this one included, is stripped on publish. -->
