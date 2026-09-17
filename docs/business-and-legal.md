---
artifact: product-doc
role: concern
concern-id: business-and-legal
behavior: module
trigger: distributed (open source), plus an ip-trademark constraint (the Dictum naming policy)
in-scope-subaspects: [eula-tos, ip-trademark-constraints]
current-rung: sketch
status: draft
version: 0.1.0
---

# Business & Legal — dictum-binder

> One-line: non-commercial and distributed — the MIT licence is the only terms of use, and the one legal constraint is Dictum's naming policy, honoured as a third party.
<!-- BUILD: Read ../dictum/concerns/11.15-business-and-legal.md. Mostly-scoped-out concern: reach Contract-grade by fully asserting the residual (Part 9 checklist). -->

## Purpose & Scope

Owns the terms under which the tool is distributed and the trademark-style constraint that applies to its naming and positioning relative to Dictum.

## Non-goals / Out-of-scope

- `commercial-licensing-model-tiers` — `absent`: non-commercial.
- `tier-capability-entitlements-limits` — `absent`: no tiers.
- `pricing` — `absent`: free.
- `business-slas` — `absent`: no service, no support commitment.
- `contractual-agreements` — `absent`: none.
- `ip-copyright-provenance` — `absent`: no declared don't-derive-from constraint; the always-on first-party attestation is Governance's `source-provenance`.

## Requirements

<!-- BUILD: Sketch outline. -->

**EULA / ToS**
- The MIT licence text in `LICENSE` is the entire terms of use. No additional EULA.

**IP / trademark constraint (to become a `LEGAL-###`)**
- Dictum's naming policy (`TRADEMARK.md` in the Dictum repository) permits using the name to *refer* to the standard in tooling and asks that adaptations not present themselves as the official standard. This tool refers to Dictum, implements nothing of the standard's text, and claims no endorsement or certification. The operator is the author of the standard but this project deliberately acts as a **third party**: the canonical binding-map schema is owned here and is not contributed back into the Dictum template.
- Conformance is described factually and with a version ("for Dictum v1.3.0 binding maps"), never as certification.

## Open Questions

- `[GAP]` Whether the README should carry an explicit "not the official Dictum project" line, or whether the naming policy's courtesy is satisfied by the factual description alone.

## Dependencies & Cross-references
<!-- BUILD: rung Specified — Governance (enforcement of the licence posture); Product constraints. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified. -->

## Design Decisions
<!-- BUILD: rung Specified → Contract-grade. -->

## Contracts
<!-- BUILD: rung Contract-grade — LEGAL-### for the naming constraint. -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade — residual fully asserted per the Part 9 checklist. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
