---
artifact: product-doc
role: concern
concern-id: architecture
behavior: core
trigger: always
in-scope-subaspects: [component-decomposition-responsibilities, component-interactions-data-flow, cross-cutting-patterns, technology-choices, adr-register]
current-rung: sketch
status: draft
version: 0.1.0
---

# Architecture — dictum-binder

> One-line: a single-process Python CLI: parse the one file with comment fidelity, validate it against a rigid schema, mutate an in-memory model, validate again, write atomically, render findings and results as JSON.
<!-- BUILD: Read ../dictum/concerns/11.3-architecture.md. Next rung: Specified — component prose + data flow; Contract-grade — COMPONENT-###, PATTERN-###, ADR-### register lines. -->

## Purpose & Scope

Owns the component decomposition, the data flow, the cross-cutting patterns, and the ADR register. The product is small in code and single-process; what needs architecture is the strict separation between the **YAML layer** (the only place ruamel.yaml is touched), the **schema and model** (the canonical style), and the **command surface** (what LLMs call).

## Non-goals / Out-of-scope

- `boundaries-isolation-model` — `absent`: one process, one trust domain, one user; the only boundary is the process boundary to the caller (Security owns it).
- `logical-deployment-topology` — `absent`: not distributed; a user-space binary.
- `scalability-resilience-patterns` — `absent` here because Performance & Scalability is deferred at the product level (see Product Non-goals); nothing to place.

## Requirements

<!-- BUILD: Sketch outline. -->

**Component decomposition (candidates)**
- *CLI front* — argument parsing, command dispatch, exit codes.
- *YAML I/O* — load and dump with comment round-trip (ruamel.yaml); the only component that knows YAML syntax. Owns atomic replace.
- *Model* — the typed in-memory binding map (Domain entities), including comment anchors.
- *Schema validator* — the structural rule set; produces Findings; runs before and after every write.
- *Commands* — one unit per capability (init, validate, format, get, list, set, add-*, remove, coverage, comment).
- *Renderer* — JSON envelope by default; human-readable rendering behind a flag.

**Interactions / data flow**
- Read path: file → YAML I/O → Model → (Validator) → Command → Renderer → stdout.
- Write path: file → YAML I/O → Model → Validator (pre) → Command mutates Model → Validator (post) → YAML I/O atomic replace → Renderer (findings from both passes) → stdout.
- `format` is the only path that reorders the Model before dumping.

**Cross-cutting patterns (candidates)**
- One JSON result envelope for every command, carrying findings (pre and post) alongside the payload.
- Exit code policy: 0 clean or warnings only, 1 validation errors, 2 usage or I/O failure.
- Structured errors never escape as Python tracebacks.

**Technology choices**
- Python ≥ 3.11; ruamel.yaml for round-trip YAML; pytest for tests; `pyproject.toml` packaging installable with pipx or uv tool.
- `[GAP]` CLI framework: standard-library argparse (zero extra dependency) or a third-party library. Not decided.

**ADR register (candidates)**
- Single file by rule (multi-map explicitly unsupported).
- Structural-only validation; no reading of manifest, docs, or code.
- ruamel.yaml dependency accepted for comment fidelity (MIT preserved).
- No line numbers anywhere.
- Order preserved on edit; reorder only on explicit `format`.
- Missing file requires `init`; no auto-create in the first version.
- Opt-in path-existence check is the only filesystem read outside the map.

## Open Questions

- `[GAP]` CLI framework (see Technology choices).
- `[GAP]` Whether the Model is exposed as an importable Python API in addition to the CLI. Product scoped `library-sdk-surface` out as absent for now; recorded here because the package layout depends on it.

## Dependencies & Cross-references
<!-- BUILD: rung Specified — Domain entities; Interfaces CLI elements attributed to components; Integrations DEP for ruamel.yaml. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified — trace one `add-assertion` call through the write path. -->

## Design Decisions
<!-- BUILD: rung Specified → Contract-grade — promote the ADR candidates above to ADR-### with rationale. -->

## Contracts
<!-- BUILD: rung Contract-grade — COMPONENT-###, PATTERN-###, ADR-### register lines. -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
