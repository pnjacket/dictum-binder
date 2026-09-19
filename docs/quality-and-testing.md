---
artifact: product-doc
role: concern
concern-id: quality-and-testing
behavior: core
trigger: always
in-scope-subaspects: [test-pyramid-test-types, coverage-map, real-flow-e2e-standard, quality-bars-gates, test-data-strategy]
current-rung: contract-grade
status: published
version: 2.0.0
---

# Quality & Testing — dictum-binder

> One-line: five `unittest` tiers, a coverage map that gives every minted ID a test or a stated reason, 100 % line coverage from the standard library's `trace` as a gate with written exclusions, `pyrefly` strict and ruff, zero retries, synthetic fixtures only, an MIT-only toolchain, and an E2E standard that drives the installed dictum-binder binary through every element in its default state.

## Purpose & Scope

Owns the test tiers, the coverage map over every in-scope contract ID, the real-flow E2E standard, the gates and the flake policy, and the fixture strategy. Delivery references `E2E-STANDARD` and the gates as its proof of done.

## Non-goals / Out-of-scope

- `specialized-testing` — `absent`: no performance (deferred at product level), security (no attack surface beyond a local file; Security's negative assertions are ordinary contract tests here), or accessibility (no UI) testing.
- `test-stage-fidelity-mapping` — `absent`: fidelity does not differ by tier or environment — Operations' map has two environments (`ENV-LOCAL`, `ENV-CI`) with identical, fully real fidelity and an empty substitution set, so there is nothing to map per stage.
- `manual-exploratory` — `absent`: all gates are automated; no manual test programme exists. The one operator-recorded criterion (`SUCCESS-CROSS-MODEL`) is a product observation, not a test.
- No property-based or fuzz testing library: test dependencies are strictly MIT (`hypothesis` is MPL-2.0). `absent` by decision.
- **No branch coverage.** Every branch-capable coverage tool (coverage.py, slipcover, covers) is Apache-licensed and excluded by the MIT-only rule; the standard library's `trace` measures lines only. `deferred` — `[FUTURE-SCOPE]` re-entry: an MIT-licensed branch-coverage tool, or an own `sys.settrace`-based tracer if the operator judges it worth a few hundred lines.
- No pytest, mypy, coverage.py, or pip-licenses: each pulls a non-MIT package (`packaging`, `pygments`, `typing_extensions`, `pathspec`, `prettytable`) or is non-MIT itself. `absent` by the MIT-only rule (Governance).
- No real-world maps as fixtures: adapting an existing map is always an LLM's job, never this repository's test data. `absent` by decision.
- No multi-version or multi-platform CI matrix: Python 3.11 on Ubuntu only. `deferred` — re-entry when a platform-specific defect is reported.

## Requirements

### Test pyramid / test types

Five tiers, all standard-library `unittest`, one package directory per tier under `tests/`, all run by one `python -m unittest discover` invocation and by CI:

| Tier | Subject | Mechanism | Directory |
|---|---|---|---|
| **Unit** | `COMPONENT-MODEL`, `COMPONENT-VALIDATOR`, `COMPONENT-EMITTER`, `COMPONENT-LOADER`, `COMPONENT-SCHEMA` in isolation | direct calls; one test method per `INV-*`; `subTest` for table-driven grammar cases | `tests/unit/` |
| **Golden** | The canonical layout and round-trip fidelity | fixture files under `tests/fixtures/`; `load`→`emit` byte comparison; `format` fixpoint | `tests/golden/` |
| **Contract** | Every `CLI-*`, `OUT-*`, `ERR-*` | in-process `dbind.cli.main(argv)` with captured stdout/stderr and exit code, in a `tempfile` directory; exact projection and key-order assertions | `tests/contract/` |
| **Fitness** | Structural and textual rules owned by Architecture, Interfaces (the `--help` tree walk), Security, Governance, Business & Legal, Delivery, Operations, and Integrations | `ast` and text over the repository: import confinement, sole writer, acyclic pipeline, pragma reasons, forbidden imports (`SEC-*`), `SOURCE:` marker form (`POLICY-SOURCE-MARKER`), README/LICENSE/`--help` wording (`LEGAL-DICTUM-NAMING`), `pyproject.toml` dependency set (`DEP-*`), build-status record ↔ tests ↔ minted IDs (Delivery) | `tests/fitness/` |
| **E2E** | Every `CAP-*` through the real installed binary | `subprocess.run(["dbind", …])` per `E2E-STANDARD` | `tests/e2e/` |

### Coverage map

Every in-scope ID has a row; an ID with no observable check has an explicit `n/a — why`. IDs sit in the last column so that no row is a register line (Part 5 rule 2: a coverage table never mints).

| Tier | Test(s) | ID(s) covered |
|---|---|---|
| — | n/a — persona definitions admit no check; they are exercised indirectly by the E2E (agent, human via `--human`) and the schema tests (converter) | `PERSONA-AGENT`, `PERSONA-HUMAN`, `PERSONA-CONVERTER` |
| E2E | one E2E journey per capability through the installed binary, default state first, then each optional flag (`E2E-STANDARD`) | `CAP-INIT` … `CAP-HELP` (twelve) |
| golden | golden: `emit(load(F)) == F` for every canonical fixture; `format(format(F)) == format(F)` for every fixture | `SUCCESS-ROUNDTRIP` |
| contract | contract: one test per row of Product's operations table, named after the row; a meta-test asserts every row has a test | `SUCCESS-COMPLETE-OPS` |
| contract | contract: fifty-binding fixture; `get` of two IDs and `list --kind` yield exactly the selected entries and no other ID string | `SUCCESS-BOUNDED-OUTPUT` |
| — | n/a — not automated: an operator observation recorded per trial session (validate clean + `format --check` exit 0); the automated half is `CLI-FORMAT --check`'s contract test | `SUCCESS-CROSS-MODEL` |
| contract | CI: SHA-256 of `dbind.schema.json` == `dbind schema --checksum` == README value | `SUCCESS-SCHEMA-MATCH` |
| unit, golden | unit: construction and `to_plain`/`from_plain` round trip per entity; golden: every entity appears in the canonical fixture | `ENTITY-MAP`, `ENTITY-BINDING`, `ENTITY-LOCATOR`, `ENTITY-FIELD-LOCATOR`, `ENTITY-WIRE`, `ENTITY-ASSERTION`, `ENTITY-COVERAGE`, `ENTITY-COMMENT`, `ENTITY-FINDING` |
| unit | unit: table-driven accept/reject sets (Domain acceptance 2 and the path rules) | `ENTITY-CONTRACT-ID`, `ENTITY-PATH` |
| unit | unit: one violating synthetic fixture each → exactly that finding code at the expected anchor, exit 1 (the unit half **completes** each of these; the write-path refusal of the same violation is proven by the `CLI-SET`/`CLI-ADD-*` edge-input rows, `ERR-INPUT-INVALID`, and by `ERR-FILE-INVALID`'s forcing) | the fifteen write-gated `INV-*` (`INV-ID-GRAMMAR`, `INV-SCHEMA-VERSION`, `INV-CLOSED-KEYS`, `INV-NO-LINE-NUMBERS`, `INV-PATH-FORM`, `INV-SYMBOL-NONEMPTY`, `INV-ROLE-VALUES`, `INV-WIRE-SUBSET`, `INV-ASSERTION-SHAPE`, `INV-FIELD-NAME`, `INV-COVERAGE-WELLFORMED`, `INV-LOCATOR-UNIQUE`, `INV-ASSERTION-UNIQUE`, `INV-COMMENT-ANCHORED`, `INV-COMMENT-TEXT`) |
| unit, contract | unit: a fixture with one missing path passes without `--check-paths` and yields the error with it; contract: `add-locator` of a missing path is refused only with the flag (`ERR-INPUT-INVALID`) | `INV-PATH-EXISTS` |
| unit | unit: duplicate-key fixture fails to load (`ERR-PARSE`, exit 2) | `INV-ID-UNIQUE` |
| unit | unit: warning finding, exit 0 | `INV-ROLE-REQUIRES-WIRE`, `INV-OWNED-TWICE`, `INV-BYTES`, the trailing-whitespace arm of `INV-COMMENT-TEXT` (advisory) |
| golden | golden (as `SUCCESS-ROUNDTRIP`) | `INV-CANONICAL-FIXPOINT` |
| contract | contract: each `add-*`/`set`/`coverage`/`comment` on a multi-binding **canonical** fixture; diff limited to the touched lines (a non-canonical fixture also shows the layout repair; order still preserved) | `INV-ORDER-PRESERVED` |
| unit | unit: injected failure after the temporary file is written → target byte-identical, no temp file left | `INV-ATOMIC-WRITE` |
| fitness, unit | fitness: import confinement (ruamel only in `loader.py`, no other third-party import anywhere), sole writer (`emitter.py`), acyclic imports with flow components importing none of each other and only `cli.py` orchestrating; unit per component as above; one unit test per rule-table entry in `COMPONENT-SCHEMA` proving the generated checker and the generated JSON Schema agree on that entry | `COMPONENT-CLI` … `COMPONENT-SCHEMA` (eight) |
| contract | contract: one forced test per error source (Architecture acceptance 3); stderr empty without `--debug` | `PATTERN-ERROR-ENVELOPE` |
| contract | contract: pre-warning reported and write proceeds; shape-breaking input rejected with file bytes identical | `PATTERN-VALIDATE-AROUND-WRITE` |
| unit | as `INV-ATOMIC-WRITE` | `PATTERN-ATOMIC-REPLACE` |
| contract | contract: every `ERR-*` and finding-severity combination maps to its code, plus the one contracted exception (`format --check` with `changed: true` → 1); a meta-test enumerates the partition | `PATTERN-EXIT-CODES` |
| contract | contract: stdout holds exactly one JSON document; `--human` holds no JSON; `--help` and `schema` are raw | `PATTERN-OUTPUT-MODE` |
| unit, contract | covered by the `INV-*`/`CLI-*` tests that realise each decision (named in the test docstring); `ADR-FORMAT-ONLY-REORDERS`'s proof lands with `CLI-FORMAT` in slice 5 and is recorded as *proof owed by slice 5* in slice 1's row | `ADR-SINGLE-FILE`, `ADR-STRUCTURAL-ONLY`, `ADR-NO-SILENT-DEFAULTS`, `ADR-MAJOR-PER-TEMPLATE`, `ADR-NUMERIC-IDS-REJECTED`, `ADR-NO-LINE-NUMBERS`, `ADR-FORMAT-ONLY-REORDERS`, `ADR-INIT-REQUIRED` |
| fitness | fitness: import confinement; no `logging` import anywhere; `argparse` is the only CLI library; schema file regenerated and diffed in CI | `ADR-LOAD-RUAMEL-EMIT-OWN`, `ADR-OWN-SHAPE-VALIDATOR`, `ADR-ARGPARSE`, `ADR-SCHEMA-SINGLE-SOURCE`, `ADR-NO-LOGGING` |
| contract | contract: happy path with exact `result`; **edge inputs per input-bearing element**: every optional flag *absent* (behaviour per its row), *empty string* (`ERR-USAGE`), and one *malformed* value (`ERR-USAGE` for enumerations and command-line grammar, `ERR-INPUT-INVALID` for domain values such as a `..` path) | `CLI-INIT` … `CLI-VERSION` (nineteen) |
| contract | contract: a test-side shape assertion per projection (own helper, fixed key sets and types) checks every captured output; key order asserted textually for the envelope | all sixteen `OUT-*` (`OUT-ENVELOPE` … `OUT-SCHEMA`, incl. `OUT-INIT-RESULT`) |
| contract | contract: forced per the catalog's *Forced by* column; `details` shape asserted | `ERR-USAGE` … `ERR-INTERNAL` (twelve, incl. `ERR-SCHEMA-VERSION` and `ERR-FILE-INVALID`) |
| contract, fitness | contract and fitness: exactly the *Forced by* and *Realised by* checks in each Security row | `SEC-ZERO-NETWORK` … `SEC-TRUST-BOUNDARY` (eight) |
| E2E | the E2E tier itself; a meta-test asserts every `CAP-*` has a journey | `E2E-STANDARD` (the real-flow standard defined below, referenced by Delivery as its proof of done) |
| fitness, contract | fitness: `pyproject.toml` declares exactly ruamel.yaml `>=0.19,<0.20` as the runtime dependency (Integrations acceptance 1); contract: import of ruamel monkeypatched to fail → `ERR-INTERNAL` while `--help` succeeds (Integrations acceptance 3) | `DEP-RUAMEL-YAML` |
| fitness | fitness: `pyproject.toml` and `.github/workflows/ci.yml` pin every tool within its `TOOL-*` row's series; the workflow names the seven gate steps, the 3.11 interpreter, and the fresh-venv wheel install for E2E (Operations acceptance 1–2) | `ENV-LOCAL`, `ENV-CI`, `TOOL-RUFF`, `TOOL-PYREFLY`, `TOOL-SETUPTOOLS`, `TOOL-ACTIONS-CHECKOUT`, `TOOL-ACTIONS-SETUP-PYTHON` |
| fitness | fitness: `LICENSE` is the MIT text with the contracted copyright line; README names MIT and the contribution sentence | `POLICY-OUTBOUND-MIT`, `POLICY-CONTRIBUTIONS-MIT` |
| fitness (gate 7) | the licence gate `tools/licence_gate.py` over the resolved environment on every CI run; a unit test feeds it a fake BSD distribution and a fake metadata-less one and asserts both fail | `POLICY-INBOUND-MIT-ONLY` |
| fitness | fitness: every `SOURCE:` comment in the tree parses to the token form and names `MIT` | `POLICY-SOURCE-MARKER` |
| — | n/a — not automated: a release-slice review whose record (the filled provenance register with a non-empty residual) is the check; the release-gate checklist requires it (Delivery) | `POLICY-PROVENANCE-PASS` |
| fitness | fitness: README contains the independence sentence verbatim; conformance phrases use the versioned form; `--help` and README never say certified/official/endorsed about Dictum outside that sentence; no paragraph in the **product artifacts** (`README.md`, `docs/`, `src/`, `tests/`, `tools/`) duplicates the standard's normative text — `dictum/`, `.claude/`, and `CLAUDE.md` are vendored Dictum tooling and exempt | `POLICY-NAMING-ENFORCEMENT`, `LEGAL-DICTUM-NAMING` |
| fitness | fitness: Delivery acceptance 2, 3, 6 (record ↔ tests ↔ minted IDs; docs never trail code) | Delivery's slice rule, DoD, playbook, build-status record |

### Real-flow E2E standard

`E2E-STANDARD` — a journey exercises the product's **own code for real**: it runs the **installed `dbind` executable** (console script) as a subprocess with a real working directory and real files, and asserts the real stdout (parsed as JSON: codes, `ok`, `result`; message texts are not contracted), stderr, exit code, and resulting file bytes (exact). Nothing of the product is imported into the test process for the E2E tier; no in-process shortcut. There are no external dependencies to substitute and no login to bypass, so the substitution set is empty and stated as such. The CLI has no screens; the "operate every control" rule maps to: **every `CLI-*` element is invoked at least once in its default state (no optional flags) and once per element-specific optional flag**; each global option other than `--help`/`--version` (`--file`, `--human`, `--check-paths`, `--no-size-limit`, `--debug`) is invoked at least once on a representative element, and `--check-paths` additionally on `validate` and on one write; asserting a non-error outcome where the contract promises one. Environment: `ENV-LOCAL` (the editable install in the developer's venv) and `ENV-CI` (a wheel built from the commit and installed into a fresh venv before the tier runs — the binding fidelity for the staged DoD), per Operations' map. The E2E tier invokes the executable by its explicit path inside the environment under test (`<venv>/bin/dbind`), never via `PATH`, so the dev install can never shadow the wheel install. Rule (a) of the standard applies: a test may compute an expected canonical file through the pure `emitter` module in the test process, which injects nothing into the subprocess.

### Quality bars & gates

Merge gate — **seven gates**, all required, run by CI on every push and pull request, Python 3.11 on Ubuntu:

1. `python -m unittest discover` — all five tiers green. **Mid-build scoping**: every full-set meta-test (coverage-map completeness, E2E journey per capability, operations-table rows, `--help` tree walk, record ↔ minted IDs) is scoped to the IDs whose completing slice the build-status record marks **Built**; an ID whose slice is not yet Built is skipped and listed, never failed. From the release slice on the scope is the full set.
2. **Line coverage 100 %** across the union of all tiers, measured by the standard library's `trace` module (`python -m trace --count --missing`) and reduced by an own report script (`tools/coverage_report.py`, standard library only) that lists every unexecuted line of `src/dbind/`. Any excluded line carries `# pragma: no cover — <reason>` on the same line; a fitness test fails on a pragma without a reason. Branch coverage is not measured (Non-goals). The target is total line coverage; a reason is the only way to fall short.
3. `ruff check` and `ruff format --check` clean.
4. `pyrefly check` in strict mode clean over `src/` and `tests/`.
5. `dbind.schema.json` regenerated from `COMPONENT-SCHEMA` equals the committed file; its SHA-256 equals the README value.
6. Once the repository's own `bindings.yaml` exists (Delivery's dogfooding rule, the release slice): `dbind validate` exit 0 and `dbind format --check` exit 0 on it. Until the file exists the CI step is skipped and says so; from the release slice on it is required.
7. **Licence gate**: `tools/licence_gate.py` over the resolved environment passes — every declared distribution and its transitive tree is exactly MIT (`POLICY-INBOUND-MIT-ONLY`, Governance). The `SOURCE:` marker check (`POLICY-SOURCE-MARKER`) and the naming check (`POLICY-NAMING-ENFORCEMENT`) run inside gate 1's fitness tier.

