---
artifact: product-doc
role: concern
concern-id: quality-and-testing
behavior: core
trigger: always
in-scope-subaspects: [test-pyramid-test-types, coverage-map, real-flow-e2e-standard, quality-bars-gates, test-data-strategy]
current-rung: contract-grade
status: draft
version: 0.3.0
---

# Quality & Testing — dictum-binder

> One-line: five test tiers, a coverage map that gives every minted ID a test or a stated reason, 100 % coverage as a gate with written exclusions, zero retries, synthetic fixtures only, and an E2E standard that drives the installed `lspd` binary through every element in its default state.
<!-- BUILD: Contract-grade as of 2026-09-17 (doc-levelup, interactive, two rounds). Owns E2E-STANDARD and the coverage map (table-shaped; Contracts points to Requirements per Part 4). Rows for IDs minted later (DEP-*, SEC-*, LEGAL-*, POLICY-*) are added when those concerns reach Contract-grade — see the forward-reference note in the map. -->

## Purpose & Scope

Owns the test tiers, the coverage map over every in-scope contract ID, the real-flow E2E standard, the gates and the flake policy, and the fixture strategy. Delivery references `E2E-STANDARD` and the gates as its proof of done.

## Non-goals / Out-of-scope

- `specialized-testing` — `absent`: no performance (deferred at product level), security (no attack surface beyond a local file; Security's negative assertions are ordinary contract tests here), or accessibility (no UI) testing.
- `test-stage-fidelity-mapping` — `absent`: a single environment; there is no release-infra stage distinct from the merge gate (Operations is absent).
- `manual-exploratory` — `absent`: all gates are automated; no manual test programme exists. The one operator-recorded criterion (`SUCCESS-CROSS-MODEL`) is a product observation, not a test.
- No property-based or fuzz testing library: test dependencies are strictly MIT (`hypothesis` is MPL-2.0). `absent` by decision.
- No real-world maps as fixtures: adapting an existing map is always an LLM's job, never this repository's test data. `absent` by decision.
- No multi-version or multi-platform CI matrix: Python 3.11 on Ubuntu only. `deferred` — re-entry when a platform-specific defect is reported.

## Requirements

### Test pyramid / test types

Five tiers, all pytest, all run by one `pytest` invocation and by CI:

| Tier | Subject | Mechanism | Marker |
|---|---|---|---|
| **Unit** | `COMPONENT-MODEL`, `COMPONENT-VALIDATOR`, `COMPONENT-EMITTER`, `COMPONENT-LOADER`, `COMPONENT-SCHEMA` in isolation | direct calls; one test function per `INV-*`; table-driven grammar tests | `unit` |
| **Golden** | The canonical layout and round-trip fidelity | fixture files under `tests/fixtures/`; `load`→`emit` byte comparison; `format` fixpoint | `golden` |
| **Contract** | Every `CLI-*`, `OUT-*`, `ERR-*` | in-process `lspd.cli.main(argv)` with captured stdout/stderr and exit code, in a temporary directory; exact projection and key-order assertions | `contract` |
| **Fitness** | Architecture's structural rules | grep/AST over `src/lspd/`: import confinement, sole writer, acyclic pipeline | `fitness` |
| **E2E** | Every `CAP-*` through the real installed binary | `subprocess.run(["lspd", …])` per `E2E-STANDARD` | `e2e` |

### Coverage map

Every in-scope ID minted so far has a row; an ID with no observable check has an explicit `n/a — why`. IDs minted by concerns not yet at Contract-grade (Delivery, Security, Governance, Integrations, Business & Legal) get rows when minted — *described here, rows owed by those level-ups*.

| ID(s) | Test(s) | Tier |
|---|---|---|
| `PERSONA-AGENT`, `PERSONA-HUMAN`, `PERSONA-CONVERTER` | n/a — persona definitions admit no check; they are exercised indirectly by the E2E (agent, human via `--human`) and the schema tests (converter) | — |
| `CAP-INIT` … `CAP-HELP` (twelve) | one E2E journey per capability through the installed binary, default state first, then each optional flag (`E2E-STANDARD`) | E2E |
| `SUCCESS-ROUNDTRIP` | golden: `emit(load(F)) == F` for every canonical fixture; `format(format(F)) == format(F)` for every fixture | golden |
| `SUCCESS-COMPLETE-OPS` | contract: one test per row of Product's operations table, named after the row; a meta-test asserts every row has a test | contract |
| `SUCCESS-BOUNDED-OUTPUT` | contract: fifty-binding fixture; `get` of two IDs and `list --kind` yield exactly the selected entries and no other ID string | contract |
| `SUCCESS-CROSS-MODEL` | n/a — automated: an operator observation recorded per trial session (validate clean + `format --check` exit 0); the automated half is `CLI-FORMAT --check`'s contract test | — |
| `SUCCESS-SCHEMA-MATCH` | CI: SHA-256 of `lspd.schema.json` == `lspd schema --checksum` == README value | contract |
| `ENTITY-MAP`, `ENTITY-BINDING`, `ENTITY-LOCATOR`, `ENTITY-FIELD-LOCATOR`, `ENTITY-WIRE`, `ENTITY-ASSERTION`, `ENTITY-COVERAGE`, `ENTITY-COMMENT`, `ENTITY-FINDING` | unit: construction and `to_plain`/`from_plain` round trip per entity; golden: every entity appears in the canonical fixture | unit, golden |
| `ENTITY-CONTRACT-ID`, `ENTITY-PATH` | unit: table-driven accept/reject sets (Domain acceptance 2 and the path rules) | unit |
| `INV-ID-GRAMMAR` … `INV-BYTES` (sixteen write-gated) | unit: one violating synthetic fixture each → exactly that finding code at the expected anchor; one contract test each that the write path refuses the violating input | unit, contract |
| `INV-ID-UNIQUE` | unit: duplicate-key fixture fails to load (`ERR-PARSE`, exit 2) | unit |
| `INV-ROLE-REQUIRES-WIRE`, `INV-OWNED-TWICE` (advisory) | unit: warning finding, exit 0 | unit |
| `INV-CANONICAL-FIXPOINT` | golden (as `SUCCESS-ROUNDTRIP`) | golden |
| `INV-ORDER-PRESERVED` | contract: each `add-*`/`set`/`coverage`/`comment` on a multi-binding fixture; diff limited to the touched lines | contract |
| `INV-ATOMIC-WRITE` | unit: injected failure after the temporary file is written → target byte-identical, no temp file left | unit |
| `COMPONENT-CLI` … `COMPONENT-SCHEMA` (eight) | fitness: import confinement (ruamel only in `loader.py`, jsonschema only in `validator.py`), sole writer (`emitter.py`), acyclic left-to-right imports; unit per component as above | fitness, unit |
| `PATTERN-ERROR-ENVELOPE` | contract: one forced test per error source (Architecture acceptance 3); stderr empty without `--debug` | contract |
| `PATTERN-VALIDATE-AROUND-WRITE` | contract: pre-warning reported and write proceeds; shape-breaking input rejected with file bytes identical | contract |
| `PATTERN-ATOMIC-REPLACE` | as `INV-ATOMIC-WRITE` | unit |
| `PATTERN-EXIT-CODES` | contract: every `ERR-*` and finding-severity combination maps to its code; a meta-test enumerates the partition | contract |
| `PATTERN-OUTPUT-MODE` | contract: stdout holds exactly one JSON document; `--human` holds no JSON; `--help` and `schema` are raw | contract |
| `ADR-SINGLE-FILE`, `ADR-STRUCTURAL-ONLY`, `ADR-NO-SILENT-DEFAULTS`, `ADR-MAJOR-PER-TEMPLATE`, `ADR-NUMERIC-IDS-REJECTED`, `ADR-NO-LINE-NUMBERS`, `ADR-FORMAT-ONLY-REORDERS`, `ADR-INIT-REQUIRED` | covered by the `INV-*`/`CLI-*` tests that realise each decision (named in the test docstring) | unit, contract |
| `ADR-LOAD-RUAMEL-EMIT-OWN`, `ADR-JSONSCHEMA-RUNTIME`, `ADR-ARGPARSE`, `ADR-SCHEMA-SINGLE-SOURCE`, `ADR-NO-LOGGING` | fitness: import confinement; no `logging` import anywhere; `argparse` is the only CLI library; schema file regenerated and diffed in CI | fitness |
| `CLI-INIT` … `CLI-VERSION` (nineteen) | contract: happy path with exact `result`; **edge inputs per input-bearing element**: every optional flag *absent* (behaviour per its row), *empty string* (`ERR-USAGE`), and one *malformed* value (`ERR-USAGE` for enumerations and command-line grammar, `ERR-INPUT-INVALID` for domain values such as a `..` path) | contract |
| `OUT-ENVELOPE` … `OUT-SCHEMA` (thirteen) | contract: a test-side JSON Schema of each projection validates every captured output; key order asserted textually for the envelope | contract |
| `ERR-USAGE` … `ERR-INTERNAL` (nine) | contract: forced per the catalog's *Forced by* column; `details` shape asserted | contract |
| `E2E-STANDARD` | the E2E tier itself; a meta-test asserts every `CAP-*` has a journey | E2E |
| `DEP-*`, `SEC-*`, `POLICY-*`/provenance register, `LEGAL-*`, Delivery's slice/DoD contracts | rows owed by each concern's level-up (forward reference) | — |

### Real-flow E2E standard (`E2E-STANDARD`)

A journey exercises the product's **own code for real**: it runs the **installed `lspd` executable** (console script) as a subprocess with a real working directory and real files, and asserts the real stdout, stderr, exit code, and resulting file bytes. Nothing of the product is imported into the test process for the E2E tier; no in-process shortcut. There are no external dependencies to substitute and no login to bypass, so the substitution set is empty and stated as such. The CLI has no screens; the "operate every control" rule maps to: **every `CLI-*` element is invoked at least once in its default state (no optional flags) and once per optional flag**, asserting a non-error outcome where the contract promises one. Environment: locally, the editable install in the developer's venv; in CI, a wheel built from the commit and installed into a fresh venv before the tier runs. Rule (a) of the standard applies: a test may compute an expected canonical file through the pure `emitter` module in the test process, which injects nothing into the subprocess.

### Quality bars & gates

Merge gate, all required, run by CI on every push and pull request, Python 3.11 on Ubuntu:

1. `pytest` — all five tiers green.
2. **Coverage 100 %** across the union of all tiers (`coverage.py`, branch coverage on). Any excluded line or branch carries `# pragma: no cover — <reason>` on the same line; a fitness test fails on a pragma without a reason. The target is total coverage; a reason is the only way to fall short.
3. `ruff check` and `ruff format --check` clean.
4. `mypy --strict` clean over `src/` and `tests/`.
5. `lspd.schema.json` regenerated from `COMPONENT-SCHEMA` equals the committed file; its SHA-256 equals the README value.
6. Once the repository's own `bindings.yaml` exists (Delivery's dogfooding rule): `lspd validate` exit 0 and `lspd format --check` exit 0 on it.

