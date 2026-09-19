---
artifact: product-doc
role: concern
concern-id: operations-and-infrastructure
behavior: module
trigger: a product whose staged DoD needs an ENV fidelity map — activated by the dev-toolchain register (11.10 owned contract 4), not by a running service
in-scope-subaspects: [environments-fidelity-map, provisioning-iac]
current-rung: contract-grade
status: published
version: 1.0.1
---

# Operations & Infrastructure — dictum-binder

> One-line: no running service and nothing to deploy, but a toolchain to pin — so this concern holds the two-environment fidelity map (developer venv, CI runner), both fully real with an empty substitution set and no auth surface, the reproducible provisioning of each, and the version-pinned build/test tooling register that Integrations may not hold.

## Purpose & Scope

Owns the environment fidelity map (`ENV-*`) and the dev-toolchain register (`TOOL-*`), plus the reproducible provisioning of the two environments. Pulled in on 2026-09-17 after the second doc-maturity audit: the vendored spec says a set must not scope Operations out while pinning build or test tooling, because a pin is an environment fact. The residual is small and fully asserted; nothing here deploys, scales, or recovers anything.

## Non-goals / Out-of-scope

- `per-component-deployment-spec` — `absent`: nothing is deployed; the product is a wheel a user installs into their own environment, and the install is Delivery's release gate.
- `runtime-configuration` — `absent`: no configuration surface exists — no config file, no environment variable, no `CONFIG-*` (Interfaces Non-goals, `SEC-NO-AMBIENT-CONFIG`).
- `runbooks` — `absent`: nothing to deploy, roll back, or recover; the repository's git history is the only recovery.
- `backups-disaster-recovery` — `absent`: the product holds no state of its own.
- `capacity-scaling` — `absent`: no service; Performance is deferred at product level.
- `network-ingress-edge` — `absent`: no network (`SEC-ZERO-NETWORK`).

## Requirements

### Environments + fidelity map

Two environments, both running the product's own real code with **no substitutions** (the substitution set is empty and stated) and **no auth surface**. Fidelity does not differ by test tier: every tier in both environments runs the same real code. The gate's E2E fidelity is `ENV-CI`. Platform/host dimension: CPython 3.11 on Linux; nothing else is targeted (Product constraints).

### Provisioning / IaC

- Provisioning of `ENV-LOCAL`: two commands from a clean checkout — create a venv on Python 3.11 and `pip install -e .[dev]`. No other setup exists.
- Provisioning of `ENV-CI`: `.github/workflows/ci.yml` — Ubuntu runner, `actions/setup-python` at 3.11, `pip install .[dev]` for gates 1–5 and 7, and a fresh venv with the built wheel for the E2E tier. The workflow file is the reproducible definition; a change to it is a change to `ENV-CI`.

### Dev-toolchain register

Five build/test-time tools, each version-pinned to the series current on 2026-09-18 (verified against PyPI and GitHub releases), none imported by product code, none a runtime dependency: ruff, pyrefly, setuptools, and the two GitHub Actions the workflow uses. The pins are the `TOOL-*` rows in Contracts; a series bump is a doc-led change to the row first, then to the file; Integrations owns the one runtime `DEP-*` only. The standard library's `unittest` and `trace` are not tools to pin — they are fixed by the interpreter version, which is the platform dimension of `ENV-*`.

## Open Questions

None open.

## Dependencies & Cross-references

- Delivery's staged DoD references `ENV-LOCAL` and `ENV-CI` (merge gate runs in both; release gate binds to `ENV-CI`); Quality's `E2E-STANDARD` names them; Quality's gates 3 and 4 run `TOOL-RUFF` and `TOOL-PYREFLY`; Governance's `POLICY-INBOUND-MIT-ONLY` covers every `TOOL-*` that is a declared Python dependency (ruff, pyrefly); setuptools and the GitHub Actions are infrastructure under Governance's scope statement but are still pinned here.
- Supersedes the retired `DEP-RUFF` and `DEP-PYREFLY` (Integrations; manifest tombstones).
- `SEC-NO-AMBIENT-CONFIG`, `SEC-ZERO-NETWORK` (Security) justify three of the scope-outs.

## Examples / Worked scenarios

