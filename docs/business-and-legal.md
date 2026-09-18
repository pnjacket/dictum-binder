---
artifact: product-doc
role: concern
concern-id: business-and-legal
behavior: module
trigger: distributed (open source), plus an ip-trademark constraint (the Dictum naming policy)
in-scope-subaspects: [eula-tos, ip-trademark-constraints]
current-rung: contract-grade
status: published
version: 1.1.0
---

# Business & Legal — dictum-binder

> One-line: non-commercial and distributed — the MIT licence with David H. Jung as holder is the entire terms of use, and the one legal constraint is Dictum's naming policy, honoured as a third party with an explicit "not the official Dictum project" line in the README.

## Purpose & Scope

Owns the terms under which the tool is distributed and the trademark-style constraint that applies to its naming and positioning relative to Dictum. Everything commercial is out; the residual is two sub-aspects, each fully asserted below.

## Non-goals / Out-of-scope

- `commercial-licensing-model-tiers` — `absent`: non-commercial; no `LICENSE-TIER-*` exists.
- `tier-capability-entitlements-limits` — `absent`: no tiers; every `CAP-*` is available to everyone.
- `pricing` — `absent`: free.
- `business-slas` — `absent`: no service, no support commitment; the MIT text's warranty disclaimer is the whole statement.
- `contractual-agreements` — `absent`: none exist.
- `ip-copyright-provenance` — `absent`: no declared don't-derive-from constraint; the always-on first-party attestation is Governance's `source-provenance`, and a future declared constraint would mint a `LEGAL-*` here.

## Requirements

### EULA / ToS

- The **MIT licence text** in `LICENSE` at the repository root, with the line `Copyright (c) 2026 David H. Jung`, is the entire terms of use. No additional EULA, terms of service, privacy policy (no data is collected), or support terms exist.
- Contributions are accepted under the same MIT terms with no CLA or DCO (Governance `POLICY-CONTRIBUTIONS-MIT`); the README states this in one sentence.

### IP / trademark constraint

Dictum's naming policy (`TRADEMARK.md` in the Dictum repository; not a registered mark, a first-use courtesy) permits using the name to *refer* to the standard in tooling and asks that adaptations not present themselves as the official standard or imply endorsement or certification. This project:

- refers to Dictum by name in its project name (`dictum-binder`), description, and README, which the policy permits;
- implements nothing of the standard's *text* and republishes none of it beyond the vendored `dictum/` cache with its own licence files (Governance);
- carries an **explicit line in the README**: *"dictum-binder is an independent tool for Dictum binding maps. It is not part of the official Dictum project and is not endorsed or certified by it."* — the operator's choice over relying on the factual description alone;
- describes conformance factually and with a version — the manifest's `authored_against` tag, mechanically, so today *"targets Dictum v1.2.0 binding maps"* and v1.3.0 only once the upgrade walk lands — never as certification;
- acts as a **third party** although the operator authors the standard: the canonical schema stays owned here and is not contributed back into Dictum's template (Product constraint).

These facts are the checkable constraint `LEGAL-DICTUM-NAMING`.

## Open Questions

None open.

## Dependencies & Cross-references

- Governance enforces the licence posture (`POLICY-OUTBOUND-MIT`, `POLICY-CONTRIBUTIONS-MIT`) and mints the policy that enforces `LEGAL-DICTUM-NAMING`, `POLICY-NAMING-ENFORCEMENT`; Quality realises that policy as the README, `--help`, and `LICENSE` fitness test named in the acceptance criteria below; Product's constraints record the third-party stance.

## Examples / Worked scenarios

1. **README review before the first release.** The reviewer confirms the four sentences the constraint requires are present verbatim: the MIT statement, the contribution sentence, the independence line, and the versioned conformance phrase. The fitness test does the same on every CI run.
2. **A fork.** Someone forks the repository and renames the tool. Nothing here constrains them beyond MIT's attribution; the Dictum naming courtesy applies to their use of the Dictum name, not to this project.

## Design Decisions

| Decision | Rationale |
|---|---|
| Explicit independence line in the README | The operator preferred it over the implicit courtesy; it removes any ambiguity created by the author of the standard also authoring the tool |
| MIT text as the whole ToS | Nothing else is needed for a free, offline tool that collects nothing |
| Contract-grade by residual assertion | Every commercial sub-aspect is `absent` with its trait fact; the two in-scope facts are stated precisely and checked (Part 9 checklist) |

## Contracts

Register form: table row, ID in the first cell.

| ID | Constraint (checkable) |
|---|---|
| `LEGAL-DICTUM-NAMING` | (1) The README contains the sentence *"dictum-binder is an independent tool for Dictum binding maps. It is not part of the official Dictum project and is not endorsed or certified by it."*; (2) every conformance statement in the README and `--help` text uses the form "targets Dictum v<X.Y.Z> binding maps" and never the words "certified", "official", or "endorsed" in relation to Dictum except inside sentence (1); (3) no **product artifact** — `README.md`, `docs/`, `src/`, `tests/`, `tools/` — reproduces Dictum's normative text; `dictum/` (the vendored standard), `.claude/` (Dictum's own installed skills and agents), and `CLAUDE.md` (the installer's path-resolution note) are vendored Dictum material and exempt; (4) `LICENSE` is the MIT text with `Copyright (c) 2026 David H. Jung` |

The terms of use are the `LICENSE` file itself (EULA/ToS, prose-shaped; Contracts points to Requirements per Part 4). No `LICENSE-TIER-*` exists.

## Acceptance criteria

1. A fitness test asserts `LEGAL-DICTUM-NAMING` clauses (1), (2), and (4) textually over `README.md`, the `--help` output of `lspd`, and `LICENSE`.
2. Clause (3) is checked by the same test: no file under `README.md`, `docs/`, `src/`, `tests/`, or `tools/` contains a paragraph longer than two sentences that also appears in `dictum/STANDARD.md` or `dictum/concerns/*.md`; `dictum/`, `.claude/`, and `CLAUDE.md` are not scanned.
3. The manifest's `out_of_scope_subaspects` for this concern equals exactly the six keys listed in Non-goals, each with its `absent` justification (the Part 9 residual checklist, verified by the `doc-maturity-auditor`).