**Flake / re-run policy:** zero retries, no quarantine list. A red run obligates investigation before any re-run. A genuine transient (re-run green with zero code change) is recorded as an incident with both run identifiers in the build-status record's notes (Delivery); the test is never quarantined. There is no measurement tier (Performance deferred), so no co-defined re-run rule exists.

### Test-data strategy

- **Synthetic only, hand-written**, under `tests/fixtures/`, each file opening with a header comment that states what it exercises. No real-world map is copied in; adapting one is an LLM's job outside this repository.
- **Golden canonical fixture**: Domain's *Persistence* example, verbatim, is `tests/fixtures/canonical.yaml`; it must validate clean and be a `format` fixpoint.
- **One violating fixture per write-gated `INV-*`** and one per `ERR-PARSE` condition, named after the code (`inv-no-line-numbers.yaml`, `err-parse-duplicate-key.yaml`).
- **A fifty-binding fixture** for bounded-output tests, generated deterministically by a test helper (not committed as a file) so its size can grow without repository churn.
- Test dependencies: `pytest`, `coverage`, `ruff`, `mypy`, `types-jsonschema` if needed — all MIT.

## Open Questions

None open.

## Dependencies & Cross-references

- Consumes every ID minted by Product, Domain, Architecture, and Interfaces (the map above); the `ERR-*` *Forced by* column and Architecture's acceptance list are the forcing sources.
- Referenced by Delivery (`E2E-STANDARD` and the six gates are the DoD; the incident record lives in build-status), Security (its negative assertions become contract tests here), Governance (gate 5 and the MIT-only test-dependency rule).

