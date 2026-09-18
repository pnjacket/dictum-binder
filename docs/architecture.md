---
artifact: product-doc
role: concern
concern-id: architecture
behavior: core
trigger: always
in-scope-subaspects: [component-decomposition-responsibilities, component-interactions-data-flow, cross-cutting-patterns, technology-choices, adr-register]
current-rung: contract-grade
status: draft
version: 0.3.0
---

# Architecture — dictum-binder

> One-line: a single-process Python CLI in eight components — parse the one file with comment fidelity, validate it against a schema that is a single Python source, mutate a plain model, validate again, emit the byte-specified canonical layout through an own emitter, replace the file atomically, and render one JSON envelope.
<!-- BUILD: Contract-grade as of 2026-09-17 (doc-levelup, interactive, one round — every proposal accepted). Owns COMPONENT-*, PATTERN-*, ADR-* (register form: table row, ID in first cell). Publish with the set. -->

## Purpose & Scope

Owns the component decomposition, the data flow between components, the cross-cutting patterns every command follows, the technology choices, and the ADR register. The product is small in code and single-process; what needs architecture is the strict separation between the **library-facing edge** (the only place ruamel.yaml, the sole third-party dependency, is touched), the **model and rules** (the canonical style), and the **command surface** (what LLMs call), so that library behaviour can never leak into the file's bytes or the envelope.

## Non-goals / Out-of-scope

- `boundaries-isolation-model` — `absent`: one process, one trust domain, one user; the only boundary is the process boundary to the caller (Security & Privacy owns it).
- `logical-deployment-topology` — `absent`: not distributed; a user-space binary.
- `scalability-resilience-patterns` — `absent` here because Performance & Scalability is deferred at the product level (Product Non-goals); nothing to place.
- No plugin or extension mechanism; no importable public API (`library-sdk-surface` is absent in Interfaces). `absent` by decision.
- No logging subsystem. `absent` by decision (`ADR-NO-LOGGING`).

## Requirements

### Component decomposition & responsibilities

Eight components, minted in Contracts. In one sentence each: **CLI** parses arguments and dispatches; **Loader** turns file bytes into the Model, comments included; **Model** is the plain in-memory form of Domain's entities; **Validator** produces findings from a Model; **Commands** implement the twelve capabilities against the Model; **Emitter** turns a Model into canonical bytes; **Renderer** turns a result or error into the JSON envelope or the human rendering; **Schema** is the single Python source of the JSON Schema, consumed by Validator and by `lspd schema`.

Package layout: a `src/lspd/` package with one module per component (`cli.py`, `loader.py`, `model.py`, `validator.py`, `commands/` one module per capability, `emitter.py`, `render.py`, `schema.py`); console script `lspd = lspd.cli:main`; tests under `tests/`; the generated schema file at the repository root as `lspd.schema.json`. The build backend is `setuptools` with `pyproject.toml` — a routine choice recorded here so it is not re-decided.

### Component interactions / data flow

Every command is one pass through a fixed pipeline; no component calls a component to its left.

```
                 bytes            Model                          Model           bytes
 file ─► Loader ─────► Validator ─────► Commands ─────► Validator ─────► Emitter ─────► atomic replace ─► file
            │             (pre)      (mutate)            (post)             │
            │                                                               │
            └── parse error ──► Renderer (ERR, exit 2)      findings + result ──► Renderer ──► stdout, exit code
```

- **Read-only commands** (`validate`, `get`, `list`, `comment get`, `schema`, `--help`) stop after the pre-validation, or before the Loader for `schema` and `--help`.
- **Write commands** (`init`, `set`, `add-*`, `remove`, `coverage`, `comment set|unset`, `format`) run the whole pipeline. `init` skips the Loader and starts from an empty Model. `format` is the only command whose mutation step reorders.
- The Validator runs twice on a write: **pre** on the loaded Model (findings reported, the write still proceeds unless the *input* breaks the shape) and **post** on the mutated Model (a shape error here aborts before the Emitter; see `PATTERN-VALIDATE-AROUND-WRITE`).
- Findings from both passes and the command result are one envelope; the Renderer never sees library objects, only Model values and findings.
- The Emitter is the **only** producer of file bytes; the Loader is the **only** consumer of ruamel.yaml. The Model carries comments as `ENTITY-COMMENT` values so that both edges agree on anchors without sharing library types.

### Cross-cutting patterns

