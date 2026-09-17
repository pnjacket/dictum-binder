---
artifact: product-doc
role: concern
concern-id: product-and-requirements
behavior: core
trigger: always
in-scope-subaspects: [problem-motivation, target-users-personas, goals-success-criteria, capability-register, constraints-assumptions, risks]
current-rung: specified
status: draft
version: 0.2.0
---

# Product & Requirements — dictum-binder

> One-line: a deterministic command-line tool, installed as `lspd`, that is the reader, writer, and validator of a Dictum project's `bindings.yaml`, so that the binding map has one canonical style and a predictable token cost regardless of which LLM or human touches it.
<!-- BUILD: Specified as of 2026-09-17 (doc-levelup, interactive, saturated in three rounds). Next rung: Contract-grade — mint PERSONA-###, CAP-###, SUCCESS-### on register lines, make every success criterion measurable, and link NFR pointers to their home concerns. Proposed IDs below sit in non-lead columns on purpose so nothing is minted yet. -->

## Purpose & Scope

Owns the *why* and the capability spine of the tool. Dictum deliberately fixes only the **form** of its machine-readable extension points and blesses no tool. In practice each LLM that maintains a binding map picks its own in-practice layout, and handing a project from one model to another causes setbacks. This tool exists to produce **one battle-tested style** for the binding map, deterministically, so that an LLM never edits the file by hand and never has to read more of it than the answer to its question. If the style succeeds, others can adopt it or write converters between their style and this known-good one, against a published schema.

The tool's remit is **strictly `bindings.yaml`**. It never reads or writes the manifest, the concern docs, or the product code. Validation is **structural to the file alone**. Anything that needs the doc set or the code tree (doc-end resolution, coverage against the ID web, symbol resolution) stays with the Dictum advisory agents.

## Non-goals / Out-of-scope

Product-level non-goals (rules set by the operator, not derivable from the standard):

- **Single file by rule.** One invocation operates on exactly one `bindings.yaml`. The standard models one map per manifest and never describes a split map; the operator has hit a multi-file case in the wild and decided **not** to support it: the hassle of supporting it forever is not worth it, and converting several maps to one is "one LLM query away". `deferred` — re-entry: reassess only if a converter proves insufficient.
- **No doc-end or code-end validation.** Reading the manifest, the docs, or the code tree is out: those artifacts have no fixed style, so a deterministic tool cannot read them reliably. `absent` by design. The one exception is the **opt-in** path-existence check (a capability below).
- **No execution.** The tool never runs an `asserted_by.run` selector or any other command. `absent`.
- **No line numbers, ever.** A line-numbered locator fails silently when code moves; the schema rejects `lines:` or any line reference and the tool never emits one. `absent` by rule.
- **No ingestion of loosely styled maps.** The tool does not convert a template-conforming but non-canonical map into canonical form; it reports findings and leaves the conversion to an LLM, which conforms to the published schema. `absent` by decision — the schema artifact is the product's contribution to that job.
- **No backups, no undo.** The target file is version-controlled by its owner; history is not the tool's concern. `absent`.
- **No upward search, no auto-create.** The file is `./bindings.yaml` or the `--file` argument; a missing file requires `init` first. `deferred` — reassess in a later version if needed.
- **No multi-map discovery or merge view.** Follows from single-file. `deferred` with the same re-entry as above.
- **No support for a moved template within one major version.** When a Dictum release changes the binding-map template, that is a **new major version of `lspd`**; a single binary supports exactly one template shape. `absent` by decision.

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

| Persona | Who | Why they use the tool | Proposed ID |
|---|---|---|---|
| **LLM maintainer agent** | A model working in a Dictum-adopted repository — running the Dictum skills and agents, closing slices, recording and validating bindings | Never open `bindings.yaml`; perform every binding-map operation the standard describes through commands whose output it can predict; learn the surface from `--help` in one call | `PERSONA-AGENT` |
| **Human maintainer** | The person who owns the repository and occasionally runs the tool at a terminal — to validate, format, or inspect | A readable rendering of the same operations; confidence that whatever model works next inherits a file in the same style | `PERSONA-HUMAN` |
| **Converter author** | A third party who has a binding map in another style and wants to move to or from the canonical one | A published, checksummed JSON Schema of the canonical shape plus the listed rules the schema cannot express, so a converter can be written without reading the tool's source | `PERSONA-CONVERTER` |

