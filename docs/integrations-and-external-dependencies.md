---
artifact: product-doc
role: concern
concern-id: integrations-and-external-dependencies
behavior: module
trigger: third-party-deps (manifest trait `third_party_deps`)
in-scope-subaspects: [per-external-contract, failure-modes-fallback-degradation, criticality, version-pinning]
current-rung: contract-grade
status: draft
version: 1.1.0
---

# Integrations & External Dependencies — dictum-binder

> One-line: one runtime dependency, ruamel.yaml, app-fatal, pinned to a range, confined to one module, its failure surface mapped to the error model; nothing else, by the MIT-only rule. Build/test-time tooling is not a dependency here — it is Operations' `TOOL-*` register.

## Purpose & Scope

Owns the register of external **runtime** dependencies with their contract, criticality, pinning, and failure modes. There are no external *services*; the module is triggered by a library dependency. Build/test-time-only tooling (ruff, pyrefly, setuptools, the GitHub Actions) is **not** a `DEP-*` per the spec; its version-pinned register is Operations' `TOOL-*`. `DEP-RUFF` and `DEP-PYREFLY`, minted here on 2026-09-17, were retired the same day and superseded by `TOOL-RUFF` and `TOOL-PYREFLY` (manifest tombstones).

## Non-goals / Out-of-scope

