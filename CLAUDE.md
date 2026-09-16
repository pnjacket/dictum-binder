# CLAUDE.md — dictum-binder

## Documentation standard (Dictum)

This repo follows the **Dictum** build-ready documentation standard. The
standard material is **vendored** under [`dictum/`](dictum/) as a local cache
of the installed release:

| | |
|---|---|
| Installed release | **`v1.2.0`** (signed tag; tag object commit `48040ba`) |
| Canonical source | `https://github.com/pnjacket/dictum` |
| Vendored on | 2026-09-16, from `git archive v1.2.0` |
| Manifest `authored_against` | `v1.2.0` (stamp this when `doc-scaffold` writes the manifest) |

Vendored files:

- `dictum/STANDARD.md` — the method (Parts 0–13).
- `dictum/GLOSSARY.md` — vocabulary.
- `dictum/failure-mode-catalog.md` — each rule tied to the failure it prevents.
- `dictum/concerns/11.x-*.md` — the 15 concern specifications.
- `dictum/templates/` — fill-in skeletons (concern-doc, single-file, manifest,
  binding-map, build-status).
- `dictum/LICENSE`, `dictum/LICENSES/` — prose is CC BY 4.0, templates are MIT
  (attribution: David H. Jung and the Dictum contributors).

The advisory tooling is installed in `.claude/` (MIT):

- **Skills** (`.claude/skills/`): `doc-scaffold` (greenfield start),
  `doc-excavate` (brownfield code→doc), `doc-levelup`, `doc-feature`
  (doc-led forward flow), `doc-change-impact`, `report-failure-mode`.
- **Agents** (`.claude/agents/`): `doc-maturity-auditor`, `code-cartographer`,
  `drift-detector`, `implementation-planner`, `concern-specialist`.

**Path resolution:** when a skill or agent references `STANDARD.md`,
`concerns/11.x`, `templates/`, `GLOSSARY.md`, or `failure-mode-catalog.md` by
bare name, resolve them under `dictum/` in this repo. Never edit the vendored
copy; upgrades re-vendor a newer signed tag and run the upgrade walk.

**Product docs:** the manifest, binding map, build-status record, and the
concern docs are placed by `doc-scaffold` (not yet run). Until then this repo
has no doc set and no product code.

## Working conventions

- Reference contracts by stable ID (`CAP-###`, `ENTITY-###`, `API-###`, …);
  each contract is owned by exactly one concern doc.
- Subject markers (`[GAP] [ASSUMPTION] [REVISIT] [FUTURE-SCOPE]`) stay in
  published docs; build markers (`<!-- BUILD: ... -->`) strip on publish.
- Doc maturity (rung) is never conflated with implementation status; the
  latter lives in the build-status record.
- Commit at checkpoints; never push unless explicitly asked.
