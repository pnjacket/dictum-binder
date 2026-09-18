---
artifact: product-doc
role: concern
concern-id: integrations-and-external-dependencies
behavior: module
trigger: third-party-deps (manifest trait `third_party_deps`)
in-scope-subaspects: [per-external-contract, failure-modes-fallback-degradation, criticality, version-pinning]
current-rung: contract-grade
status: published
version: 1.1.0
---

# Integrations & External Dependencies — dictum-binder

> One-line: one runtime dependency, ruamel.yaml, app-fatal, pinned to a range, confined to one module, its failure surface mapped to the error model; two zero-dependency development tools, ruff and pyrefly; nothing else, by the MIT-only rule.

## Purpose & Scope

Owns the register of external dependencies with their contract, criticality, pinning, and failure modes. There are no external *services*; the module is triggered by a library dependency. Environment infrastructure (the interpreter, pip, the build backend, GitHub Actions) is not a dependency in this register (Governance's scope decision).

## Non-goals / Out-of-scope

- `fidelity-substitution` — `absent`: nothing to substitute; no test environment differs from production (Operations absent). The substitution set is empty and stated (Delivery).
- `data-mapping` — `absent`: no external data model; the YAML library returns the product's own document, converted at the Loader edge into the Model.
- No schema-validation, CLI-framework, test-runner, coverage, type-checker, or licence-scanner dependency: each candidate failed the MIT-only rule and was replaced by the standard library or own code (Governance's rejected list; Architecture `ADR-OWN-SHAPE-VALIDATOR`, `ADR-ARGPARSE`; Quality). `absent` by decision.
- No hash-pinned lock file: version ranges only. `absent` by the operator's decision.
- No network dependency of any kind at runtime (`SEC-ZERO-NETWORK`). `absent`.

## Requirements

### Per-external contract

One runtime dependency (`DEP-RUAMEL-YAML`) and two development-only tools (`DEP-RUFF`, `DEP-PYREFLY`), minted in Contracts. ruamel.yaml is imported by `COMPONENT-LOADER` only; the two tools are never imported by product code. Every declared dependency is MIT with zero transitive dependencies, so the resolved tree equals the declared list.

### Failure modes + fallback/degradation

- **ruamel.yaml parse failure** on the target file → `ERR-PARSE`, exit 2 (`SEC-FAIL-CLOSED`). No fallback parser; the failure is the contracted outcome.
- **ruamel.yaml import failure** (package missing or broken) → `ERR-INTERNAL`, exit 2, message naming the missing package. There is no degraded mode: without a YAML parser the tool has no function.
- **Behavioural drift across ruamel.yaml versions** (comment attachment, round-trip token layout): contained at the Loader edge; the Emitter never depends on the library (`ADR-LOAD-RUAMEL-EMIT-OWN`), so output bytes cannot drift. Loader-side drift is caught by the golden and seven-anchor round-trip tests (Quality) before a version bump lands.
- **ruff or pyrefly failure or drift**: affects CI gates only, never the product; a tool regression is pinned around, not worked around.

### Criticality

- The runtime dependency is **app-fatal**: absent or broken, no command except `schema`, `--help`, and `--version` can run, and those three do not import it (see `DEP-RUAMEL-YAML`).
- The two development tools are **gate-fatal** (a CI-only analogue of app-fatal): a missing tool fails the gate; the product is unaffected (see `DEP-RUFF`, `DEP-PYREFLY`).

### Version pinning

Ranges, declared once in `pyproject.toml`, re-confirmed at slice 1 against the then-current releases and moved only within the policy below:

- `ruamel.yaml >=0.19,<0.20` — the 0.19 series is the first with zero required dependencies (the C accelerator moved to an optional extra, never installed here). A minor-series bump (`<0.21`) is a deliberate change that must pass the golden tier and the licence gate first.
- `ruff` and `pyrefly`: pinned to a **minor series** current at slice 1 (`>=X.Y,<X.(Y+1)`), bumped deliberately; a formatter change alters `ruff format --check` results and must land as its own commit.
- The licence gate (`tools/licence_gate.py`, Governance) runs after every resolution, so no bump can introduce a non-MIT package.

## Open Questions

None open.

## Dependencies & Cross-references

- Consumed by Architecture (`COMPONENT-LOADER` is the sole importer; `ADR-LOAD-RUAMEL-EMIT-OWN`), Governance (`POLICY-INBOUND-MIT-ONLY`, the inbound register), Quality (golden tier as the compatibility gate; ruff and pyrefly as gates), Security (`SEC-FAIL-CLOSED`, `SEC-ZERO-NETWORK`), Delivery (no substitution set).
- References `ERR-PARSE`, `ERR-INTERNAL` (Interfaces).

## Examples / Worked scenarios

1. **A ruamel.yaml minor release.** Dependabot-style notice or a manual check finds 0.20. The implementer widens the range in a dedicated commit; CI runs the licence gate (still MIT, zero deps), the golden tier (round trip unchanged), and the seven-anchor tests (comment attachment unchanged). Green: the bump lands. Red on anchors: the bump is reverted and the finding recorded.
2. **ruamel.yaml missing at runtime.** A user installed the wheel into an environment where the dependency failed to build. `lspd validate` → `ERR-INTERNAL` with "ruamel.yaml is not importable"; `lspd --help` and `lspd schema` still work.

## Design Decisions

| Decision | Rationale |
|---|---|
| One runtime dependency, confined to one module | Comment-preserving YAML parsing is the one thing not worth writing; everything else is small enough to own, and confinement keeps the file bytes independent of the library |
| Ranges, no lock | The operator's call; with zero transitive dependencies a range resolves to one package, so a lock adds ceremony without pinning anything more |
| Gate-fatal as a criticality class for tools | The spec's three classes describe runtime; a CI tool's absence has the same shape at the gate and is worth naming |

## Contracts

Register form: table row, ID in the first cell.

| ID | Package · role | Contract (how used) | Auth | Failure modes → outcome | Fallback | Criticality | Fidelity substitution | Version pinning | Licence |
|---|---|---|---|---|---|---|---|---|---|
| `DEP-RUAMEL-YAML` | ruamel.yaml · runtime | Round-trip loader (`YAML(typ="rt")`) used by `COMPONENT-LOADER` to parse the target file's bytes into a comment-bearing object that the Loader converts into the Model; imported lazily inside `load()` so `schema`, `--help`, and `--version` never touch it; never used to emit | none | parse error → `ERR-PARSE` (exit 2); duplicate key → `ERR-PARSE`; import failure → `ERR-INTERNAL` (exit 2); version drift in comment attachment → caught by the golden and anchor tests before a bump lands | none — no parser, no product | app-fatal (except `schema`, `--help`, `--version`, which do not import it) | n/a — real everywhere; nothing substituted | `>=0.19,<0.20`; series bumps deliberate, gated by golden tier + licence gate | MIT, zero required dependencies |
| `DEP-RUFF` | ruff · development | Lint (`ruff check`) and format check (`ruff format --check`) as CI gates; never imported | none | tool missing or crashing → gate fails; product unaffected | none | gate-fatal | n/a | minor series current at slice 1, bumped deliberately | MIT, zero dependencies |
| `DEP-PYREFLY` | pyrefly · development | Static type check in strict mode (`pyrefly check`) over `src/` and `tests/` as a CI gate; never imported | none | as `DEP-RUFF` | none | gate-fatal | n/a | minor series current at slice 1, bumped deliberately | MIT, zero dependencies |

## Acceptance criteria

1. `pyproject.toml` declares exactly one runtime dependency, `ruamel.yaml`, with the range above, and exactly two development dependencies, `ruff` and `pyrefly` (a fitness test parses the file).
2. The resolved environment in CI contains no distribution other than those three, the project itself, and environment infrastructure (the licence-gate script also emits the resolved list; a test asserts the set).
3. `ERR-PARSE` and `ERR-INTERNAL` forcings for `DEP-RUAMEL-YAML` exist (Interfaces' catalog; a test monkeypatches the import to fail and asserts `ERR-INTERNAL` while `--help` still succeeds).
4. Every `DEP-*` row has a non-empty criticality and pinning cell (review check; the spec's under-specification finding).

