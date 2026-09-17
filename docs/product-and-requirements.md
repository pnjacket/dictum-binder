---
artifact: product-doc
role: concern
concern-id: product-and-requirements
behavior: core
trigger: always
in-scope-subaspects: [problem-motivation, target-users-personas, goals-success-criteria, capability-register, constraints-assumptions, risks]
current-rung: sketch
status: draft
version: 0.1.0
---

# Product & Requirements — dictum-binder

> One-line: a deterministic command-line tool, installed as `lspd`, that is the reader, writer, and validator of a Dictum project's `bindings.yaml`, so that the binding map has one canonical style regardless of which LLM or human touches it.
<!-- BUILD: Read ../dictum/concerns/11.1-product-and-requirements.md. Sketch content below was elicited in the scaffold interview (2026-09-16/17). Next rung: Specified — complete prose per sub-aspect; then Contract-grade — mint PERSONA/SUCCESS/CAP register lines. -->

## Purpose & Scope

Owns the *why* and the capability spine of the tool. Dictum deliberately fixes only the **form** of its machine-readable extension points and blesses no tool. In practice each LLM that maintains a binding map picks its own in-practice layout, and handing a project from one model to another causes large setbacks. This tool exists to produce **one battle-tested style** for the binding map, deterministically, so that an LLM never edits the file by hand. If the style succeeds, others can adopt it or write converters between their style and this known-good one.

The tool's remit is **strictly `bindings.yaml`**. It never reads or writes the manifest, the concern docs, or the product code. Validation is **structural to the file alone**. Anything that needs the doc set or the code tree (doc-end resolution, coverage against the ID web, symbol resolution) stays with the Dictum advisory agents.

## Non-goals / Out-of-scope

Product-level non-goals (rules set in the interview, not derivable from the standard):

- **Single file by rule.** One invocation operates on exactly one `bindings.yaml`. The standard models one map per manifest and never describes a split map; the operator has hit a multi-file case in the wild and decided **not** to support it: the hassle of supporting it forever is not worth it, and converting several maps to one is "one LLM query away". `deferred` — re-entry: reassess only if a converter proves insufficient.
- **No doc-end or code-end validation.** Reading the manifest, the docs, or the code tree is out: those artifacts have no fixed style, so a deterministic tool cannot read them reliably. `absent` by design. The one exception is an **opt-in** path-existence check (Interfaces).
- **No execution.** The tool never runs an `asserted_by.run` selector or any other command. `absent`.
- **No line numbers, ever.** A line-numbered locator fails silently when code moves; the schema rejects `lines:` or any line reference and the tool never emits one. `absent` by rule.
- **No upward search, no auto-create.** The file is `./bindings.yaml` or the `--file` argument; a missing file requires `init` first. Reassessed in a later version if needed. `deferred`.
- **No multi-map discovery or merge view.** Follows from single-file. `deferred` with the same re-entry as above.

Scoped-out sub-aspects of this concern (manifest keys):

- `market-competitive-context` — `absent`: non-commercial tool; the "market" is the set of ad-hoc styles it intends to replace, which is the problem statement, not a market.
- `stakeholders-decision-makers` — `absent`: single-maintainer project; the operator is the only decision-maker.

Re-entry note for a scoped-out **concern**: Performance & Scalability is `deferred` at the operator's explicit call — Dictum doc sets can be very large, so no size or latency target is set; the tool goes into the wild and performance is fixed if issues arise. `[FUTURE-SCOPE]` re-entry: the first reported performance issue re-opens 11.13.

## Requirements

<!-- BUILD: Sketch outline. Specified = complete prose per bullet. -->

**Problem & motivation**
- Dictum's binding map (`templates/binding-map.template.md`) is a stored index that must self-validate every run, yet in 14 real maps surveyed at scaffold time the locator shapes, symbol notations, top-level keys, deferral forms, and prose conventions all diverged. Style divergence, not the standard, is what breaks hand-over between models.
- A deterministic tool that owns read, write, and validate removes the LLM from the file's syntax entirely.

