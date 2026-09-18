---
artifact: product-doc
role: concern
concern-id: delivery-process
behavior: core
trigger: always
in-scope-subaspects: [vertical-slice-rule-slice-types, definition-of-done, build-playbook-sequence, work-item-hierarchy-slice-level, build-ready-gate-scope, verified-build-status-tracking, branching-release-versioning]
current-rung: contract-grade
status: draft
version: 1.1.0
---

# Delivery Process — dictum-binder

> One-line: six headless slices (the last verification-only) from `main`, a Definition of Done that is Quality's seven gates plus a build-status row, an empty substitution set, an LLM-written `bindings.yaml` (written without the tool, then conformed through `lspd`) right before the `v1.0.0` tag, and the in-repo record as the only tracker.

## Purpose & Scope

Owns how the tool gets built and proven: the slice rule and types, the Definition of Done at its two fidelity gates, the build playbook, the work-item level, the build-ready gate scope, Verified tracking, and release and versioning up to the first release. This concern *defines* Verified for every other concern.

## Non-goals / Out-of-scope

- `external-tracker-binding` — `absent`: no external tracker; the in-repo build-status record is the tracker. (GitHub Issues may carry inbound demand after the repository goes public; that would enter as a tracker-binding declaration through the enhancement lifecycle as ordinary demand — no re-entry note is owed for an `absent` subject.)
- **Branching inside the build is not governed by the doc set.** Until `v1.0.0` the work happens on `main`; how the implementer arranges local branches or commits between checkpoints is an implementation-level matter the operator deliberately leaves outside this document. `absent` by decision. Post-release branching re-enters when a second release is planned, `[FUTURE-SCOPE]`.
- No signed tags, no GitHub Release objects, no published wheel: the release is the tag alone; users clone and install. `absent` by decision.
- No release-infrastructure gate distinct from the merge gate beyond the checklist below: nothing is deployed. The substitution set is **empty and stated** in Operations' fidelity map (`ENV-LOCAL`, `ENV-CI`): no externals; nothing substituted; own code real at every gate. Operations is **in** on that map and the `TOOL-*` register only (pulled in 2026-09-17 after the second audit: a toolchain to pin is an environment fact per the spec; the earlier "both halves evaluated" rationale had missed that clause).
- No tool-maintained binding map during the build (see the playbook): relying on an unfinished tool for its own bookkeeping is a risk the operator declines. `deferred` — re-entry at the release slice, where the map is minted.

## Requirements

### Vertical-slice rule + slice types

- A slice is a vertical cut that ends in a **verified increment**: model, validator, emitter or loader change, command, renderer, tests at every tier the coverage map demands, and its build-status row. Never one layer alone.
- Every slice is **`slice:headless`**: there is no UI. The "no deferred E2E" rule applies at capability granularity: no `CAP-*` completes without its E2E journey through the installed binary (`E2E-STANDARD`).
- **Cross-cutting / foundation slices are first-class**: slice 1 lights up the shared pipeline every capability rides and is verified on its own before any capability slice lands.
- **Verification-only work is first-class**: the release slice's increment is largely proof (CI, checksum, provenance pass, dogfood conformance) over the built surface.
- A contract may span slices; each has exactly one **completing** slice, named in the playbook's *Completes* column and in the record.

### Definition of Done (fidelity-staged)

**Merge gate** (`ENV-LOCAL` or `ENV-CI`; nothing substituted; `ENV-CI` is the binding fidelity). A slice is done when all of the following hold on the commit that lands it:

