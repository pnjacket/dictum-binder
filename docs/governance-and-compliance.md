---
artifact: product-doc
role: concern
concern-id: governance-and-compliance
behavior: baseline
trigger: always
in-scope-subaspects: [license-ip-compliance, source-provenance]
current-rung: sketch
status: draft
version: 0.1.0
---

# Governance & Compliance — dictum-binder

> One-line: MIT outbound, MIT-compatible inbound, and — because the code is model-authored — an explicit first-party source-provenance discipline with a detection pass owed.
<!-- BUILD: Read ../dictum/concerns/11.8-governance-and-compliance.md. The code_authorship: model-authored trait raises source-provenance depth: SOURCE: markers at any copied/adapted site plus a best-effort detection pass whose residual is recorded, never read as cleared. -->

## Purpose & Scope

Owns the licence and IP posture at the dependency boundary and the first-party source-provenance register.

## Non-goals / Out-of-scope

- `data-handling-policy` — `absent`: no classified data (Domain).
- `audit-requirements` — `absent`: single-user local tool; no accountability regime.
- `compliance-framework-mapping` — `absent`: not regulated.
- `records-retention-data-residency` — `absent`: no records held.
- `consent-management` — `absent`: no personal data.

## Requirements

<!-- BUILD: Sketch outline. -->

**Licence & IP compliance**
- Outbound: MIT. This is a hard constraint from the operator: dependencies are acceptable only while the MIT outcome holds.
- Inbound: ruamel.yaml (MIT); pytest (MIT, dev only). Any future dependency is checked against the outbound stance before adoption.
- Vendored Dictum material under `dictum/`: prose CC BY 4.0, templates MIT, attribution to David H. Jung and the Dictum contributors, as recorded in `CLAUDE.md`. The vendored copy is never edited.

**Source provenance (first-party)**
- Code is model-authored. Every non-trivial unit copied, ported, or adapted from an external source carries `SOURCE: <origin> — <license>` at the site (the v1.3.0 separator form).
- A best-effort detection pass for undeclared reproduction of licensed source is owed before the first release; its residual is recorded in this doc, never read as "cleared".

## Open Questions

- `[GAP]` The concrete detection method for the source-provenance pass (a search of distinctive strings, a licence-scanner, a manual review) is not chosen.

## Dependencies & Cross-references
<!-- BUILD: rung Specified — Integrations DEP-### register; Business & Legal for the Dictum naming constraint. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified. -->

## Design Decisions
<!-- BUILD: rung Specified → Contract-grade. -->

## Contracts
<!-- BUILD: rung Contract-grade — the source-provenance register (table-shaped; Contracts may point to Requirements). -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade — dependency licence check in CI; provenance pass recorded. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