Five, minted in Contracts: the total error envelope (`PATTERN-ERROR-ENVELOPE`), validate-around-write (`PATTERN-VALIDATE-AROUND-WRITE`), atomic replace (`PATTERN-ATOMIC-REPLACE`), the exit-code partition (`PATTERN-EXIT-CODES`), and output mode selection (`PATTERN-OUTPUT-MODE`).

### Technology choices

| Choice | Decision | ADR |
|---|---|---|
| Language / runtime | Python ≥ 3.11 | (Product constraint) |
| CLI parsing | `argparse` (standard library); subparsers give `--help` at every level | `ADR-ARGPARSE` |
| YAML parsing | ruamel.yaml, round-trip loader, **load only** | `ADR-LOAD-RUAMEL-EMIT-OWN` |
| YAML writing | own emitter for the canonical subset | `ADR-LOAD-RUAMEL-EMIT-OWN` |
| Schema | one Python rule table; the JSON Schema file **and** the shape checker are generated from it | `ADR-SCHEMA-SINGLE-SOURCE`, `ADR-OWN-SHAPE-VALIDATOR` |
| Shape validation | own checker generated from the rule table; no schema library at runtime | `ADR-OWN-SHAPE-VALIDATOR` |
| Tests | standard-library `unittest`; line coverage via standard-library `trace`; `pyrefly` strict; ruff | (Quality) |
| Packaging | `pyproject.toml`, `setuptools`, console script | (Delivery) |
| Runtime dependencies | ruamel.yaml only (MIT, zero transitive dependencies) | (Integrations `DEP-*`) |

### ADR register

Thirteen decisions, minted in Contracts. Concern-local decisions stay in each concern's Design Decisions section.

## Open Questions

None open.

## Dependencies & Cross-references

- Consumes `CAP-*` (Product): each Commands module realises one capability; `ENTITY-*` and `INV-*` (Domain): the Model realises the entities, the Validator the invariants.
- Referenced by Interfaces (every `CLI-*` element is owned by `COMPONENT-CLI` and served by `COMPONENT-COMMANDS`; the envelope `OUT-*` is emitted by `COMPONENT-RENDERER`; the `ERR-*` catalog realises `PATTERN-ERROR-ENVELOPE`), Delivery (slices map to components), Integrations (`DEP-*` for the two libraries), Security (`PATTERN-ATOMIC-REPLACE` is the file-footprint guarantee), Quality (fitness checks below).

## Examples / Worked scenarios

1. **`add-assertion` end to end.** CLI parses `lspd add-assertion INV-X --path t.py --symbol "t x" --run "pytest -k x"`. Loader reads `./bindings.yaml` into a Model with comments. Validator (pre) finds one advisory warning elsewhere in the file. Commands checks `INV-X` exists, builds the assertion, checks `INV-ASSERTION-UNIQUE`, appends. Validator (post) is clean. Emitter writes canonical bytes to `bindings.yaml.<tmp>`; rename. Renderer prints the envelope with the new binding, the one warning, exit 0.
2. **A parse failure.** The file has a duplicated key. Loader raises; the CLI's catch-all maps it to the parse error code; Renderer prints the error envelope; exit 2. No other component ran.
3. **Shape-breaking input.** `set` receives JSON with `lines: 12`. Commands hands the candidate binding to the Validator's input check before mutating; `INV-CLOSED-KEYS` fails; nothing is mutated or written; exit 1 with the finding.
4. **`schema --checksum`.** CLI dispatches straight to Schema, which serialises the Python definition with sorted keys and fixed separators and hashes the bytes; Renderer prints it. The repository file is produced by the same serialisation, so the hashes agree by construction.

## Design Decisions

Concern-local decisions: the package layout and build backend above; the pipeline's left-to-right rule (no component calls leftward); the Model as plain dataclasses carrying `ENTITY-COMMENT` values rather than library comment tokens. Cross-cutting decisions are the ADRs.

## Contracts

Register form: table row, ID in the first cell.

### Components