1. **A new contributor.** Clones, creates a 3.11 venv, runs `pip install -e .[dev]` and `python -m unittest discover`. That is `ENV-LOCAL` in full; nothing else to configure.
2. **A ruff minor bump.** The implementer edits the `TOOL-RUFF` pin in `pyproject.toml` in its own commit; CI runs gate 3 with the new formatter; a formatting diff is fixed in the same commit or the bump is reverted. The `TOOL-RUFF` row's pin cell is updated by the same change (doc-led: the row first, then the file).

## Design Decisions

| Decision | Rationale |
|---|---|
| Operations in, on a two-row map and a five-row register | The spec's rule: a toolchain to pin is an environment fact; scoping Ops out while pinning tooling is not allowed. The residual is asserted fully rather than waived |
| Two environments, not one | Local and CI differ in provisioning (editable install vs wheel install) even though fidelity is identical; the E2E tier's wheel install is a real difference worth naming |
| GitHub Actions and setuptools as `TOOL-*` | They are pinned build-time tooling with versions that change behaviour; the register's job is to hold every such pin in one place |

## Contracts

Register form: table row, ID in the first cell.

### Environment fidelity map

| ID | Environment | Per-external fidelity | `auth:` | Platform / host | Test tiers | Provisioning |
|---|---|---|---|---|---|---|
| `ENV-LOCAL` | The developer's machine | no externals; nothing substituted; own code real | `n/a — no auth surface exists` | CPython 3.11 (floor), Linux (Debian 12 in practice); other platforms supported wherever Python 3.11 runs but untested (Quality's deferred CI matrix) | all five tiers, E2E against the editable install's console script | clean checkout → venv on 3.11 → `pip install -e .[dev]` |
| `ENV-CI` | GitHub Actions runner | no externals; nothing substituted; own code real | `n/a — no auth surface exists` | CPython 3.11, `ubuntu-latest` | gates 1–7 against `pip install .[dev]`; E2E tier against a fresh venv with the built wheel; gate 6 skipped until `bindings.yaml` exists. **This is the binding fidelity for the staged DoD** | `.github/workflows/ci.yml` |

### Dev-toolchain register

| ID | Tool · role | Pin (policy) | Runs in | Licence |
|---|---|---|---|---|
| `TOOL-RUFF` | ruff · lint and format check (Quality gate 3) | `>=0.16,<0.17` (0.16.8 current on 2026-09-18), bumped deliberately in its own commit | `ENV-LOCAL`, `ENV-CI` | MIT, zero dependencies |
| `TOOL-PYREFLY` | pyrefly · static type check, strict (Quality gate 4) | `>=1.3,<1.4` (1.3.1 current on 2026-09-18), bumped deliberately | `ENV-LOCAL`, `ENV-CI` | MIT, zero dependencies |
| `TOOL-SETUPTOOLS` | setuptools · build backend (`[build-system] requires`) | `>=84,<85` (84.0.0 current on 2026-09-18) | both (build) | MIT (vendors `packaging`; infrastructure under Governance's scope statement) |
| `TOOL-ACTIONS-CHECKOUT` | `actions/checkout` · CI checkout step | `@v7` (v7.0.1 current on 2026-09-18) | `ENV-CI` | MIT |
| `TOOL-ACTIONS-SETUP-PYTHON` | `actions/setup-python` · CI interpreter step | `@v7` (v7.0.0 current on 2026-09-18), `python-version: "3.11"` | `ENV-CI` | MIT |

## Acceptance criteria

1. A fitness test asserts `pyproject.toml` pins `ruff` to `>=0.16,<0.17` and `pyrefly` to `>=1.3,<1.4` (dev extra) and `setuptools` to `>=84,<85` (build-system), and that `.github/workflows/ci.yml` uses `actions/checkout@v7`, `actions/setup-python@v7`, and `python-version: "3.11"` — the values in the `TOOL-*` rows.
2. The workflow file names the seven gate steps and the E2E tier's fresh-venv wheel install (`ENV-CI` row).
3. The manifest's `out_of_scope_subaspects` for this concern equals the six keys in Non-goals, each `absent` with its trait fact (Part 9 residual checklist).
4. `DEP-RUFF` and `DEP-PYREFLY` are tombstoned in the manifest with `superseded_by` pointing here, and no live reference to either remains in `docs/` — "live" meaning a mention not in the same sentence as *retired*, *tombstone*, or *superseded*.
