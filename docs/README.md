# dictum-binder — documentation set

Derived index. **`manifest.yaml` is authoritative**; regenerate or update this file in lockstep whenever the manifest changes (the `doc-maturity-auditor` flags drift between the two).

Documented to Dictum **v1.2.0** (`authored_against`), per-concern packaging. Scaffolded 2026-09-17 by `doc-scaffold` from an interactive intake interview. No product code and no `bindings.yaml` exist yet — the binding map is authored during the build.

| Concern | In scope | Location | Current rung | Target |
|---|---|---|---|---|
| Product & Requirements | yes | [product-and-requirements.md](product-and-requirements.md) | contract-grade | contract-grade |
| Domain & Data | yes | [domain-and-data.md](domain-and-data.md) | sketch | contract-grade |
| Architecture | yes | [architecture.md](architecture.md) | sketch | contract-grade |
| Interfaces & Contracts (CLI) | yes | [interfaces-and-contracts.md](interfaces-and-contracts.md) | sketch | contract-grade |
| Quality & Testing | yes | [quality-and-testing.md](quality-and-testing.md) | sketch | contract-grade |
| Delivery Process | yes | [delivery-process.md](delivery-process.md) | sketch | contract-grade |
| Security & Privacy | yes (baseline) | [security-and-privacy.md](security-and-privacy.md) | sketch | contract-grade |
| Governance & Compliance | yes (baseline, raised) | [governance-and-compliance.md](governance-and-compliance.md) | sketch | contract-grade |
| Integrations & External Dependencies | yes (module) | [integrations-and-external-dependencies.md](integrations-and-external-dependencies.md) | sketch | contract-grade |
| Business & Legal | yes (module, minimal) | [business-and-legal.md](business-and-legal.md) | sketch | contract-grade |
| User Experience | no — absent (no UI) | — | — | — |
| Operations & Infrastructure | no — absent (no service) | — | — | — |
| Observability & Monitoring | no — absent (no service) | — | — | — |
| Performance & Scalability | no — **deferred** (operator's call; re-entry note in Product Non-goals) | — | — | — |
| Accessibility & i18n | no — absent (no UI, single locale) | — | — | — |

**Traits:** CLI only · not interactive · not deployed · persists one file · one third-party dependency (ruamel.yaml) · no perf target · single locale · non-commercial (MIT) · unregulated · no security risk factors · model-authored code.

**Build-ready gate:** every in-scope concern at contract-grade and published. Product & Requirements is at contract-grade (2026-09-17, still draft); the rest are at sketch. Next: `doc-levelup` in dependency order — Domain & Data / Architecture → Interfaces → downstream.
