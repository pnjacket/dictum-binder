---
artifact: product-doc
role: concern
concern-id: delivery-process
behavior: core
trigger: always
in-scope-subaspects: [vertical-slice-rule-slice-types, definition-of-done, build-playbook-sequence, work-item-hierarchy-slice-level, build-ready-gate-scope, verified-build-status-tracking, branching-release-versioning]
current-rung: contract-grade
status: draft
version: 0.3.0
---

# Delivery Process — dictum-binder

> One-line: six headless slices from `main`, a Definition of Done that is Quality's six gates plus a build-status row, an empty substitution set, an LLM-written `bindings.yaml` (written without the tool, then conformed through `lspd`) right before the `v1.0.0` tag, and the in-repo record as the only tracker.
<!-- BUILD: Contract-grade as of 2026-09-17 (doc-levelup, interactive, one round). Owned contracts are process-shaped and fully stated in Requirements; Contracts points there (Part 4). The build-status record docs/IMPLEMENTATION.md is created with slice 1 from dictum/templates/build-status.template.md. -->

## Purpose & Scope

Owns how the tool gets built and proven: the slice rule and types, the Definition of Done at its two fidelity gates, the build playbook, the work-item level, the build-ready gate scope, Verified tracking, and release and versioning up to the first release. This concern *defines* Verified for every other concern.

## Non-goals / Out-of-scope

- `external-tracker-binding` — `absent`: no external tracker; the in-repo build-status record is the tracker. GitHub Issues may carry inbound demand after the repository goes public; that would enter as a tracker-binding declaration through the enhancement lifecycle, `[FUTURE-SCOPE]`.
- **Branching inside the build is not governed by the doc set.** Until `v1.0.0` the work happens on `main`; how the implementer arranges local branches or commits between checkpoints is an implementation-level matter the operator deliberately leaves outside this document. `absent` by decision. Post-release branching re-enters when a second release is planned, `[FUTURE-SCOPE]`.
- No signed tags, no GitHub Release objects, no published wheel: the release is the tag alone; users clone and install. `absent` by decision.
- No release-infrastructure gate distinct from the merge gate beyond the checklist below: there is no infrastructure (Operations absent). The substitution set is **empty and stated**: no externals; nothing substituted; own code real at every gate.
- No tool-maintained binding map during the build (see the playbook): relying on an unfinished tool for its own bookkeeping is a risk the operator declines. `deferred` — re-entry at the release slice, where the map is minted.

## Requirements

### Vertical-slice rule + slice types

- A slice is a vertical cut that ends in a **verified increment**: model, validator, emitter or loader change, command, renderer, tests at every tier the coverage map demands, and its build-status row. Never one layer alone.
- Every slice is **`slice:headless`**: there is no UI. The "no deferred E2E" rule applies at capability granularity: no `CAP-*` completes without its E2E journey through the installed binary (`E2E-STANDARD`).
- **Cross-cutting / foundation slices are first-class**: slice 1 lights up the shared pipeline every capability rides and is verified on its own before any capability slice lands.
- **Verification-only work is first-class**: the release slice's increment is largely proof (CI, checksum, provenance pass, dogfood conformance) over the built surface.
- A contract may span slices; each has exactly one **completing** slice, named in the playbook's *Completes* column and in the record.

### Definition of Done (fidelity-staged)

**Merge gate** (`ENV` = the developer machine or the CI runner; nothing substituted). A slice is done when all of the following hold on the commit that lands it:

1. Every contract the slice *completes* has the tests the coverage map assigns it (Quality), and every `CLI-*` it touches has its contract test and edge-input cases.
2. Quality's six gates are green: pytest all tiers, 100 % coverage with reasoned exclusions, ruff, mypy strict, schema-file equality, and (from the release slice on) dogfood `validate` and `format --check`.
3. **The build-status row is updated** — an explicit exit criterion, not a by-product: slice built, Verified at `merge`, proof named, *Completes* column filled.
4. Bindings the slice realises are **listed in the row's *Realizes* column**; the map file itself is not written until the release slice (operator's decision, Non-goals). The row is the binding record until then.
5. No doc changed except through the doc-led flow: a contract change during the build goes through `doc-feature` first, re-publishes the touched doc, and then the code catches up. Code never leads.
6. Any `SOURCE:` provenance marker owed by copied or adapted code is present (Governance).

**Release gate** (the `v1.0.0` tag): the merge gate is green on the tagged commit; a wheel is built from it and installed into a fresh venv; the E2E tier is green against that install; the README's checksum equals `lspd schema --checksum`; the source-provenance pass is recorded (Governance); the repository's own `bindings.yaml` validates clean and `format --check` exits 0; the version in `pyproject.toml` equals the tag. Nothing is deferred past this gate: with no infrastructure there is nothing that cannot run at merge, so the deferred-and-tracked list is empty and stated.

### Build playbook / sequence

Dependency-ordered; each slice names what it *realises* and what it *completes*. IDs realised early and completed later are marked "(partial)".