There is no fourth persona. The Dictum tooling itself is not a distinct persona: if the Dictum skills are ever changed to shell out to `lspd`, they act as the LLM maintainer agent.

### Goals & success criteria

Goals, in priority order:

1. **One canonical style.** Any map written by the tool is in the same layout, key order, and notation, whoever asked for the write.
2. **Predictable token consumption.** A query returns exactly what was requested — one binding, one list, one comment — never the whole file and never a partial entry. Output carries no prose beyond the fixed envelope.
3. **Complete coverage of the standard's operations.** Every operation Dictum performs on the map (stub, record, update, remove on retirement, fix or retire a locator, declare coverage, validate) is a command, so no situation forces a hand edit.
4. **A conformance artifact for others.** A JSON Schema file, shipped with a SHA-256 checksum, that an LLM or a converter author can conform to.

Success criteria are qualitative at this rung; each is expected to become measurable at Contract-grade (proposed IDs in the right-hand column):

| Criterion (qualitative) | How the operator intends to gauge it | Proposed ID |
|---|---|---|
| Round-trip fidelity: a map written by the tool and read back is unchanged, comments included; `format` is idempotent | golden tests over public fixtures | `SUCCESS-ROUNDTRIP` |
| Every operation the standard describes on the map is available without opening the file | a coverage check of commands against the standard's operation list | `SUCCESS-COMPLETE-OPS` |
| Output size for a query is a function of the selected entries only | contract tests on the JSON envelope | `SUCCESS-BOUNDED-OUTPUT` |
| No style divergence across models: after the first tentative version, the operator uses it on their own projects and adapts existing ones, with different models, and observes whether maps stay in one style; fully model-run trials may follow | the operator's own cross-model use; possibly 100 % model-run trials | `SUCCESS-CROSS-MODEL` |
| The shipped schema file matches the schema embedded in the binary | the checksum printed by the tool equals the checksum in the README | `SUCCESS-SCHEMA-MATCH` |

### Capability register

All capabilities below are **in scope for v1**; the operator marked nothing out. Proposed IDs are in a non-lead column and are minted at Contract-grade.

| Capability | Description | Persona(s) | Proposed ID |
|---|---|---|---|
| Initialise a map | Create an empty canonical `bindings.yaml`. Refuses if the file exists; there is no force flag. Required before any other write, because a missing file is an error for every other command | agent, human | `CAP-INIT` |
| Validate | Structural validation of the file alone: ID grammar on keys, closed key sets, non-empty path and symbol, no line numbers, `role` requires `wire`, every assertion has `run` (unless owed — open question in Domain), owned-twice locator warning, excluded-kind warning (open question below), coverage kinds well-formed, comments only at anchors. Runs on request, and automatically before and after every write | agent, human | `CAP-VALIDATE` |
| Format | Rewrite the file to the canonical layout and canonical order (bindings sorted by ID; keys in template order). The **only** command that reorders. Formats what it can when the file has validation errors and reports them | agent, human | `CAP-FORMAT` |
| Query | `get` one binding by ID; `list` bindings, optionally filtered by kind, in file order. Comments at the queried anchors are included. Output is exactly the requested entries | agent, human | `CAP-QUERY` |
| Upsert a binding | `set` a whole binding from structured input; creates the ID if unknown, replaces it if known. The stub form (`locators: []`) is a legal value | agent | `CAP-SET` |
| Append an entry | `add-locator`, `add-field`, `add-assertion` on an existing binding. A duplicate locator (same path and symbol) is an error; `add-field` on an existing field name replaces it; a new entry is appended, existing order untouched | agent | `CAP-ADD` |
| Remove | Remove a whole binding, or one locator, field, or assertion inside it. An unknown ID or entry is an error. This is how a binding is dropped on contract retirement and how a dangling locator is retired | agent | `CAP-REMOVE` |
| Declare coverage | Set `fully_bound` kinds and `curated` entries with their reason | agent | `CAP-COVERAGE` |
| Comments | Get and set the comment at a defined anchor (file header, a binding, a single locator or assertion, a coverage entry). Comments are round-tripped byte-for-byte and exposed in the JSON interface | agent, human | `CAP-COMMENT` |
| Path check (opt-in) | With a flag, additionally check that each locator `path` exists relative to the working directory. Off by default; the only filesystem read outside the target file | agent, human | `CAP-PATHCHECK` |
| Schema artifact | The canonical shape as a plain JSON Schema file, shipped in the repository with a SHA-256 checksum in the README. The executable embeds the same schema and never reads the external file. The tool prints the checksum of its embedded schema so the shipped file can be confirmed against the installed binary. The schema covers shape only; rules it cannot express are listed in the README beside the checksum and enforced by the built-in validator | converter, agent | `CAP-SCHEMA` |
| Self-description | Comprehensive plain-text `--help` at every level: `lspd --help`, `lspd <command> --help`, `lspd <command> <subcommand> --help`, so an agent learns the surface in one bounded call | agent, human | `CAP-HELP` |