| ID | Responsibility | Owned interfaces | Dependencies |
|---|---|---|---|
| `COMPONENT-CLI` | Entry point. Parses argv with `argparse` subparsers, resolves `--file`, `--human`, `--check-paths`, `--debug`, dispatches to one Commands function, holds the **single catch-all** that maps every exception to `PATTERN-ERROR-ENVELOPE`, and sets the process exit code per `PATTERN-EXIT-CODES` | The `lspd` executable and every `CLI-*` element (Interfaces); `--help` at every level (`CAP-HELP`) | `COMPONENT-COMMANDS`, `COMPONENT-RENDERER`, `COMPONENT-SCHEMA` (for `schema`); `argparse` |
| `COMPONENT-LOADER` | Resolves the target to its final real path (`SEC-SYMLINK-FINAL-TARGET`), enforces the 10 MiB size cap unless `--no-size-limit` (`SEC-FAIL-CLOSED`), reads the bytes, checks `INV-BYTES`, parses with ruamel.yaml's round-trip loader, and converts the result into a `COMPONENT-MODEL` value including every comment mapped to its anchor (`INV-COMMENT-ANCHORED` is checked here, since anchors exist only at this edge). Raises a parse error for unparseable input, a duplicate key, or a comment with no anchor | `load(path) -> Model` | ruamel.yaml (the only importer); `COMPONENT-MODEL` |
| `COMPONENT-MODEL` | Plain Python dataclasses realising `ENTITY-MAP`, `ENTITY-BINDING`, `ENTITY-LOCATOR`, `ENTITY-FIELD-LOCATOR`, `ENTITY-WIRE`, `ENTITY-ASSERTION`, `ENTITY-COVERAGE`, `ENTITY-COMMENT`, `ENTITY-FINDING`, plus the `ENTITY-CONTRACT-ID` and `ENTITY-PATH` value checks. Preserves insertion order everywhere. No library types | The typed in-memory map; `to_plain()` for schema validation and JSON rendering; `from_plain()` for `set`/`add-*` input | none |
| `COMPONENT-VALIDATOR` | Produces `ENTITY-FINDING`s from a Model or from a candidate input value: first the **shape** pass through the checker `COMPONENT-SCHEMA` generates from its rule table (mapped to `INV-CLOSED-KEYS`, `INV-ID-GRAMMAR`, `INV-ROLE-VALUES`, `INV-PATH-FORM`, … wherever the rule table expresses the rule), then the **rule** pass in plain Python for every remaining `INV-*`. Reports **all** findings in one run, never the first only. Optionally the path check (`CAP-PATHCHECK`) | `validate(model) -> list[Finding]`; `validate_input(value, kind) -> list[Finding]` | `COMPONENT-SCHEMA`, `COMPONENT-MODEL`; standard library only |
| `COMPONENT-COMMANDS` | One module per capability (`init`, `validate`, `format`, `get`, `list`, `set`, `add`, `remove`, `coverage`, `comment`). Each takes a Model (or none for `init`) and arguments, applies the capability's lifecycle rules from Product's `CAP-*` rows, and returns a result value plus, for writes, the mutated Model. Enforces `INV-ORDER-PRESERVED`; only `format` reorders | One function per `CLI-*` element | `COMPONENT-MODEL`, `COMPONENT-VALIDATOR` (for input checks) |
| `COMPONENT-EMITTER` | Serialises a Model to the canonical layout in Domain's *Persistence* section, byte for byte: key orders, flow style, quoting rule, comment carriers, blank lines. The **only** producer of file bytes. Performs the atomic replace (`PATTERN-ATOMIC-REPLACE`) | `emit(model) -> bytes`; `write(model, path)` | `COMPONENT-MODEL`; standard library only |
| `COMPONENT-RENDERER` | Turns a command result, findings, and errors into the JSON envelope (`OUT-*`, Interfaces) or, with `--human`, the readable rendering; prints to stdout. Never sees library objects | `render(result, findings, mode) -> str`; `render_error(err, mode) -> str` | `COMPONENT-MODEL` |
| `COMPONENT-SCHEMA` | A Python **rule table** describing `ENTITY-MAP`'s shape — every mapping's closed key set, each key's type, optionality, enum, and pattern — from which two things are generated: the JSON Schema document (draft 2020-12; serialised deterministically with sorted keys, fixed separators, trailing newline; its SHA-256 computed) and the shape checker `COMPONENT-VALIDATOR` runs (`ADR-SCHEMA-SINGLE-SOURCE`, `ADR-OWN-SHAPE-VALIDATOR`). The repository file `lspd.schema.json` is generated from it; a CI test asserts equality (`SUCCESS-SCHEMA-MATCH`) | `schema() -> dict`; `schema_json() -> bytes`; `checksum() -> str`; `check_shape(value, node) -> list[Finding]` | standard library only |

### Cross-cutting patterns

