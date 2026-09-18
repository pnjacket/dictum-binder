# dictum-binder — documentation set

Derived index. **`manifest.yaml` is authoritative**; regenerate or update this file in lockstep whenever the manifest changes (the `doc-maturity-auditor` flags drift between the two).

Documented to Dictum **v1.2.0** (`authored_against`), per-concern packaging. Scaffolded 2026-09-17 by `doc-scaffold` from an interactive intake interview, levelled to contract-grade and published the same day. No product code and no `bindings.yaml` exist yet — the binding map is authored during the build (the release slice, by decision).

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
| Operations & Infrastructure | no — absent (no service; staged DoD needs no fidelity map — both trigger halves evaluated) | — | — | — |
| Observability & Monitoring | no — absent (no service) | — | — | — |
| Performance & Scalability | no — **deferred** (operator's call; re-entry note in Product Non-goals) | — | — | — |
| Accessibility & i18n | no — absent (no UI, single locale) | — | — | — |

**Traits:** CLI only · not interactive · not deployed · persists one file · one runtime dependency (ruamel.yaml) plus ruff and pyrefly for development, all MIT · no perf target · single locale · non-commercial (MIT) · unregulated · no security risk factors · model-authored code.

**Build-ready gate:** every in-scope concern at contract-grade and published. **Build-ready.** All ten in-scope concerns are at contract-grade and **published** (2026-09-17, doc version 1.0.0 each) after a `doc-maturity-auditor` pass whose findings were applied. Next: slice 1 of the build playbook in [delivery-process.md](delivery-process.md), which creates `docs/IMPLEMENTATION.md`.
