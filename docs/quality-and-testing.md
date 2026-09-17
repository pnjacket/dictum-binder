---
artifact: product-doc
role: concern
concern-id: quality-and-testing
behavior: core
trigger: always
in-scope-subaspects: [test-pyramid-test-types, coverage-map, real-flow-e2e-standard, quality-bars-gates, test-data-strategy]
current-rung: sketch
status: draft
version: 0.1.0
---

# Quality & Testing — dictum-binder

> One-line: how the canonical style is proven — unit tests on the grammar and schema, golden round-trip tests over real binding maps, and a real-flow E2E that drives the installed `lspd` binary.
<!-- BUILD: Read ../dictum/concerns/11.5-quality-and-testing.md. Next rung: Specified — prose per sub-aspect; Contract-grade — the coverage map over every in-scope ID + the E2E-STANDARD definition + gate thresholds. -->

## Purpose & Scope

Owns the test types, the coverage map over every in-scope contract, the real-flow E2E standard, the quality gates, and the fixture strategy.

## Non-goals / Out-of-scope

- `specialized-testing` — `absent`: no performance (deferred at product level), security (no attack surface beyond a local file), or accessibility (no UI) testing.
- `test-stage-fidelity-mapping` — `absent`: a single environment; there is no release-infra stage distinct from the merge gate (Operations is absent).
- `manual-exploratory` — `absent`: all gates are automated; no manual test programme exists.

## Requirements

<!-- BUILD: Sketch outline. -->

**Test pyramid**
- Unit: ID grammar, schema rules (each finding code), comment-anchor handling, ordering rules.
- Golden round-trip: load → dump on each fixture must be byte-identical when the fixture is already canonical, and `format` must be idempotent.
- Contract: one test per CLI command exercising the JSON envelope and exit code.
- Real-flow E2E: invoke the installed `lspd` binary in a temporary directory over a fixture map; own code real, nothing substituted (there are no externals to substitute).

**Coverage map**
- Every `INV-###` has one assertion; every `CLI-###` a contract test; every `ERR-###` a forced-condition test; every `CAP-###` an E2E path.

**Quality bars & gates**
- Merge gate: pytest green on CI (GitHub Actions) on Python 3.11 and the latest stable.
- `[GAP]` Linters or type checkers as gates: not decided.

**Test-data strategy**
- Fixtures come only from **public** sources: the jotdo example map in the Dictum repository and the dictum-lab fixture, both public. Maps from private adoption repositories are not used, even anonymised.
- Synthetic fixtures cover every finding code and every non-conforming construct seen in the survey (line-numbered locators, unknown keys, `role` without `wire`, comments between anchors).

## Open Questions

- `[GAP]` Linter/type-checker gates.
- `[GAP]` Whether the E2E standard installs the package into a fresh venv per run or reuses the CI environment.

## Dependencies & Cross-references
<!-- BUILD: rung Specified — CAP/INV/CLI/ERR IDs; Delivery references E2E-STANDARD as proof of done. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified. -->

## Design Decisions
<!-- BUILD: rung Specified → Contract-grade. -->

## Contracts
<!-- BUILD: rung Contract-grade — E2E-STANDARD; the coverage map may be a pointer to Requirements (Part 4 shape-adaptive). -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