| ID | Pattern |
|---|---|
| `PATTERN-ERROR-ENVELOPE` | **Total.** Every failure from every source — argument parsing (argparse's own errors are intercepted, never its default stderr text), file I/O, ruamel parse errors, jsonschema errors, command-level errors, and any unexpected exception — is caught at `COMPONENT-CLI`'s single catch-all and rendered as the error envelope with a stable `ERR-*` code (Interfaces). A Python traceback never reaches stdout or stderr unless `--debug` is set, and then only **in addition** to the envelope, on stderr. **Content-negotiated** in the CLI sense: the envelope is JSON by default and the human rendering under `--human`; both carry the same code and message. `KeyboardInterrupt` is the one exception: exit 130, no envelope |
| `PATTERN-VALIDATE-AROUND-WRITE` | Every write command runs the Validator **before** (on the loaded Model) and **after** (on the mutated Model). Pre-findings never block the write by themselves — a file with findings may still be edited through the tool (Product constraint). Candidate **input** is validated with `validate_input` before mutation; any error there aborts with nothing written. A post-validation **error** is a tool bug by construction (valid model + valid input must yield a valid model) and aborts before the Emitter with the internal-error code. Both passes' findings are returned in the envelope, labelled `pre` and `post` |
| `PATTERN-ATOMIC-REPLACE` | The Emitter writes to a temporary file in the **resolved** target's directory (`<name>.<random>.tmp`), copies the target's permission bits, flushes and fsyncs, then `rename`s over the target. On any failure the temporary file is removed and the target is untouched (`INV-ATOMIC-WRITE`). Nothing else on disk is ever written |
| `PATTERN-EXIT-CODES` | `0` clean or warnings only · `1` the caller can fix it (validation errors, unknown ID or entry, duplicate, rejected input, usage error) · `2` the environment must change (file missing → `init`, unreadable, unparseable, unwritable, internal error) · `130` interrupted. The code is decided by `COMPONENT-CLI` from the `ERR-*` class or the highest finding severity; no command sets it directly |
| `PATTERN-OUTPUT-MODE` | Default JSON on stdout, one document per invocation, no other stdout output ever. `--human` switches the Renderer to the readable form. `--help` is plain text regardless of mode. stderr is used only by `--debug`. The envelope's payload for `get`/`list` is exactly the selected entries (`SUCCESS-BOUNDED-OUTPUT`) |

### ADR register

| ID | Decision · context · consequences |
|---|---|
| `ADR-SINGLE-FILE` | **One invocation, one file.** Context: the standard models one map per manifest; a multi-file case exists in the wild. Decision: unsupported; `--file` addresses another doc set's map. Consequences: no discovery, no merge view; conversion of several maps to one is left to an LLM. Status: accepted (Product) |
| `ADR-STRUCTURAL-ONLY` | **Validation reads nothing but the target file.** Context: the manifest, docs, and code have no fixed style; a deterministic reader of them is not buildable. Decision: doc-end and code-end checks stay with Dictum's agents; the opt-in path check is the one exception and only stats paths. Consequences: coverage gaps and unknown IDs are invisible to `lspd` by design. Status: accepted |
| `ADR-NO-LINE-NUMBERS` | **No line references in any form.** Context: a stale line number fails silently. Decision: `lines`/`line` keys and `:NNN` suffixes are errors; the tool never emits them. Consequences: some wild maps fail validation until converted. Status: accepted |
| `ADR-LOAD-RUAMEL-EMIT-OWN` | **ruamel.yaml loads; an own emitter writes.** Context: the canonical layout is specified byte for byte; library dumpers vary across versions. Decision: parse arbitrary YAML with comments via ruamel's round-trip loader, convert to the Model at the Loader edge, and serialise with an own emitter for the strict subset. Consequences: a library upgrade cannot change file bytes; the emitter is small and fully tested by golden fixtures; ruamel is confined to one module. Status: accepted |
| `ADR-ARGPARSE` | **Standard-library `argparse`.** Context: hierarchical `--help` is required; dependencies must stay MIT and few. Decision: argparse subparsers; argparse's own error path is intercepted into the envelope. Consequences: no colour, no shell completion in v1. Status: accepted |
| `ADR-SCHEMA-SINGLE-SOURCE` | **The schema is one Python object.** Context: the executable must embed the schema and never read the shipped file; the file must match the binary. Decision: define once in `COMPONENT-SCHEMA`; generate `lspd.schema.json` from it; assert equality in CI; `lspd schema --checksum` hashes the same bytes. Consequences: no drift is possible; regenerating the file is a build step. Status: accepted |
| `ADR-OWN-SHAPE-VALIDATOR` | **No schema library at runtime; the shape checker is generated from the rule table.** Context: the published schema and the validator must not disagree on shape, and every declared dependency must be MIT — `jsonschema`'s tree pulls `typing_extensions` (PSF-2.0) on Python 3.11/3.12. Decision: one Python rule table in `COMPONENT-SCHEMA` generates both the JSON Schema document and the checker; agreement is by construction, not by a second engine. Consequences: ruamel.yaml is the only runtime dependency; the rule table's expressiveness is bounded to what both outputs can express (closed keys, types, optionality, enums, patterns), and everything else is an explicit `INV-*` rule; a unit test per rule-table entry replaces differential testing. Status: accepted, supersedes the earlier `jsonschema` choice |
| `ADR-FORMAT-ONLY-REORDERS` | **Edits preserve order; only `format` sorts.** Context: an LLM appending to a file must not see unrelated diffs. Decision: append-only writes; canonical order on explicit `format`. Consequences: a file can be valid but non-canonical; `SUCCESS-CROSS-MODEL` uses `format` as a no-op check. Status: accepted |
| `ADR-INIT-REQUIRED` | **No auto-create.** Context: first version; clean control over file creation. Decision: a missing file is exit 2 for every command but `init`; `init` refuses an existing file with no force flag. Consequences: one extra call on a new repo; reassessed in a later version. Status: accepted, `[FUTURE-SCOPE]` reassess |
| `ADR-NO-SILENT-DEFAULTS` | **Ambiguity is an error the LLM fixes.** Context: a default chosen by the tool is an invisible style decision. Decision: empty file, empty comment, kind declared twice, missing path under the check, CRLF, BOM, two comment carriers — all errors, never normalised. Consequences: stricter than the template; more round-trips on messy input, none on tool-written files. Status: accepted |
| `ADR-MAJOR-PER-TEMPLATE` | **A template change is a new `lspd` major; `schema_version` tracks it.** Context: one binary should support one shape. Decision: no version flag; the file declares its shape; mismatch is an error; no migration in v1. Consequences: a Dictum template change forces a coordinated bump and, later, a migration command. Status: accepted |
| `ADR-NUMERIC-IDS-REJECTED` | **All-digit ID segments are rejected, tighter than Dictum.** Context: LLMs mis-handle numbered IDs; the operator authors the standard and may promote the rule later. Decision: `INV-ID-GRAMMAR` excludes all-digit segments; digits inside a segment are fine. Consequences: some conforming maps fail until re-minted; a clear finding names the rule. Status: accepted, `[REVISIT]` toward Dictum |
| `ADR-NO-LOGGING` | **No logging subsystem.** Context: a CLI with one JSON document per run has no need for a log stream, and stdout must carry nothing else. Decision: no `logging` use; `--debug` adds a traceback on stderr, nothing more. Consequences: diagnostics come from the envelope's error code and message. Status: accepted |

## Acceptance criteria

1. **Import fitness**: a test asserts that `ruamel` is imported only in `loader.py` and that no other third-party package is imported anywhere in `src/lspd/` (grep over the tree; the standard library is the only other source).
2. **Emitter sole writer**: a test asserts no module other than `emitter.py` opens a file for writing (grep for write-mode opens).
3. **Total error envelope**: a forced test per error source — bad argv, missing file, unreadable file, unparseable YAML, duplicate key, shape-breaking input, unknown ID, an injected unexpected exception — asserts a JSON envelope on stdout, the expected exit code, and no traceback without `--debug`; with `--debug`, the traceback appears on stderr and the envelope is unchanged.
4. **Validate-around-write**: a fixture with a pre-existing warning is edited; the envelope carries the warning under `pre`, the write succeeds; a candidate input with an unknown key is rejected with nothing written (file bytes identical).
5. **Atomic replace**: an injected failure after the temporary file is written leaves the target byte-identical and no temporary file behind.
6. **Schema single source**: CI regenerates `lspd.schema.json` from `COMPONENT-SCHEMA` and fails on any diff; `lspd schema --checksum` equals the SHA-256 of the file.
7. **Pipeline direction**: a test asserts the module import graph is acyclic and no component imports a component to its left in the flow diagram.

---
<!-- Status markers (subject, stay published): [GAP] [ASSUMPTION] [REVISIT] [FUTURE-SCOPE]. Build markers: these BUILD comments, stripped on publish. -->
