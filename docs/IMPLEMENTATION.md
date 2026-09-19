# Build-status record — dictum-binder (`lspd`)

The Verified-rung / implementation-status record owned by Delivery Process (`verified-build-status-tracking`). Separate from the manifest: doc maturity ≠ implementation status. Current status only; history rides on git. Created by slice 1 on 2026-09-18 from `dictum/templates/build-status.template.md`; the *Completes* column is Delivery's extension (STANDARD Part 10e) and is pre-filled for all six rows from the playbook so the union check holds from day one.

Fidelity: `merge` = the seven Quality gates green in `ENV-LOCAL`/`ENV-CI` (nothing substituted; the substitution set is empty); `release` = the release gate at the `v1.0.0` tag.

## Slices

| # | Slice | Type | Realises | Completes (explicit; one completing slice per ID) | Built | Verified (stage) | Proof |
|---|---|---|---|---|:---:|---|---|
| 1 | Foundation — package, LICENSE, console script; Model, Schema (+ generated `lspd.schema.json`), Loader, Emitter, Validator, Renderer, CLI with the catch-all, `errors.py`; `init`, `validate`, `schema`, `--help`, `--version`; golden fixture; fitness suite; CI with the seven gates; `tools/licence_gate.py`, `tools/coverage_report.py`; README sentences; this record | headless, cross-cutting | all `COMPONENT-*`, `ENTITY-*`, `INV-*` (read side), `PATTERN-*`, the five slice-1 `CLI-*`, seven `OUT-*`, eight `ERR-*` (`ERR-SCHEMA-VERSION` partial), all `SEC-*` (write-path three partial), `DEP-RUAMEL-YAML`, `ENV-*`, all `TOOL-*`, five `POLICY-*`, `LEGAL-DICTUM-NAMING`, every `ADR-*`, `SUCCESS-SCHEMA-MATCH` (partial) | `CAP-INIT`, `CAP-VALIDATE`, `CAP-SCHEMA`, `CAP-HELP`, `CAP-PATHCHECK`, `COMPONENT-MODEL`, `COMPONENT-SCHEMA`, `COMPONENT-LOADER`, `COMPONENT-VALIDATOR`, `COMPONENT-RENDERER`, `ENTITY-MAP`, `ENTITY-CONTRACT-ID`, `ENTITY-BINDING`, `ENTITY-LOCATOR`, `ENTITY-FIELD-LOCATOR`, `ENTITY-WIRE`, `ENTITY-ASSERTION`, `ENTITY-PATH`, `ENTITY-COVERAGE`, `ENTITY-COMMENT`, `ENTITY-FINDING`, `INV-ID-GRAMMAR`, `INV-SCHEMA-VERSION`, `INV-CLOSED-KEYS`, `INV-NO-LINE-NUMBERS`, `INV-PATH-FORM`, `INV-SYMBOL-NONEMPTY`, `INV-ROLE-VALUES`, `INV-WIRE-SUBSET`, `INV-ASSERTION-SHAPE`, `INV-FIELD-NAME`, `INV-COVERAGE-WELLFORMED`, `INV-LOCATOR-UNIQUE`, `INV-ASSERTION-UNIQUE`, `INV-COMMENT-ANCHORED`, `INV-COMMENT-TEXT`, `INV-ID-UNIQUE`, `INV-PATH-EXISTS`, `INV-ROLE-REQUIRES-WIRE`, `INV-OWNED-TWICE`, `INV-BYTES`, `PATTERN-ERROR-ENVELOPE`, `PATTERN-EXIT-CODES`, `PATTERN-OUTPUT-MODE`, `CLI-INIT`, `CLI-VALIDATE`, `CLI-SCHEMA`, `CLI-HELP`, `CLI-VERSION`, `OUT-ENVELOPE`, `OUT-ERROR`, `OUT-FINDING`, `OUT-ANCHOR`, `OUT-VALIDATE-RESULT`, `OUT-SCHEMA`, `OUT-INIT-RESULT`, `ERR-USAGE`, `ERR-FILE-MISSING`, `ERR-FILE-EXISTS`, `ERR-FILE-TOO-LARGE`, `ERR-IO`, `ERR-PARSE`, `ERR-INTERNAL`, `SEC-ZERO-NETWORK`, `SEC-ZERO-EXEC`, `SEC-NO-AMBIENT-CONFIG`, `SEC-FAIL-CLOSED`, `SEC-NO-SECRETS`, `DEP-RUAMEL-YAML`, `ENV-LOCAL`, `ENV-CI`, `TOOL-SETUPTOOLS`, `TOOL-ACTIONS-CHECKOUT`, `TOOL-ACTIONS-SETUP-PYTHON`, `POLICY-OUTBOUND-MIT`, `POLICY-CONTRIBUTIONS-MIT`, `POLICY-SOURCE-MARKER`, `POLICY-NAMING-ENFORCEMENT`, `LEGAL-DICTUM-NAMING`, `ADR-SINGLE-FILE`, `ADR-STRUCTURAL-ONLY`, `ADR-NO-LINE-NUMBERS`, `ADR-LOAD-RUAMEL-EMIT-OWN`, `ADR-ARGPARSE`, `ADR-SCHEMA-SINGLE-SOURCE`, `ADR-OWN-SHAPE-VALIDATOR`, `ADR-INIT-REQUIRED`, `ADR-NO-SILENT-DEFAULTS`, `ADR-MAJOR-PER-TEMPLATE`, `ADR-NUMERIC-IDS-REJECTED`, `ADR-NO-LOGGING` | ✅ | merge | E2E `tests.e2e.test_journeys` (five journeys + invocation meta-test); unit per INV-* in `tests.unit.test_invariants`; golden `tests.golden.test_canonical`; contract `tests.contract.test_elements`, `tests.contract.test_errors_security`; fitness `tests.fitness.test_structure`, `tests.fitness.test_governance_ops`, `tests.fitness.test_delivery`; seven CI gates green (gate 6 skipped). Proofs owed: `ADR-FORMAT-ONLY-REORDERS` → slice 5; `ERR-USAGE` (--json/mismatch/partial-shape/selector conditions → slice 3, `lspd comment` group → slice 4); `PATTERN-EXIT-CODES` (format --check exception → slice 5); `PATTERN-ERROR-ENVELOPE` (unknown-ID source → slice 2, shape-breaking input → slice 3); `INV-PATH-EXISTS`/`CAP-PATHCHECK` (write-input half → slice 3) |
| 2 | Query — `get`, `list`, `--full` | headless | per the playbook row in `docs/delivery-process.md` | `CAP-QUERY`, `CLI-GET`, `CLI-LIST`, `OUT-BINDING`, `OUT-LOCATOR`, `OUT-FIELD-LOCATOR`, `OUT-ASSERTION`, `OUT-BINDING-SUMMARY`, `ERR-SCHEMA-VERSION`, `SUCCESS-BOUNDED-OUTPUT` | ☐ | — | — |
| 3 | Writes — `set`, `add-*`, `remove`, `coverage`; the Emitter write path | headless | per the playbook row in `docs/delivery-process.md` | `CAP-SET`, `CAP-ADD`, `CAP-REMOVE`, `CAP-COVERAGE`, `CLI-SET`, `CLI-ADD-LOCATOR`, `CLI-ADD-FIELD`, `CLI-ADD-ASSERTION`, `CLI-REMOVE`, `CLI-COVERAGE-GET`, `CLI-COVERAGE-FULLY-BOUND`, `CLI-COVERAGE-CURATED`, `OUT-WRITE-RESULT`, `OUT-COVERAGE`, `PATTERN-VALIDATE-AROUND-WRITE`, `PATTERN-ATOMIC-REPLACE`, `INV-ORDER-PRESERVED`, `INV-ATOMIC-WRITE`, `ERR-NOT-FOUND`, `ERR-DUPLICATE`, `ERR-INPUT-INVALID`, `ERR-FILE-INVALID`, `SEC-FILE-FOOTPRINT`, `SEC-SYMLINK-FINAL-TARGET`, `SEC-TRUST-BOUNDARY` | ☐ | — | — |
| 4 | Comments — `comment get/set/unset`, comments in the `set` projection | headless | per the playbook row in `docs/delivery-process.md` | `CAP-COMMENT`, `CLI-COMMENT-GET`, `CLI-COMMENT-SET`, `CLI-COMMENT-UNSET`, `OUT-COMMENT`, `COMPONENT-EMITTER` | ☐ | — | — |
| 5 | Format — `format`, `format --check` | headless | per the playbook row in `docs/delivery-process.md` | `CAP-FORMAT`, `CLI-FORMAT`, `OUT-FORMAT-RESULT`, `INV-CANONICAL-FIXPOINT`, `ADR-FORMAT-ONLY-REORDERS`, `COMPONENT-COMMANDS`, `COMPONENT-CLI`, `SUCCESS-ROUNDTRIP`, `SUCCESS-COMPLETE-OPS` | ☐ | — | — |
| 6 | Release — README install instructions, provenance pass, `bindings.yaml` written by an LLM and conformed with `lspd format`, version `1.0.0`, tag `v1.0.0` | headless (verification-only) | per the playbook row in `docs/delivery-process.md` | `SUCCESS-SCHEMA-MATCH`, `TOOL-RUFF`, `TOOL-PYREFLY`, `POLICY-INBOUND-MIT-ONLY`, `POLICY-PROVENANCE-PASS` | ☐ | — | — |