| # | Slice | Type | Realises | Completes | Proof |
|---|---|---|---|---|---|
| 1 | **Foundation** — package skeleton and console script; `COMPONENT-MODEL`, `COMPONENT-SCHEMA` with the generated `lspd.schema.json`, `COMPONENT-LOADER`, `COMPONENT-EMITTER`, `COMPONENT-VALIDATOR`, `COMPONENT-RENDERER`, `COMPONENT-CLI` with the catch-all; `init`, `validate`, `schema`, `--help`, `--version`; golden canonical fixture; fitness tests; `docs/IMPLEMENTATION.md` created | headless, cross-cutting | all eight `COMPONENT-*`; all `ENTITY-*`; every write-gated and advisory `INV-*` (partial: checked on read); `PATTERN-ERROR-ENVELOPE`, `PATTERN-EXIT-CODES`, `PATTERN-OUTPUT-MODE`; `CLI-INIT`, `CLI-VALIDATE`, `CLI-SCHEMA`, `CLI-HELP`, `CLI-VERSION`; `OUT-ENVELOPE`, `OUT-ERROR`, `OUT-FINDING`, `OUT-ANCHOR`, `OUT-VALIDATE-RESULT`, `OUT-SCHEMA`; `ERR-USAGE`, `ERR-FILE-MISSING`, `ERR-FILE-EXISTS`, `ERR-IO`, `ERR-PARSE`, `ERR-INTERNAL`; `CAP-INIT`, `CAP-VALIDATE`, `CAP-SCHEMA`, `CAP-HELP`; `ADR-*` (all) | `COMPONENT-MODEL`, `COMPONENT-SCHEMA`, `COMPONENT-LOADER`, `COMPONENT-VALIDATOR`, `COMPONENT-RENDERER`; all `ENTITY-*`; `INV-ID-GRAMMAR`, `INV-ID-UNIQUE`, `INV-SCHEMA-VERSION`, `INV-CLOSED-KEYS`, `INV-NO-LINE-NUMBERS`, `INV-PATH-FORM`, `INV-SYMBOL-NONEMPTY`, `INV-ROLE-VALUES`, `INV-WIRE-SUBSET`, `INV-ASSERTION-SHAPE`, `INV-FIELD-NAME`, `INV-COVERAGE-WELLFORMED`, `INV-LOCATOR-UNIQUE`, `INV-ASSERTION-UNIQUE`, `INV-BYTES`, `INV-ROLE-REQUIRES-WIRE`, `INV-OWNED-TWICE`; the three patterns and six errors listed; the five `CLI-*` and six `OUT-*` listed; `CAP-INIT`, `CAP-VALIDATE`, `CAP-SCHEMA`, `CAP-HELP`; every `ADR-*` | E2E journeys for the four capabilities; unit per `INV-*`; fitness suite |
| 2 | **Query** — `get`, `list`, `--full` | headless | `CLI-GET`, `CLI-LIST`; `OUT-BINDING`, `OUT-LOCATOR`, `OUT-FIELD-LOCATOR`, `OUT-ASSERTION`, `OUT-BINDING-SUMMARY`; `ERR-NOT-FOUND` (partial); `CAP-QUERY`; `SUCCESS-BOUNDED-OUTPUT` | all listed except `ERR-NOT-FOUND` | E2E for `CAP-QUERY`; bounded-output contract test on the fifty-binding fixture |
| 3 | **Writes** — `set`, `add-locator`, `add-field`, `add-assertion`, `remove`, `coverage` | headless | `CLI-SET`, `CLI-ADD-LOCATOR`, `CLI-ADD-FIELD`, `CLI-ADD-ASSERTION`, `CLI-REMOVE`, `CLI-COVERAGE-GET`, `CLI-COVERAGE-FULLY-BOUND`, `CLI-COVERAGE-CURATED`; `OUT-WRITE-RESULT`, `OUT-COVERAGE`; `PATTERN-VALIDATE-AROUND-WRITE`, `PATTERN-ATOMIC-REPLACE`; `INV-ORDER-PRESERVED`, `INV-ATOMIC-WRITE`; `ERR-NOT-FOUND`, `ERR-DUPLICATE`, `ERR-INPUT-INVALID`; `COMPONENT-COMMANDS` (partial); `CAP-SET`, `CAP-ADD`, `CAP-REMOVE`, `CAP-COVERAGE`; `SUCCESS-COMPLETE-OPS` (partial) | everything listed except `COMPONENT-COMMANDS` and `SUCCESS-COMPLETE-OPS` | E2E per capability; atomic-write injection test; order-preservation diffs |
| 4 | **Comments** — carriers in Loader and Emitter, `comment get/set/unset`, comments in the `set` projection | headless | `CLI-COMMENT-GET`, `CLI-COMMENT-SET`, `CLI-COMMENT-UNSET`; `OUT-COMMENT`; `INV-COMMENT-ANCHORED` (full); `CAP-COMMENT`; `SUCCESS-ROUNDTRIP` (partial) | the three `CLI-*`, `OUT-COMMENT`, `INV-COMMENT-ANCHORED`, `CAP-COMMENT` | E2E for `CAP-COMMENT`; seven-anchor round-trip fixtures |
| 5 | **Format and path check** — `format`, `format --check`, `--check-paths` | headless | `CLI-FORMAT`; `OUT-FORMAT-RESULT`; `INV-CANONICAL-FIXPOINT`; `CAP-FORMAT`, `CAP-PATHCHECK`; `COMPONENT-COMMANDS`; `SUCCESS-ROUNDTRIP`, `SUCCESS-COMPLETE-OPS` | all listed | golden fixpoint over every fixture; E2E for both capabilities |
| 6 | **Release** — CI workflow with the six gates; README with install instructions, the schema checksum, and the rules JSON Schema cannot express; source-provenance pass recorded; the repository's own `bindings.yaml` written by an LLM in canonical style **without using `lspd`**, then conformed and verified through `lspd validate` and `lspd format --check`; version `1.0.0` in `pyproject.toml`; tag `v1.0.0` | verification-only | `SUCCESS-SCHEMA-MATCH`; Governance's provenance register; Business & Legal's naming compliance in the README; `SUCCESS-CROSS-MODEL` (begins after release, operator-recorded) | `SUCCESS-SCHEMA-MATCH`; the release gate | release-gate checklist, recorded in `docs/IMPLEMENTATION.md` |