**Flake / re-run policy:** zero retries, no quarantine list. A red run obligates investigation before any re-run. A genuine transient (re-run green with zero code change) is recorded as an incident with both run identifiers in the build-status record's notes (Delivery); the test is never quarantined. There is no measurement tier (Performance deferred), so no co-defined re-run rule exists.

### Test-data strategy

- **Synthetic only, hand-written**, under `tests/fixtures/`, each file opening with a header comment that states what it exercises. No real-world map is copied in; adapting one is an LLM's job outside this repository.
- **Golden canonical fixture**: Domain's *Persistence* example, verbatim, is `tests/fixtures/canonical.yaml`; it must validate clean and be a `format` fixpoint.
- **One violating fixture per write-gated `INV-*`** and one per `ERR-PARSE` condition, named after the code (`inv-no-line-numbers.yaml` uses the `:NN` suffix form and `inv-comment-text.yaml` the bare-`#` form so that exactly one code fires; a `lines:` key also fires `INV-CLOSED-KEYS` and a trailing-whitespace comment also fires `INV-BYTES`; `err-parse-duplicate-key.yaml`).
- **A fifty-binding fixture** for bounded-output tests, generated deterministically by a test helper (not committed as a file) so its size can grow without repository churn.
- Test and tooling dependencies: `ruff` and `pyrefly` only — both MIT with zero transitive dependencies. Test runner, coverage, licence gate, and shape assertions are standard library or own code.

