# dictum-binder

dictum-binder is a deterministic command-line tool, installed as `dbind`, that reads, writes, and validates a
Dictum project's `bindings.yaml`, so the binding map has one canonical style and
a predictable token cost whichever LLM or human touches it.

Documented under the **Dictum** build-ready documentation standard (v1.2.0,
vendored at [`dictum/`](dictum/)). The doc set lives in [`docs/`](docs/) —
start at [`docs/README.md`](docs/README.md), the index derived from
`docs/manifest.yaml`.

dictum-binder is an independent tool for Dictum binding maps. It is not part of
the official Dictum project and is not endorsed or certified by it. It targets
Dictum v1.2.0 binding maps (the vendored, authored-against release).

Status: v1.0.0 (2026-09-18). The doc set is published at Contract-grade; all six
build slices are Built and Verified at the release gate (`docs/IMPLEMENTATION.md`).

## Install

Python 3.11 or newer. Clone the repository and install the package into a
virtual environment; the `dbind` executable lands in that environment's `bin/`.

```
git clone <this repository> dictum-binder
cd dictum-binder
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/dbind --help
```

The only runtime dependency is `ruamel.yaml` (MIT). There is no published
wheel and no GitHub Release object: the release is the plain tag `v1.0.0`.

For development, install the toolchain too and run the seven gates the CI
workflow runs (`.github/workflows/ci.yml`):

```
.venv/bin/pip install ".[dev]"
.venv/bin/python -m unittest discover -s tests -t .   # gate 1: five test tiers
.venv/bin/python tools/coverage_report.py             # gate 2: 100% line coverage (stdlib trace)
.venv/bin/ruff check . && .venv/bin/ruff format --check .   # gate 3
.venv/bin/pyrefly check                               # gate 4: strict types
.venv/bin/dbind schema | diff - dbind.schema.json       # gate 5: schema file and README checksum
.venv/bin/dbind validate && .venv/bin/dbind format --check    # gate 6: this repo's own bindings.yaml
.venv/bin/python tools/licence_gate.py                # gate 7: MIT-only dependencies
```

## Usage

Every command prints one JSON envelope on stdout (`--human` for a readable
form) and exits 0 (clean or warnings), 1 (something the caller can fix) or 2
(environment). `dbind --help` and `dbind <command> --help` list every argument,
exit code and error code.

```
dbind init                                   # the canonical empty map
dbind validate [--check-paths]               # structural findings, nothing written
dbind get ID [ID …]                          # bindings with their comments
dbind list [--kind K …] [--full]             # summaries in file order
dbind set ID --json DOC                      # create or replace a whole binding
dbind add-locator ID --path P [--symbol S] [--role producer|consumer] [--comment T]
dbind add-field ID NAME --path P [--symbol S] [--comment T]
dbind add-assertion ID (--path P --symbol S --run R | --owed REF) [--arm A] [--comment T]
dbind remove ID [--locator --path P [--symbol S] | --field NAME | --assertion …]
dbind coverage get | fully-bound add|remove KIND | curated set KIND --reason T | unset KIND
dbind comment get|set|unset <anchor> [--text T]
dbind format [--check]                       # canonical layout and order; the only reordering
dbind schema [--checksum]                    # the embedded JSON Schema
```

## Licence and contributions

dictum-binder is licensed under the MIT licence (see `LICENSE`).
Contributions are accepted under the same MIT terms; no CLA and no sign-off
are required. Vendored Dictum material under `dictum/`: prose CC BY 4.0,
templates MIT — David H. Jung and the Dictum contributors.

## Schema

`dbind.schema.json` is the JSON Schema (draft 2020-12) of the canonical
`bindings.yaml` shape, generated from the tool's own rule table; the
executable embeds the same schema and never reads this file.

SHA-256 of `dbind.schema.json`: `01becb83bc98002f68f5ec5c96d5a8347ccd653ac5708957fc4ce9d600ebf4f0`
(confirm against `dbind schema --checksum`).

Rules the schema cannot express, enforced by `dbind validate`:

- contract IDs are semantic — no segment is all digits (`CAP-003` is rejected);
- a locator `role` needs a `wire` block on the binding (warning);
- an assertion is exactly bound (`path`, `symbol`, `run`) or exactly owed (`owed`);
- no `path` or `symbol` ends in `:` followed by digits, and no key is `lines` or `line`;
- no `(path, symbol)` pair repeats within a binding, and one shared across bindings is a warning;
- a kind is never both `fully_bound` and `curated`;
- comments attach only at anchors (header, binding, locator, field, assertion, coverage,
  curated entry) by line adjacency, one carrier per anchor, non-empty text;
- the file is UTF-8 without BOM, LF-terminated, and laid out canonically (`dbind format`).

See [`CLAUDE.md`](CLAUDE.md) for how the standard and its tooling are laid out
in this repo.