## Examples / Worked scenarios

1. **A new `INV-*` lands.** The author adds one violating fixture, one unit test asserting the finding at its anchor, and one contract test that the write path rejects it. The coverage-map meta-test fails until the map row exists.
2. **A pragma without a reason.** `# pragma: no cover` alone fails the fitness test; `# pragma: no cover — unreachable: argparse exits before this line` passes.
3. **E2E for `CAP-COMMENT`.** In a temp dir: `lspd init`; `lspd set ENTITY-X --json '…'`; `lspd comment set binding ENTITY-X --text "why"`; `lspd comment get binding ENTITY-X` → text equals; `lspd comment unset binding ENTITY-X`; `lspd comment get …` → exit 1 `ERR-NOT-FOUND`. The file's bytes are asserted at each step against the emitter-computed expectation.
4. **A transient red.** CI fails on a temp-dir cleanup race; re-run green with no diff. The incident and both run IDs go into `docs/IMPLEMENTATION.md`; the test stays.

## Design Decisions

| Decision | Rationale |
|---|---|
| Contract tier in-process, E2E tier via subprocess on the installed binary | In-process gives exact, fast assertions on projections; the subprocess tier proves the real executable, packaging, and console script |
| 100 % coverage with written exclusions rather than a threshold | The operator's rule: total coverage is the target, a reason is the only shortfall |
| No real-world fixtures | Keeps the test data free of provenance questions and keeps the product honest about not ingesting foreign styles |
| Test dependencies strictly MIT | The operator's rule extends the licence posture to the toolchain |
| Single Python version in CI | The operator's call; widened only on a reported platform defect |

