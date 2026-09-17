---
artifact: product-doc
role: concern
concern-id: integrations-and-external-dependencies
behavior: module
trigger: third_party_deps
in-scope-subaspects: [per-external-contract, failure-modes-fallback-degradation, criticality, version-pinning]
current-rung: sketch
status: draft
version: 0.1.0
---

# Integrations & External Dependencies — dictum-binder

> One-line: one runtime dependency, ruamel.yaml, accepted for comment-preserving YAML; app-fatal, pinned, with its failure surface mapped to the error model.
<!-- BUILD: Read ../dictum/concerns/11.12-integrations-and-external-dependencies.md. Small register: one DEP-### at runtime, dev-only tooling listed for the licence check. -->

## Purpose & Scope

Owns the register of external dependencies, their criticality, pinning, and failure modes. There are no external *services*; the module is triggered by a library dependency.

## Non-goals / Out-of-scope

- `fidelity-substitution` — `absent`: nothing to substitute; no test environment differs from production (Operations absent).
- `data-mapping` — `absent`: no external data model; the YAML library returns the product's own document.

## Requirements

<!-- BUILD: Sketch outline. -->

**Per-external contract (candidates)**
- ruamel.yaml — runtime; round-trip loader/dumper with comment preservation. The only component that imports it is the YAML I/O component (Architecture). Assumptions to verify at Specified: comment attachment semantics for flow-style sequences, and stability of dump formatting across versions.
- pytest — development only.
- `[GAP]` a CLI framework, if one is chosen (Architecture open question).

**Criticality**
- ruamel.yaml: app-fatal; there is no degraded mode without a YAML parser.

**Failure modes**
- Parse failure → structured error, exit 2 (Security's fail-closed assertion).
- Dump formatting drift across ruamel.yaml versions → caught by the golden round-trip tests (Quality); mitigated by pinning.

**Version pinning**
- Pinned to a compatible range in `pyproject.toml`; the golden tests are the compatibility gate for any bump.

## Open Questions

- `[GAP]` Exact ruamel.yaml version range.

## Dependencies & Cross-references
<!-- BUILD: rung Specified — Governance licence register; Architecture YAML I/O component. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified. -->

## Design Decisions
<!-- BUILD: rung Specified → Contract-grade. -->

## Contracts
<!-- BUILD: rung Contract-grade — DEP-### register lines. -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
