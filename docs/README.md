# dictum-binder — documentation set

Derived index. **`manifest.yaml` is authoritative**; regenerate or update this file in lockstep whenever the manifest changes (the `doc-maturity-auditor` flags drift between the two).

Documented to Dictum **v1.2.0** (`authored_against`), per-concern packaging. Scaffolded 2026-09-17 by `doc-scaffold` from an interactive intake interview and levelled to contract-grade; publish state is tracked in the status line below. No product code and no `bindings.yaml` exist yet — the binding map is authored during the build (the release slice, by decision).

| Concern | In scope | Location | Current rung | Target |
|---|---|---|---|---|
| Product & Requirements | yes | [product-and-requirements.md](product-and-requirements.md) | contract-grade | contract-grade |
| Domain & Data | yes | [domain-and-data.md](domain-and-data.md) | contract-grade | contract-grade |
| Architecture | yes | [architecture.md](architecture.md) | contract-grade | contract-grade |
| Interfaces & Contracts (CLI) | yes | [interfaces-and-contracts.md](interfaces-and-contracts.md) | contract-grade | contract-grade |
| Quality & Testing | yes | [quality-and-testing.md](quality-and-testing.md) | contract-grade | contract-grade |
| Delivery Process | yes | [delivery-process.md](delivery-process.md) | contract-grade | contract-grade |
| Security & Privacy | yes (baseline) | [security-and-privacy.md](security-and-privacy.md) | contract-grade | contract-grade |
| Governance & Compliance | yes (baseline, raised) | [governance-and-compliance.md](governance-and-compliance.md) | contract-grade | contract-grade |
| Integrations & External Dependencies | yes (module) | [integrations-and-external-dependencies.md](integrations-and-external-dependencies.md) | contract-grade | contract-grade |
| Business & Legal | yes (module, minimal) | [business-and-legal.md](business-and-legal.md) | contract-grade | contract-grade |
| User Experience | no — absent (no UI) | — | — | — |
| Operations & Infrastructure | yes (module, minimal — pulled in 2026-09-17: a toolchain to pin is an ENV fact) | [operations-and-infrastructure.md](operations-and-infrastructure.md) | contract-grade | contract-grade |
| Observability & Monitoring | no — absent (no service) | — | — | — |
| Performance & Scalability | no — **deferred** (operator's call; re-entry note in Product Non-goals) | — | — | — |
| Accessibility & i18n | no — absent (no UI, single locale) | — | — | — |

**Traits:** CLI only · not interactive · not deployed (but a toolchain to pin, so Operations is in minimally) · persists one file · one runtime dependency (ruamel.yaml) plus five pinned build/test tools registered in Operations, all MIT · no perf target · single locale · non-commercial (MIT) · unregulated · no security risk factors · model-authored code.

**Build-ready gate:** every in-scope concern at contract-grade and published. **Build-ready (published 2026-09-18).** Eleven in-scope concerns at contract-grade and `published`: ten docs at 1.2.0, Operations & Infrastructure at 1.0.0. Reached through ten `doc-maturity-auditor` passes and four `implementation-planner` runs, every finding applied through `doc-feature` (the sixth pass pulled Operations in and retired `DEP-RUFF`/`DEP-PYREFLY` for `TOOL-RUFF`/`TOOL-PYREFLY`; the tenth audit and the fourth planner run were clean or closed). Build status lives in [IMPLEMENTATION.md](IMPLEMENTATION.md): all six slices Built and Verified at `release` (tag `v1.0.0`, 2026-09-18) of the playbook in [delivery-process.md](delivery-process.md).