Cross-cutting behaviour of every command: JSON on stdout by default, a readable rendering behind a flag; findings from the pre- and post-write validation ride in the same envelope; exit code 0 for clean or warnings only, 1 for validation errors, 2 for usage or I/O failure.

### Constraints & assumptions

- **Language and runtime.** Python, minimum 3.11 (so the operator's Debian 12 machine runs it on the system interpreter; a venv is used regardless). Supported platforms are whatever Python 3.11+ supports; none is targeted specifically.
- **Licence.** MIT. Dependencies are acceptable only while the MIT outcome holds. ruamel.yaml (MIT) is the YAML library, chosen for comment fidelity.
- **Distribution.** A GitHub repository that users clone and install into a user-space bin; binary name `lspd`. Private until the first release, public at the first release. Ships alongside Dictum v1.3.0 (pending on Dictum main at scaffold time). `[REVISIT]` this doc set is authored against v1.2.0; run the upgrade walk when v1.3.0 is vendored.
- **Schema.** Exactly the Dictum template's keys plus the two forms the standard names without shaping (`arm:` on an assertion; `owed:` for a deferred assertion). Anything else is an error. The schema is owned by this project; the operator is the author of the Dictum standard but this project acts as a **third party** and does not contribute the schema back into the template.
- **Versioning.** A change to the Dictum binding-map template is a new major version of `lspd`.
- **Ordering.** Edits preserve existing order and append; only `format` reorders.
- **Writes against an invalid file are allowed.** The rigid schema gives comments a defined place, so the tool can read and rewrite a file that carries findings; pre- and post-write findings are reported.
- **Performance.** No target (deferred concern).
- **Test fixtures** come only from public sources (Quality).

### Risks

- **Style lock-in.** The canonical style may not fit a future Dictum template. Mitigated by the major-version rule and by the schema artifact, which makes conversion a bounded job.
- **Comment fidelity.** A comment found between anchors must be relocated deterministically or rejected; a wrong rule loses information the wild maps demonstrably carry (deferrals, caveats, provenance notes).
- **Library formatting drift.** ruamel.yaml output could change across versions and break round-trip fidelity; pinned and guarded by golden tests (Integrations, Quality).
- **Model-authored code** raises the source-provenance obligation (Governance).
- **Performance in the wild** (deferred; re-entry note above).

## Open Questions

- `[GAP]` Should the file carry a schema-version field? Owned jointly with Domain & Data (`migrations-versioning`). Related: whether the JSON envelope carries a version field (Interfaces).
- `[GAP]` Name of the human-readable output flag (Interfaces).
- `[GAP]` Value vocabularies for `wire.casing`, `wire.enums`, `wire.dates`, and `compare_via`: open strings or a pinned set? The template only exemplifies values.
- `[GAP]` A binding on a kind the template excludes from the map (`CAP`, `POLICY`, `ROLE`, `LICENSE-TIER`, `PERF`): a warning, or silently allowed? Real maps carry `CAP` rows "for traceability".

## Dependencies & Cross-references

This concern consumes nothing minted elsewhere yet; it is the root of the ID web. Forward references it will be tightened against (described here, minted by the named concern):

- The command surface, JSON envelope, error catalog, and exit codes — minted by Interfaces & Contracts (`CLI-###`, `OUT-###`, `ERR-###`).
- The binding-map entities and the structural rules the validator enforces — minted by Domain & Data (`ENTITY-###`, `INV-###`).
- The single-file, structural-only, no-line-number, embedded-schema, and major-version decisions as cross-cutting ADRs — minted by Architecture (`ADR-###`).
- The E2E standard and golden-test definition that will make `SUCCESS-ROUNDTRIP` and `SUCCESS-BOUNDED-OUTPUT` measurable — minted by Quality & Testing.
- The ruamel.yaml dependency — minted by Integrations (`DEP-###`).
- The Dictum naming constraint — minted by Business & Legal (`LEGAL-###`).

## Examples / Worked scenarios

1. **An agent closes a slice.** A model has just realised `ENTITY-USER` in `src/models/user.py`. It runs `set ENTITY-USER` with the locator, then `add-assertion INV-USER-EMAIL-UNIQUE` with the verbatim test title and the run selector. Each call validates before and after, writes atomically, and returns the affected binding plus findings. The model never saw the file and read only two bindings' worth of output.
2. **A human tidies up.** After a week of agent edits, bindings sit in insertion order. The maintainer runs `format`; the file is rewritten in canonical order with every comment kept at its anchor. A second `format` changes nothing.
3. **A converter author.** Someone with a map in a different style downloads the JSON Schema from the repository, checks its SHA-256 against the README, and writes a converter. They then run `validate` on the result and fix the findings the schema could not express (a `role` without `wire`).
4. **A hand-over between models.** The next model starts with `lspd --help`, learns the surface in one call, runs `list --kind INV` to see what is asserted, and `get` on the one binding it needs. Its reads cost the same as the previous model's would have.
5. **Retirement.** A contract is tombstoned in the manifest by the doc-change-impact skill. The agent runs `remove <ID>`; the binding is gone, order elsewhere untouched, and the post-write validation confirms nothing else referenced that locator.

## Design Decisions

| Decision | Rationale |
|---|---|
| The LLM converts foreign-style maps; the tool only publishes the schema | Ingestion of unbounded styles is exactly the undecidable, style-dependent reading the tool exists to avoid; a schema plus rules is a bounded target a model can hit |
| Schema embedded in the binary; the shipped file is a copy with a checksum | The tool must be self-contained and deterministic; an external file could drift from the validator. The printed checksum makes the copy verifiable |
| Queries return exactly the requested entries | The observed token-waste patterns (grep-then-reread, whole-file reads) disappear when the tool, not the model, does the selection |
| `--help` is plain text at every level | Conventional, readable by both personas, and one bounded call is enough for an agent to learn the surface |
| No backups or undo | The file is version-controlled by its owner; a second history would be a stored duplicate the standard's Part 0.5 warns against |
| A template change is a new major version | One binary supports one shape; a version flag would reintroduce style variance inside the tool |
| Everything discussed is v1 | The operator marked nothing out; the surface is small enough to ship whole |

Cross-cutting decisions (single file, structural-only validation, no line numbers, ruamel.yaml, order preserved except on `format`) are recorded in Architecture's ADR register.

## Contracts
<!-- BUILD: rung Contract-grade — mint PERSONA-AGENT, PERSONA-HUMAN, PERSONA-CONVERTER; CAP-INIT … CAP-HELP; SUCCESS-ROUNDTRIP … SUCCESS-SCHEMA-MATCH on register lines (Part 5), each CAP with an explicit in/out mark and a success-criterion reference. -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade — each SUCCESS-### maps to an observable check (golden test, contract test, checksum comparison). -->

---
<!-- Status markers (subject, stay published): [GAP] [ASSUMPTION] [REVISIT] [FUTURE-SCOPE]. Build markers: these BUILD comments, stripped on publish. -->