- `fidelity-substitution` — `absent`: nothing to substitute; both environments in Operations' map (`ENV-LOCAL`, `ENV-CI`) run the one dependency real. The substitution set is empty and stated there and in Delivery.
- `data-mapping` — `absent`: no external data model; the YAML library returns the product's own document, converted at the Loader edge into the Model.
- No schema-validation, CLI-framework, test-runner, coverage, type-checker, or licence-scanner dependency: each candidate failed the MIT-only rule and was replaced by the standard library or own code (Governance's rejected list; Architecture `ADR-OWN-SHAPE-VALIDATOR`, `ADR-ARGPARSE`; Quality). `absent` by decision.
- No hash-pinned lock file: version ranges only. `absent` by the operator's decision.
- No network dependency of any kind at runtime (`SEC-ZERO-NETWORK`). `absent`.

## Requirements

### Per-external contract

One runtime dependency (`DEP-RUAMEL-YAML`), minted in Contracts, imported by `COMPONENT-LOADER` only. It is MIT with zero transitive dependencies, so the resolved runtime tree is exactly one package. Development tooling is registered as `TOOL-*` in Operations and still falls under Governance's MIT-only rule where it is a declared Python dependency.

### Failure modes + fallback/degradation

- **ruamel.yaml parse failure** on the target file → `ERR-PARSE`, exit 2 (`SEC-FAIL-CLOSED`). No fallback parser; the failure is the contracted outcome.
- **ruamel.yaml import failure** (package missing or broken) → `ERR-INTERNAL`, exit 2, message naming the missing package. There is no degraded mode: without a YAML parser the tool has no function.
- **Behavioural drift across ruamel.yaml versions** (node line/column reporting, which the Loader's line-adjacency anchoring relies on; parse-error classes): contained at the Loader edge; the Emitter never depends on the library (`ADR-LOAD-RUAMEL-EMIT-OWN`), so output bytes cannot drift. Loader-side drift is caught by the golden and seven-anchor round-trip tests (Quality) before a version bump lands.
- Tool failures (ruff, pyrefly) are Operations' `TOOL-*` concern: they affect CI gates only, never the product.

### Criticality

- The runtime dependency is **app-fatal**: absent or broken, no command except `schema`, `--help`, and `--version` can run, and those three do not import it (see `DEP-RUAMEL-YAML`).

### Version pinning

Ranges, declared once in `pyproject.toml`, re-confirmed at slice 1 against the then-current releases and moved only within the policy below:

- `ruamel.yaml >=0.19,<0.20` — the 0.19 series is the first with zero required dependencies (the C accelerator moved to an optional extra, never installed here). A minor-series bump (`<0.21`) is a deliberate change that must pass the golden tier and the licence gate first.
- The licence gate (`tools/licence_gate.py`, Governance) runs after every resolution, so no bump can introduce a non-MIT package.

## Open Questions

None open.

## Dependencies & Cross-references

- Consumed by Architecture (`COMPONENT-LOADER` is the sole importer; `ADR-LOAD-RUAMEL-EMIT-OWN`), Governance (`POLICY-INBOUND-MIT-ONLY`, the inbound register), Quality (golden tier as the compatibility gate), Security (`SEC-FAIL-CLOSED`, `SEC-ZERO-NETWORK`), Delivery and Operations (empty substitution set in `ENV-LOCAL`/`ENV-CI`); the tooling gates are Operations' `TOOL-RUFF`/`TOOL-PYREFLY`.
- References `ERR-PARSE`, `ERR-INTERNAL` (Interfaces).

## Examples / Worked scenarios

1. **A ruamel.yaml minor release.** Dependabot-style notice or a manual check finds 0.20. The implementer widens the range in a dedicated commit; CI runs the licence gate (still MIT, zero deps), the golden tier (round trip unchanged), and the seven-anchor tests (comment attachment unchanged). Green: the bump lands. Red on anchors: the bump is reverted and the finding recorded.
2. **ruamel.yaml missing at runtime.** A user installed the wheel into an environment where the dependency failed to build. `lspd validate` → `ERR-INTERNAL` with "ruamel.yaml is not importable"; `lspd --help` and `lspd schema` still work.

## Design Decisions

| Decision | Rationale |
|---|---|
| One runtime dependency, confined to one module | Comment-preserving YAML parsing is the one thing not worth writing; everything else is small enough to own, and confinement keeps the file bytes independent of the library |
| Ranges, no lock | The operator's call; with zero transitive dependencies a range resolves to one package, so a lock adds ceremony without pinning anything more |

## Contracts

Register form: table row, ID in the first cell.

| ID | Package · role | Contract (how used) | Auth | Failure modes → outcome | Fallback | Criticality | Fidelity substitution | Version pinning | Licence |
|---|---|---|---|---|---|---|---|---|---|
| `DEP-RUAMEL-YAML` | ruamel.yaml · runtime | Round-trip loader (`YAML(typ="rt")`) used by `COMPONENT-LOADER` to parse the target file's bytes into a node tree with line positions from which the Loader builds the Model and derives comment anchors by line adjacency; imported lazily inside `load()` so `schema`, `--help`, and `--version` never touch it; never used to emit | none | parse error → `ERR-PARSE` (exit 2); duplicate key → `ERR-PARSE`; import failure → `ERR-INTERNAL` (exit 2); version drift in node position reporting or error classes → caught by the golden and anchor tests before a bump lands | none — no parser, no product | app-fatal (except `schema`, `--help`, `--version`, which do not import it) | n/a — real everywhere; nothing substituted | `>=0.19,<0.20`; series bumps deliberate, gated by golden tier + licence gate | MIT, zero required dependencies |

## Acceptance criteria

1. `pyproject.toml` declares exactly one runtime dependency, `ruamel.yaml`, with the range above (a fitness test parses the file); the development extra holds only tools registered as `TOOL-*` in Operations.
2. The resolved environment in CI contains no distribution other than ruamel.yaml, the `TOOL-*` Python tools (ruff, pyrefly), the project itself, and environment infrastructure (the licence-gate script also emits the resolved list; a test asserts the set).
3. `ERR-PARSE` and `ERR-INTERNAL` forcings for `DEP-RUAMEL-YAML` exist (Interfaces' catalog; a test monkeypatches the import to fail and asserts `ERR-INTERNAL` while `--help` still succeeds).
4. The one `DEP-*` row has a non-empty criticality and pinning cell (review check; the spec's under-specification finding).