Slices land in this order; a later slice never starts before the earlier one's row reads Verified at `merge`.

### Work-item hierarchy & slice level

- **Slice level** = the six playbook rows. Each is one row in `docs/IMPLEMENTATION.md`.
- Work inside a slice (a component, a fixture set, a test tier) is free-form and not tracked by the doc set; the row's *Proof* column is the only required evidence.
- **The in-repo record is the tracker**: no external system holds work items before the release.

### Build-ready gate scope

Every in-scope concern (the ten in the manifest) at Contract-grade **and published**, before slice 1 begins; the scope to build is all twelve `CAP-*`. Nothing in scope is deferred past the gate; the only deferrals are the Part 9 scope-outs already recorded in each doc's Non-goals.

### Verified / build-status tracking

- `docs/IMPLEMENTATION.md`, from `dictum/templates/build-status.template.md`, created by slice 1 with all six rows unbuilt.
- Per row: Built · Verified (`merge` only, until the release slice re-runs the gate at the tag) · Proof · Realises · Completes.
- Flake incidents (Quality's policy) are appended to the record's notes with both run identifiers.
- The record is separate from the manifest: doc rungs never change because code landed, and rows never change because a doc was edited.

### Branching / release / versioning

- All work on `main` until `v1.0.0`; commits at checkpoints; never pushed unless the operator says so.
- CI: GitHub Actions on every push, Python 3.11 on Ubuntu, running the six gates (Quality).
- **First target: `1.0.0`**, so `schema_version` is `1` from the first release with no decoupling.
- The version is **stamped by the implementing LLM** once in `pyproject.toml` as part of the release slice, never derived from the tag; the tag `v1.0.0` must equal it (release gate).
- The release is a **plain git tag**; no GitHub Release object, no published wheel. The repository goes public at that tag.
- Semantic versioning thereafter: a Dictum template change is a major (`ADR-MAJOR-PER-TEMPLATE`); anything additive within the surface is a minor.

## Open Questions

None open.

## Dependencies & Cross-references

- Consumes `E2E-STANDARD` and the six gates (Quality); `CAP-*`, `SUCCESS-*` (Product); `COMPONENT-*`, `PATTERN-*`, `ADR-*` (Architecture); `CLI-*`, `OUT-*`, `ERR-*` (Interfaces); `ENTITY-*`, `INV-*` (Domain); the provenance register (Governance); the naming constraint (Business & Legal).
- No fidelity map is consumed: Operations is absent and the substitution set is empty.
- Referenced by the build-status record and by every slice's commit message (which names the slice number).

## Examples / Worked scenarios

1. **Slice 3 lands.** The implementer finishes `set`, `add-*`, `remove`, `coverage`; the coverage-map meta-test passes; CI is green; the row for slice 3 is set Built, Verified `merge`, proof "E2E `CAP-SET`/`CAP-ADD`/`CAP-REMOVE`/`CAP-COVERAGE` + atomic-write injection", *Realizes* lists the IDs above, *Completes* lists all but `COMPONENT-COMMANDS` and `SUCCESS-COMPLETE-OPS`. Commit at checkpoint.
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
3. The union of every row's *Completes* column equals the set of code-realisable IDs minted in the doc set, each appearing exactly once (a fitness test derives both sets).
4. CI runs the six gates on every push; the workflow file names each gate as a separate step.
5. At the tag `v1.0.0`: `pyproject.toml` version equals `1.0.0`; a fresh-venv wheel install passes the E2E tier; README checksum equals `lspd schema --checksum`; the repository's `bindings.yaml` validates clean and `format --check` exits 0.
6. A commit that touches `src/` and changes any published doc in the same commit fails a fitness check, unless the doc change is a version bump produced by the doc-led flow — code never leads the docs.

---
<!-- Status markers (subject, stay published): [GAP] [ASSUMPTION] [REVISIT] [FUTURE-SCOPE]. Build markers: these BUILD comments, stripped on publish. -->