1. Every contract the slice *completes* has the tests the coverage map assigns it (Quality), and every `CLI-*` it touches has its contract test and edge-input cases.
2. Quality's seven gates are green: `unittest` all tiers (which include the `SOURCE:` and naming fitness checks), 100 % line coverage with reasoned exclusions, ruff, pyrefly strict, schema-file equality, the licence gate, and (from the release slice on) dogfood `validate` and `format --check`.
3. **The build-status row is updated** — an explicit exit criterion, not a by-product: slice built, Verified at `merge`, proof named, *Completes* column filled.
4. Bindings the slice realises are **listed in the row's *Realises* column**; the map file itself is not written until the release slice (operator's decision, Non-goals). The row is the binding record until then. A proof that can only land with a later slice is recorded in the row as *proof owed by slice N* (build-status template), never left blank.
5. No doc changed except through the doc-led flow: a contract change during the build goes through `doc-feature` first, re-publishes the touched doc, and then the code catches up. Code never leads.
6. Any `SOURCE:` provenance marker owed by copied or adapted code is present (Governance).

**Release gate** (the `v1.0.0` tag): the merge gate is green on the tagged commit; a wheel is built from it and installed into a fresh venv; the E2E tier is green against that install; the README's checksum equals `lspd schema --checksum`; the source-provenance pass is recorded (Governance); the repository's own `bindings.yaml` validates clean and `format --check` exits 0; the version in `pyproject.toml` equals the tag. Nothing is deferred past this gate: with no infrastructure there is nothing that cannot run at merge, so the deferred-and-tracked list is empty and stated.

### Build playbook / sequence

Dependency-ordered; each slice names what it *realises* and what it *completes*. IDs realised early and completed later are marked "(partial)".