**Target users**
- Primary: LLM agents invoking the tool from a shell (the Dictum skills and agents such as `drift-detector`, `implementation-planner`, `doc-feature`, `doc-excavate`). Machine-readable output is the primary contract.
- Secondary: a human maintainer at a terminal, occasionally.

**Goals & success criteria (candidates, measurable at Contract-grade)**
- A map written by the tool and read back by the tool is unchanged (idempotent round-trip, comments included).
- Every real-world map that conforms to the Dictum template validates clean; every non-conforming construct found in the survey is reported with a named finding.
- An LLM can perform every binding-map operation the standard describes without opening the file.

**Capability register (candidates; IDs minted at Contract-grade)**
- Initialise an empty map (required before any write).
- Validate a map structurally, on request and automatically before and after every write.
- Format a map to the canonical layout (the only operation that reorders).
- Query: get one binding by ID; list bindings, optionally by kind.
- Write: set (upsert) a whole binding; add a locator, a field locator, or an assertion; remove a binding, a locator, a field, or an assertion; set the coverage declaration.
- Comments: get and set comments at their defined anchors, exposed through the JSON interface.
- Opt-in path-existence check on locators.

**Constraints & assumptions**
- Python, minimum 3.11 (chosen so the operator's Debian 12 machine runs it on the system interpreter; a venv is used regardless).
- MIT licence; dependencies allowed as long as the MIT outcome holds. ruamel.yaml (MIT) for comment-preserving YAML.
- Distributed as a GitHub repository that users clone and install into a user-space bin. Binary name `lspd`. Not public at first commit; public at first release.
- Ships alongside Dictum v1.3.0 (pending on Dictum main at scaffold time). `[REVISIT]` the doc set is authored against v1.2.0; run the upgrade walk when v1.3.0 is vendored.
- Supported platforms: whatever Python 3.11+ supports; none targeted specifically.
- Schema: exactly the Dictum template's keys plus the two forms the standard names without shaping (`arm:` on an assertion, `owed:` for a deferred assertion). Anything else is an error.
- The operator is the author of the Dictum standard but this project acts as a third party: the schema stays owned here and is **not** contributed back into the Dictum template.

**Risks**
- Style lock-in: the canonical style may not fit a future Dictum release; mitigated by the single-file rule and the conversion path.
- Comment fidelity: comments outside the defined anchors must be relocated deterministically or rejected; a wrong choice loses information.
- Performance in the wild (see deferred re-entry above).

## Open Questions

- `[GAP]` Should the file carry a schema-version field? Asked at intake; not yet answered. Owned jointly with Domain & Data (`migrations-versioning`).
- `[GAP]` Name of the human-readable output flag.
- `[GAP]` Value vocabularies for `wire.casing`, `wire.enums`, `wire.dates`, and `compare_via`: open strings or a pinned set? The template only exemplifies values.
- `[GAP]` A binding on a kind the template excludes from the map (`CAP`, `POLICY`, `ROLE`, `LICENSE-TIER`, `PERF`): a warning, or silently allowed? Real maps carry `CAP` rows "for traceability".

## Dependencies & Cross-references
<!-- BUILD: rung Specified — link consumed IDs (none minted yet). -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified — an LLM agent closing a slice: set binding → add assertion → validate; a human formatting a hand-edited map. -->

## Design Decisions
<!-- BUILD: rung Specified — cross-cutting decisions go to Architecture's ADR register (single-file rule, structural-only validation, ruamel dependency, no line numbers, format-only reordering). -->

## Contracts
<!-- BUILD: rung Contract-grade — PERSONA-###, SUCCESS-###, CAP-### register lines (Part 5 register form). -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade — each SUCCESS-### maps to an observable check. -->

---
<!-- Status markers (subject, stay published): [GAP] [ASSUMPTION] [REVISIT] [FUTURE-SCOPE]. Build markers: these BUILD comments, stripped on publish. -->