Not completed by any slice, by design: `SUCCESS-CROSS-MODEL` (operator-recorded after the release), `PERSONA-*` (definitions), `CAP-*` (headlines, listed under the slice whose E2E proves them).

## Gate status (summary)

- **Merge gate (`ENV-LOCAL`/`ENV-CI`):** slice 1 green on 2026-09-18 — unit, golden, contract, fitness, E2E tiers; 100 % line coverage of `src/lspd` via `tools/coverage_report.py`; ruff; pyrefly strict; schema file equals the embedded schema and the README checksum; licence gate MIT-only. Gate 6 skipped (no `bindings.yaml` until the release slice).
- **Release gate (`v1.0.0`):** not yet run.
- **Blocked-by-environment:** none — there is no infrastructure; nothing is deferred.

## Release-gate checklist

- [ ] merge gate green on the tagged commit
- [ ] wheel built with `pip wheel . --no-deps -w dist/` and installed into a fresh venv; E2E tier green against it
- [ ] README checksum equals `lspd schema --checksum`
- [ ] source-provenance pass recorded below (rows + non-empty residual)
- [ ] repository `bindings.yaml` written (by an LLM, without the tool), error-level findings fixed by hand, `lspd format` applied; `lspd validate` and `lspd format --check` exit 0
- [ ] `pyproject.toml` version `1.0.0` equals the tag

## Source-provenance register

Shape owned by Governance & Compliance (`POLICY-PROVENANCE-PASS`); rows filled by the release slice's pass.

| unit (path#symbol) | determination | origin | licence | outbound-compatible |
|---|---|---|---|---|
| *(filled at the release slice)* | | | | |

**Residual:** *(stated by the pass; never "none" without a reason).*

## Capability coverage

Built and verified at `merge`: `CAP-INIT`, `CAP-VALIDATE`, `CAP-PATHCHECK`, `CAP-SCHEMA`, `CAP-HELP` (slice 1). Not yet built: `CAP-QUERY` (slice 2), `CAP-SET`, `CAP-ADD`, `CAP-REMOVE`, `CAP-COVERAGE` (slice 3), `CAP-COMMENT` (slice 4), `CAP-FORMAT` (slice 5) — all inside the build-ready gate scope.

## Notes

- Flake incidents (Quality's policy): none.