| # | Slice | Type | Realises | Completes | Proof |
|---|---|---|---|---|---|
| 1 | **Foundation** — package skeleton (version `1.0.0.dev0`), `LICENSE`, console script; `COMPONENT-MODEL`, `COMPONENT-SCHEMA` (`SCHEMA_VERSION`, rule table, generated `lspd.schema.json`), `COMPONENT-LOADER` (size cap, symlink resolution, **both comment carriers**, lazy ruamel import), `COMPONENT-EMITTER` (`emit` incl. both carriers and padding; `write` for the create case), `COMPONENT-VALIDATOR` (shape + rule passes, `--check-paths`), `COMPONENT-RENDERER`, `COMPONENT-CLI` with the catch-all, `errors.py`; `init`, `validate`, `schema`, `--help`, `--version`; golden canonical fixture; fitness tests incl. the `SEC-*` import checks, the `SOURCE:` marker check, the naming check; **CI workflow with all seven gates** (gate 6 skipped until `bindings.yaml` exists), `tools/licence_gate.py`, `tools/coverage_report.py`, README with the MIT and contribution sentences, the Dictum attribution, the independence line, the versioned conformance phrase, and the schema-checksum line (the naming and policy fitness checks read them from slice 1 on); `docs/IMPLEMENTATION.md` created | headless, cross-cutting | all eight `COMPONENT-*`; all `ENTITY-*`; all `INV-*` (read side; `INV-ORDER-PRESERVED`, `INV-CANONICAL-FIXPOINT` partial); all five `PATTERN-*` (`PATTERN-VALIDATE-AROUND-WRITE` via `init`, `PATTERN-ATOMIC-REPLACE` create case — partial); `CLI-INIT`, `CLI-VALIDATE`, `CLI-SCHEMA`, `CLI-HELP`, `CLI-VERSION`; `OUT-ENVELOPE`, `OUT-ERROR`, `OUT-FINDING`, `OUT-ANCHOR`, `OUT-VALIDATE-RESULT`, `OUT-SCHEMA`, `OUT-INIT-RESULT`; `ERR-USAGE`, `ERR-FILE-MISSING`, `ERR-FILE-EXISTS`, `ERR-FILE-TOO-LARGE`, `ERR-IO`, `ERR-PARSE`, `ERR-INTERNAL`, `ERR-SCHEMA-VERSION` (partial: raised by no slice-1 element); all eight `SEC-*` (the three write-path ones partial); `DEP-RUAMEL-YAML`; `ENV-LOCAL`, `ENV-CI`; all five `TOOL-*`; `POLICY-OUTBOUND-MIT`, `POLICY-INBOUND-MIT-ONLY`, `POLICY-CONTRIBUTIONS-MIT`, `POLICY-SOURCE-MARKER`, `POLICY-NAMING-ENFORCEMENT`; `LEGAL-DICTUM-NAMING`; `CAP-INIT`, `CAP-VALIDATE`, `CAP-SCHEMA`, `CAP-HELP`, `CAP-PATHCHECK`; `ADR-*` (all); `SUCCESS-SCHEMA-MATCH` (partial: README value) | `COMPONENT-MODEL`, `COMPONENT-SCHEMA`, `COMPONENT-LOADER`, `COMPONENT-VALIDATOR`, `COMPONENT-RENDERER`; all `ENTITY-*`; the fifteen write-gated `INV-*` (unit half, per Quality), `INV-ID-UNIQUE`, `INV-PATH-EXISTS`, `INV-ROLE-REQUIRES-WIRE`, `INV-OWNED-TWICE`; `PATTERN-ERROR-ENVELOPE`, `PATTERN-EXIT-CODES`, `PATTERN-OUTPUT-MODE`; the five `CLI-*`, seven `OUT-*`, and the seven `ERR-*` listed other than `ERR-SCHEMA-VERSION`; `SEC-ZERO-NETWORK`, `SEC-ZERO-EXEC`, `SEC-NO-AMBIENT-CONFIG`, `SEC-FAIL-CLOSED`, `SEC-NO-SECRETS`; `DEP-RUAMEL-YAML`; `ENV-LOCAL`, `ENV-CI`; `TOOL-SETUPTOOLS`, `TOOL-ACTIONS-CHECKOUT`, `TOOL-ACTIONS-SETUP-PYTHON`; `POLICY-OUTBOUND-MIT`, `POLICY-CONTRIBUTIONS-MIT`, `POLICY-SOURCE-MARKER`, `POLICY-NAMING-ENFORCEMENT`; `LEGAL-DICTUM-NAMING`; `CAP-INIT`, `CAP-VALIDATE`, `CAP-SCHEMA`, `CAP-HELP`, `CAP-PATHCHECK`; every `ADR-*` except `ADR-FORMAT-ONLY-REORDERS` (*proof owed by slice 5*) | E2E journeys for the five capabilities; unit per `INV-*`; golden round trip incl. all seven anchors; fitness suite incl. `SEC-*` forcings; seven CI steps green (gate 6 skipped) |
| 2 | **Query** — `get`, `list`, `--full` | headless | `CLI-GET`, `CLI-LIST`; `OUT-BINDING`, `OUT-LOCATOR`, `OUT-FIELD-LOCATOR`, `OUT-ASSERTION`, `OUT-BINDING-SUMMARY`; `ERR-SCHEMA-VERSION` (first reader; closes slice 1's partial); `ERR-NOT-FOUND` (partial → slice 3); `CAP-QUERY`; `SUCCESS-BOUNDED-OUTPUT` | all listed except `ERR-NOT-FOUND`; `ERR-SCHEMA-VERSION` completes here | E2E for `CAP-QUERY`; bounded-output contract test on the fifty-binding fixture |
| 3 | **Writes** — `set`, `add-locator`, `add-field`, `add-assertion`, `remove`, `coverage`; the Emitter's write path with atomic replace, symlink resolution, and mode-bit copy | headless | `CLI-SET`, `CLI-ADD-LOCATOR`, `CLI-ADD-FIELD`, `CLI-ADD-ASSERTION`, `CLI-REMOVE`, `CLI-COVERAGE-GET`, `CLI-COVERAGE-FULLY-BOUND`, `CLI-COVERAGE-CURATED`; `OUT-WRITE-RESULT`, `OUT-COVERAGE`; `PATTERN-VALIDATE-AROUND-WRITE`, `PATTERN-ATOMIC-REPLACE`; `INV-ORDER-PRESERVED`, `INV-ATOMIC-WRITE`; `ERR-NOT-FOUND`, `ERR-DUPLICATE`, `ERR-INPUT-INVALID`, `ERR-FILE-INVALID`; `SEC-FILE-FOOTPRINT`, `SEC-SYMLINK-FINAL-TARGET`, `SEC-TRUST-BOUNDARY`; `COMPONENT-COMMANDS` (partial); `CAP-SET`, `CAP-ADD`, `CAP-REMOVE`, `CAP-COVERAGE`; `SUCCESS-COMPLETE-OPS` (partial) | everything listed except `COMPONENT-COMMANDS` and `SUCCESS-COMPLETE-OPS` (`CLI-SET` completes here with its comment clause recorded as *proof owed by slice 4*; `ERR-FILE-INVALID`'s `format` forcing and `ERR-NOT-FOUND`'s `comment get` forcing likewise *owed by slice 5 / 4*; `INV-ORDER-PRESERVED`'s `comment` writes *owed by slice 4*) | E2E per capability; atomic-write injection test; order-preservation diffs; symlink-chain and mode-bit tests |
| 4 | **Comments** — `comment get/set/unset`, anchor parsing, comments in the `set` projection (`null` clears) — a two-carrier anchor stays an error-level finding fixed by hand, and a stray comment is `ERR-PARSE`, so neither has write semantics | headless | `CLI-COMMENT-GET`, `CLI-COMMENT-SET`, `CLI-COMMENT-UNSET`; `OUT-COMMENT`; `COMPONENT-EMITTER` (full: every write path exercised); `CAP-COMMENT`; `SUCCESS-ROUNDTRIP` (partial) | the three `CLI-*`, `OUT-COMMENT`, `COMPONENT-EMITTER`, `CAP-COMMENT` | E2E for `CAP-COMMENT`; seven-anchor edit fixtures; `set` with comments round-trips the `get` document (closes `CLI-SET`'s proof owed from slice 3) |
| 5 | **Format** — `format`, `format --check`; the last command wired into the CLI | headless | `CLI-FORMAT`; `OUT-FORMAT-RESULT`; `INV-CANONICAL-FIXPOINT`; `ADR-FORMAT-ONLY-REORDERS` (proof); `CAP-FORMAT`; `COMPONENT-COMMANDS`, `COMPONENT-CLI` (full: every element dispatched); `SUCCESS-ROUNDTRIP`, `SUCCESS-COMPLETE-OPS` | all listed (`ADR-FORMAT-ONLY-REORDERS` closes its owed proof from slice 1) | golden fixpoint over every fixture; E2E for `CAP-FORMAT`; `--help` enumeration equals the `CLI-*` set |
| 6 | **Release** — README install instructions and the rules JSON Schema cannot express (the licence, attribution, independence, and conformance sentences exist since slice 1); source-provenance pass recorded in `docs/IMPLEMENTATION.md`; the repository's own `bindings.yaml` written by an LLM in canonical style **without using `lspd`**, then conformed and verified through `lspd validate` and `lspd format --check` (gate 6 turns on); version `1.0.0` in `pyproject.toml`; fresh-venv wheel install + E2E; tag `v1.0.0` | verification-only | `SUCCESS-SCHEMA-MATCH` (final); `TOOL-RUFF`, `TOOL-PYREFLY` (confirmed at the tag); `POLICY-INBOUND-MIT-ONLY` (confirmed at the tag); `POLICY-PROVENANCE-PASS` | `SUCCESS-SCHEMA-MATCH`; `TOOL-RUFF`, `TOOL-PYREFLY`; `POLICY-INBOUND-MIT-ONLY`; `POLICY-PROVENANCE-PASS`; the release gate | release-gate checklist, recorded in `docs/IMPLEMENTATION.md` |

**Not completed by any slice, by design:** `SUCCESS-CROSS-MODEL` is an operator-recorded observation that begins after the release (Product); `PERSONA-*` are definitions with no realisation; `CAP-*` complete transitively through their `CLI-*` (the table lists them under the slice whose E2E proves them).

Slices land in this order; a later slice never starts before the earlier one's row reads Verified at `merge`. Every code-realisable ID minted in the doc set appears in exactly one *Completes* cell above (Delivery acceptance 3).

### Work-item hierarchy & slice level

- **Slice level** = the six playbook rows. Each is one row in `docs/IMPLEMENTATION.md`.
- Work inside a slice (a component, a fixture set, a test tier) is free-form and not tracked by the doc set; the row's *Proof* column is the only required evidence.
- **The in-repo record is the tracker**: no external system holds work items before the release.

### Build-ready gate scope

Every in-scope concern (the eleven in the manifest) at Contract-grade **and published**, before slice 1 begins; the scope to build is all twelve `CAP-*`. Nothing in scope is deferred past the gate; the only deferrals are the Part 9 scope-outs already recorded in each doc's Non-goals.

### Verified / build-status tracking

- `docs/IMPLEMENTATION.md`, from `dictum/templates/build-status.template.md`, created by slice 1 with all six rows unbuilt.
- Per row: Built · Verified (`merge` only, until the release slice re-runs the gate at the tag) · Proof · Realises · Completes.
- Flake incidents (Quality's policy) are appended to the record's notes with both run identifiers.
- The record is separate from the manifest: doc rungs never change because code landed, and rows never change because a doc was edited.
- **The first-party source-provenance register** (Governance's `POLICY-PROVENANCE-PASS`) is filled **in this record**, as a section of `docs/IMPLEMENTATION.md`, at the release slice — an implementation-time artefact must not edit a published doc. Governance owns the register's shape and residual clause; Delivery owns the filled rows.

### Branching / release / versioning

- All work on `main` until `v1.0.0`; commits at checkpoints; never pushed unless the operator says so.
- CI: GitHub Actions on every push, Python 3.11 on Ubuntu, running the seven gates (Quality).
- **First target: `1.0.0`**, so `schema_version` is `1` from the first release with no decoupling.
- The version is `1.0.0.dev0` in `pyproject.toml` from slice 1 (so the package major, and `schema_version`, are 1 throughout) and is **stamped `1.0.0` by the implementing LLM** as part of the release slice, never derived from the tag; the tag `v1.0.0` must equal it (release gate).
- The release is a **plain git tag**; no GitHub Release object, no published wheel. The repository goes public at that tag.
- Semantic versioning thereafter: a Dictum template change is a major (`ADR-MAJOR-PER-TEMPLATE`); anything additive within the surface is a minor.

## Open Questions

None open.

## Dependencies & Cross-references

- Consumes `E2E-STANDARD` and the seven gates (Quality); `CAP-*`, `SUCCESS-*` (Product); `COMPONENT-*`, `PATTERN-*`, `ADR-*` (Architecture); `CLI-*`, `OUT-*`, `ERR-*` (Interfaces); `ENTITY-*`, `INV-*` (Domain); the provenance register (Governance); the naming constraint (Business & Legal).
- Consumes Operations' fidelity map (`ENV-LOCAL`, `ENV-CI`; empty substitution set) and its `TOOL-*` register for the gate tooling.
- Referenced by the build-status record and by every slice's commit message (which names the slice number).

## Examples / Worked scenarios

1. **Slice 3 lands.** The implementer finishes `set`, `add-*`, `remove`, `coverage`; the coverage-map meta-test passes; CI is green; the row for slice 3 is set Built, Verified `merge`, proof "E2E `CAP-SET`/`CAP-ADD`/`CAP-REMOVE`/`CAP-COVERAGE` + atomic-write injection", *Realises* lists the IDs above (the record's own column header keeps the vendored template's spelling, *Realizes*; the two are the same column), *Completes* lists all but `COMPONENT-COMMANDS` and `SUCCESS-COMPLETE-OPS`. Commit at checkpoint.
2. **A contract turns out wrong mid-build.** Slice 4 reveals that a trailing comment on a flow line cannot be distinguished from a comment on the next line in one edge case. The implementer stops, runs `doc-feature` to amend `INV-COMMENT-ANCHORED` in Domain (classified `breaking` for the Loader), the doc re-publishes, and only then does the code change. The record's slice 4 row stays unbuilt until the amended contract is realised.
3. **Release slice.** An LLM writes `bindings.yaml` for this repository in canonical style without invoking `lspd`, mapping every `COMPONENT-*`, `CLI-*`, `ENTITY-*`, `INV-*` to `src/lspd/` symbols and tests. It then runs `lspd validate` and `lspd format --check`, fixes findings through `lspd`, and the release-gate checklist is ticked in the record. `pyproject.toml` says `1.0.0`; `git tag v1.0.0`.

## Design Decisions

| Decision | Rationale |
|---|---|
| Six slices, foundation first | The pipeline is shared by every capability; proving it alone before any capability keeps later slices small and attributable |
| Binding record lives in the build-status rows until the release slice | The operator will not depend on an unfinished tool for its own bookkeeping; the row carries the same information until an LLM writes the map |
| Release = plain tag; version stamped by the LLM in `pyproject.toml` | Minimal ceremony for a clone-and-install tool; a tag-derived version would add a build-time dependency for no gain |
| `1.0.0` first | Keeps `schema_version` equal to the major from the start, as Domain contracts |
| Branching inside the build ungoverned | Implementation-level; the doc set governs what lands and how it is proven, not the local workflow |

## Contracts

The owned contracts are process-shaped and fully stated in *Requirements* (Part 4): the **slice rule and types**, the **fidelity-staged Definition of Done**, the **build playbook**, the **work-item hierarchy declaration**, the **build-ready gate scope**, and the **build-status record** (`docs/IMPLEMENTATION.md`, created by slice 1). No `SLICE-###` ID web is invented; slices are process artifacts. No tracker-binding declaration exists (Non-goals).

## Acceptance criteria

1. `docs/IMPLEMENTATION.md` exists after slice 1 with exactly the six playbook rows and the release-gate checklist section.
2. Every row that reads Built has a named proof that exists in the test suite (a test function or a CI job name), checked by a fitness test reading the record.
3. The union of every row's *Completes* column equals the set of code-realisable IDs minted in the doc set — every `COMPONENT-*`, `PATTERN-*`, `INV-*`, `CLI-*`, `OUT-*`, `ERR-*`, `SEC-*`, `DEP-*`, `ENV-*`, `TOOL-*`, `POLICY-*`, `LEGAL-*`, `ENTITY-*`, `ADR-*`, and every `SUCCESS-*` except `SUCCESS-CROSS-MODEL` — each appearing exactly once (a fitness test derives both sets from the docs' register lines). `CAP-*` headlines appear under the slice whose E2E proves them and are excluded from the exactly-once check, as are `PERSONA-*`.
4. CI runs the seven gates on every push; the workflow file names each gate as a separate step.
5. At the tag `v1.0.0`: `pyproject.toml` version equals `1.0.0`; a fresh-venv wheel install passes the E2E tier; README checksum equals `lspd schema --checksum`; the repository's `bindings.yaml` validates clean and `format --check` exits 0.
6. From slice 1 on, a commit that touches `src/`, `tests/`, or `tools/` and also changes a **published concern doc** (`docs/*.md` other than `README.md` and `IMPLEMENTATION.md`) fails a fitness check run over the commit range since the previous CI run, unless the doc change is a version bump produced by the doc-led flow — code never leads the docs. `docs/IMPLEMENTATION.md` and `docs/README.md` are records, not published concern docs, and are exempt.

