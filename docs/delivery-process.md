---
artifact: product-doc
role: concern
concern-id: delivery-process
behavior: core
trigger: always
in-scope-subaspects: [vertical-slice-rule-slice-types, definition-of-done, build-playbook-sequence, work-item-hierarchy-slice-level, build-ready-gate-scope, verified-build-status-tracking, branching-release-versioning]
current-rung: sketch
status: draft
version: 0.1.0
---

# Delivery Process — dictum-binder

> One-line: headless vertical slices, an in-repo build-status record as the tracker, CI on GitHub Actions, and a first public release that ships alongside Dictum v1.3.0.
<!-- BUILD: Read ../dictum/concerns/11.6-delivery-process.md. Next rung: Specified — the slice rule, DoD checklist, playbook order in prose; Contract-grade — all concrete, plus the build-status record file (templates/build-status.template.md) created at first slice. -->

## Purpose & Scope

Owns how the tool gets built and proven: the slice rule, the Definition of Done, the build playbook, the work-item record, the build-ready gate scope, Verified tracking, and release/versioning.

## Non-goals / Out-of-scope

- `external-tracker-binding` — `absent`: no external tracker; the in-repo build-status record is the tracker. (GitHub Issues may be used for inbound demand after the repository goes public; that would enter as a tracker-binding declaration through the enhancement lifecycle, `[FUTURE-SCOPE]`.)

## Requirements

<!-- BUILD: Sketch outline. -->

**Slice rule & types**
- Every slice is `slice:headless` (no UI). Each realises its contract IDs through every layer they touch: model, validator, command, renderer, tests, and the binding-map entry.
- **Dogfooding is a DoD item:** this product maintains its own `bindings.yaml` with `lspd` itself once the tool can write; until then the first slices record bindings by hand in the canonical style.

**Definition of Done (candidates)**
- Contract test per CLI element; assertion per INV; E2E-STANDARD green for the capability; binding recorded; build-status row updated (an explicit exit criterion, per Dictum Part 10e).

**Build playbook (candidate order)**
1. Foundation: model + YAML round-trip + `init` + `validate` (the schema).
2. Query: `get`, `list`.
3. Write: `set`, `add-*`, `remove`, `coverage`, with pre/post validation and atomic replace.
4. Comments: anchors, round-trip, `comment get|set`, JSON exposure.
5. `format` and the opt-in path check.
6. Packaging, CI, README, first release.

**Work-item hierarchy**
- Slice level = one capability or one foundation step; recorded in the build-status record (`IMPLEMENTATION.md` beside this doc set, created at the first slice).

**Build-ready gate scope**
- Every in-scope concern at Contract-grade and published before the first slice is built (Dictum Part 10).

**Verified tracking**
- The build-status record, separate from the manifest (doc maturity ≠ implementation status).

**Branching / release / versioning**
- `main` is the integration branch; commits at checkpoints; never pushed without the operator's instruction.
- CI: GitHub Actions running pytest.
- Semantic versioning for the tool. The repository is private until the first release, then public. The first release is timed with Dictum v1.3.0.

## Open Questions

- `[GAP]` Release mechanics: a git tag only, or also a GitHub Release with an artifact.
- `[GAP]` Whether `pyproject.toml` versions are stamped by hand or derived from the tag.

## Dependencies & Cross-references
<!-- BUILD: rung Specified — Quality's E2E-STANDARD and coverage map; Architecture components per slice. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified. -->

## Design Decisions
<!-- BUILD: rung Specified → Contract-grade. -->

## Contracts
<!-- BUILD: rung Contract-grade — the slice rule/DoD/playbook are table- or prose-shaped; Contracts may point to Requirements (Part 4). -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