## Open Questions

None open.

## Dependencies & Cross-references

- Consumes every ID minted by Product, Domain, Architecture, and Interfaces (the map above); the `ERR-*` *Forced by* column and Architecture's acceptance list are the forcing sources.
- Referenced by Delivery (`E2E-STANDARD` and the seven gates are the DoD; the incident record lives in build-status), Security (its negative assertions become contract tests here), Governance (gate 7 is `POLICY-INBOUND-MIT-ONLY`; the `SOURCE:` and naming checks in the fitness tier are `POLICY-SOURCE-MARKER` and `POLICY-NAMING-ENFORCEMENT`; the MIT-only test-dependency rule), Business & Legal (`LEGAL-DICTUM-NAMING`'s check), Integrations (`DEP-*` fitness), Operations (`ENV-*`/`TOOL-*` fitness; gates 3 and 4 are `TOOL-RUFF` and `TOOL-PYREFLY`).

## Examples / Worked scenarios

1. **A new `INV-*` lands.** The author adds one violating fixture, one unit test asserting the finding at its anchor, and one contract test that the write path rejects it. The coverage-map meta-test fails until the map row exists.
2. **A pragma without a reason.** `# pragma: no cover` alone fails the fitness test; `# pragma: no cover — unreachable: argparse exits before this line` passes.
3. **E2E for `CAP-COMMENT`.** In a temp dir: `dbind init`; `dbind set ENTITY-X --json '…'`; `dbind comment set binding ENTITY-X --text "why"`; `dbind comment get binding ENTITY-X` → text equals; `dbind comment unset binding ENTITY-X`; `dbind comment get …` → exit 1 `ERR-NOT-FOUND`. The file's bytes are asserted at each step against the emitter-computed expectation.
4. **A transient red.** CI fails on a temp-dir cleanup race; re-run green with no diff. The incident and both run IDs go into `docs/IMPLEMENTATION.md`; the test stays.

## Design Decisions

| Decision | Rationale |
|---|---|
| Contract tier in-process, E2E tier via subprocess on the installed binary | In-process gives exact, fast assertions on projections; the subprocess tier proves the real executable, packaging, and console script |
| 100 % coverage with written exclusions rather than a threshold | The operator's rule: total coverage is the target, a reason is the only shortfall |
| No real-world fixtures | Keeps the test data free of provenance questions and keeps the product honest about not ingesting foreign styles |
| Test dependencies strictly MIT | The operator's rule extends the licence posture to the toolchain |
| Single Python version in CI | The operator's call; widened only on a reported platform defect |
| `unittest`, `trace`, `pyrefly`, own scripts instead of pytest, coverage.py, mypy, pip-licenses | The MIT-only rule over the full declared tree (Governance) excludes each of the usual tools; the standard library and two zero-dependency MIT tools cover every gate except branch coverage, which is deferred with its reason |

## Contracts

The owned contracts are table- and prose-shaped and fully stated in Requirements (Part 4): the **coverage map**, **`E2E-STANDARD`**, and the **quality bars and gates** including the flake policy. No separate ID register exists for them; `E2E-STANDARD` is the one named contract and is referenced by Delivery under that name.

## Acceptance criteria

1. A meta-test enumerates every `PERSONA-*`, `CAP-*`, `SUCCESS-*`, `ENTITY-*`, `INV-*`, `COMPONENT-*`, `PATTERN-*`, `ADR-*`, `CLI-*`, `OUT-*`, `ERR-*`, `SEC-*`, `POLICY-*`, `DEP-*`, `ENV-*`, `TOOL-*`, `LEGAL-*` ID **from the register lines of the owning docs' Contracts sections only** — a register line being a Contracts-section table row whose first cell's first token is the ID (never from prose, list items, or code blocks, where illustrative IDs such as `ENTITY-USER` appear as example data), plus `E2E-STANDARD`, and asserts each has a row in a machine-readable copy of the coverage map (`tests/coverage_map.py`) and that every non-`n/a` row names at least one existing test function.
2. Every one of the seven gates in *Quality bars* is a required CI job; a pull request cannot merge with any red.
3. The E2E tier invokes every `CLI-*` element in default state and per optional flag (meta-test over the recorded invocations).
4. The `trace`-based line-coverage report shows 100 % with every exclusion carrying a reason (fitness test).
5. `tests/fixtures/canonical.yaml` is byte-identical to the example block in Domain's *Persistence* section (a test extracts the block and compares).

