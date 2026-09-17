---
artifact: product-doc
role: concern
concern-id: interfaces-and-contracts
behavior: core
trigger: always
in-scope-subaspects: [cli-surface, error-model-catalog, versioning-compatibility]
current-rung: sketch
status: draft
version: 0.1.0
---

# Interfaces & Contracts — dictum-binder

> One-line: the `lspd` command surface — every command, flag, JSON output document, error, and exit code — precise enough that an LLM agent can drive it without ever opening `bindings.yaml`.
<!-- BUILD: Read ../dictum/concerns/11.4-interfaces-and-contracts.md (CLI sub-type). Next rung: Specified — per-command description + rough I/O; Contract-grade — CLI-### per command with typed I/O as concrete JSON projections, OUT-### per emitted document, a total ERR-### catalog, pre/postconditions, owning COMPONENT and served CAP. This will be the largest doc in the set. -->

## Purpose & Scope

Owns the CLI surface (sub-type `cli-surface`), the error model, and the versioning of the machine-readable output. The primary caller is an LLM agent from a shell; JSON on stdout is the primary contract and the human-readable rendering is secondary.

## Non-goals / Out-of-scope

- `http-rpc-api-surface` — `absent`: no network API.
- `library-sdk-surface` — `absent`: not consumed as a library (see the Architecture open question; a change here re-enters as a `[FUTURE-SCOPE]` item).
- `event-surface` — `absent`: no events.
- `ui-entrypoints` — `absent`: no UI.
- `pagination-filtering-rate-limit-conventions` — `absent`: no API.

## Requirements

<!-- BUILD: Sketch outline — a list of commands by name. -->

**Binary and global behaviour**
- Binary name `lspd`.
- Target file: `./bindings.yaml` by default; `--file <path>` overrides. No upward search.
- Output: JSON on stdout by default; a human-readable flag (`[GAP]` name) switches rendering. Findings from pre- and post-write validation ride in the same envelope.
- Exit codes: `0` clean or warnings only; `1` one or more validation errors; `2` usage error or I/O failure (including "file not found, run init"). No strict flag promoting warnings in the first version.
- Opt-in flag to check that each locator `path` exists on disk relative to the working directory; off by default.

**Commands (candidates)**
- `init` — create an empty canonical map; refuses to overwrite.
- `validate` — structural validation; findings only.
- `format` — rewrite to canonical layout and order; the only reordering command.
- `get <ID>` — one binding as JSON, comments included.
- `list [--kind K]` — IDs (and summaries) in file order.
- `set <ID>` — upsert a whole binding from JSON input.
- `add-locator <ID>`, `add-field <ID> <name>`, `add-assertion <ID>` — append one entry.
- `remove <ID> [--locator … | --field … | --assertion …]` — remove a binding or one entry inside it.
- `coverage` — set `fully_bound` and `curated` entries.
- `comment get|set <anchor>` — read or write the comment at an anchor.

**Error model**
- Every failure, including argument parsing and YAML parse errors, maps to one structured error shape in the JSON envelope; a raw traceback reaching the caller is a contract violation.
- Validation findings are not errors of the command; they are payload, and only their severity drives the exit code.

**Versioning & compatibility**
- The JSON envelope is a public contract for LLM tooling; additive changes only within a major version. `[GAP]` whether the envelope carries an explicit version field (paired with the file schema-version question in Product).

## Open Questions

- `[GAP]` Human-readable flag name.
- `[GAP]` Envelope version field.
- `[GAP]` Input channel for `set` and `add-*`: JSON on stdin, a `--json` argument, or individual flags per field?
- `[GAP]` Anchor addressing syntax for `comment` (how an LLM names "the second locator of ENTITY-USER").

## Dependencies & Cross-references
<!-- BUILD: rung Specified — ENTITY/INV from Domain (I/O shapes project from them); COMPONENT from Architecture; CAP from Product. -->

## Examples / Worked scenarios
<!-- BUILD: rung Specified — full request/response for validate on a failing map, and for add-assertion. -->

## Design Decisions
<!-- BUILD: rung Specified → Contract-grade. -->

## Contracts
<!-- BUILD: rung Contract-grade — CLI-### per command; OUT-### per JSON document (envelope, finding, binding projection); ERR-### catalog (total, incl. parse/usage). -->

## Acceptance criteria
<!-- BUILD: rung Contract-grade — a contract test per CLI-###; envelope conformance for every ERR-###. -->

---
<!-- Status markers stay; BUILD comments strip on publish. -->