## Contracts

The owned contracts are table- and prose-shaped and fully stated in Requirements (Part 4): the **coverage map**, **`E2E-STANDARD`**, and the **quality bars and gates** including the flake policy. No separate ID register exists for them; `E2E-STANDARD` is the one named contract and is referenced by Delivery under that name.

## Acceptance criteria

1. A meta-test enumerates every `CAP-*`, `SUCCESS-*`, `ENTITY-*`, `INV-*`, `COMPONENT-*`, `PATTERN-*`, `ADR-*`, `CLI-*`, `OUT-*`, `ERR-*` ID from the docs and asserts each has a row in a machine-readable copy of the coverage map (`tests/coverage_map.py`) and that every non-`n/a` row names at least one existing test function.
2. Every gate in *Quality bars* is a required CI job; a pull request cannot merge with any red.
3. The E2E tier invokes every `CLI-*` element in default state and per optional flag (meta-test over the recorded invocations).
4. Coverage report shows 100 % with every exclusion carrying a reason (fitness test).
5. `tests/fixtures/canonical.yaml` is byte-identical to the example block in Domain's *Persistence* section (a test extracts the block and compares).

---
<!-- Status markers (subject, stay published): [GAP] [ASSUMPTION] [REVISIT] [FUTURE-SCOPE]. Build markers: these BUILD comments, stripped on publish. -->
