---
artifact: product-doc
role: concern
concern-id: security-and-privacy
behavior: baseline
trigger: always
in-scope-subaspects: [trust-boundaries, secrets-credential-handling, threat-model]
current-rung: sketch
status: draft
version: 0.1.0
---

# Security & Privacy — dictum-binder

> One-line: a minimal-risk local tool; this concern's job is to state the negative assertions as contracts — no network, no execution, no secrets, one file written.
<!-- BUILD: Read ../dictum/concerns/11.7-security-and-privacy.md. Baseline minimum: trust boundaries + secrets always; the threat model here is the "not a threat here" contractual negative assertion the spec asks for on minimal-risk products. -->

## Purpose & Scope

Owns the trust boundary, the (empty) secrets posture, and the threat model as a set of checkable negative assertions.

## Non-goals / Out-of-scope

- `authentication-mechanism` — `absent`: no users beyond the invoking local account.
- `authorization` — `absent`: no roles, no protected resources.
- `encryption` — `absent`: no sensitive data at rest or in transit; no transit.
- `session-management` — `absent`: no sessions.
- `data-protection-mechanisms-per-sensitive-field` — `absent`: no sensitive fields (Domain scoped classification tags out as absent).

## Requirements

<!-- BUILD: Sketch outline. -->

**Trust boundaries**
- One boundary: the process boundary between `lspd` and its caller (an LLM agent's shell or a human). Everything inside runs with the caller's privileges.
- Filesystem footprint: reads and writes exactly the target `bindings.yaml` (and its temporary sibling during atomic replace). With the opt-in path check, it additionally *stats* the locator paths relative to the working directory, never reads them.

**Secrets & credentials**
- None handled, stored, or required. A `run` selector is an opaque string; the tool never interprets or executes it.

**Threat model (negative assertions, to become contracts)**
- Zero network egress or ingress.
- Zero subprocess execution.
- No file outside the target is written; no file other than the target is read.
- Malformed input (YAML bombs, deeply nested documents, non-UTF-8 bytes) fails closed with a structured error and exit code 2.

## Open Questions

- `[GAP]` Whether to bound input size or nesting depth explicitly against pathological YAML, given performance is deferred but fail-closed is a security assertion.

## Dependencies & Cross-references
<!-- BUILD: rung Specified — Interfaces ERR-### for the fail-closed paths; Governance for the licence posture. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified. -->

## Design Decisions
<!-- BUILD: rung Specified → Contract-grade. -->

## Contracts
<!-- BUILD: rung Contract-grade — SEC-### negative assertions, each with a forcing test. -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
