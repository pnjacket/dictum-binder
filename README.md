# dictum-binder

`lspd` — a deterministic command-line tool that reads, writes, and validates a
Dictum project's `bindings.yaml`, so the binding map has one canonical style and
a predictable token cost whichever LLM or human touches it.

Documented under the **Dictum** build-ready documentation standard (v1.2.0,
vendored at [`dictum/`](dictum/)). The doc set lives in [`docs/`](docs/) —
start at [`docs/README.md`](docs/README.md), the index derived from
`docs/manifest.yaml`.

dictum-binder is an independent tool for Dictum binding maps. It is not part of
the official Dictum project and is not endorsed or certified by it. It targets
Dictum v1.2.0 binding maps (the vendored, authored-against release).

Status: doc set published at Contract-grade (build-ready, 2026-09-18); slices 1–4 (Foundation, Query, Writes, Comments) built and verified at the merge gate on 2026-09-18; slices 5–6 pending.

## Licence and contributions

dictum-binder is licensed under the MIT licence (see `LICENSE`).
Contributions are accepted under the same MIT terms; no CLA and no sign-off
are required. Vendored Dictum material under `dictum/`: prose CC BY 4.0,
templates MIT — David H. Jung and the Dictum contributors.

## Schema

`lspd.schema.json` is the JSON Schema (draft 2020-12) of the canonical
`bindings.yaml` shape, generated from the tool's own rule table; the
executable embeds the same schema and never reads this file.

SHA-256 of `lspd.schema.json`: `22b8ff45e3c81bb242df1856f4b91b02e74804bd1e6af586f1bf0d7c13fa3379`
(confirm against `lspd schema --checksum`).

Rules the schema cannot express, enforced by `lspd validate`:

- contract IDs are semantic — no segment is all digits (`CAP-003` is rejected);
- a locator `role` needs a `wire` block on the binding (warning);
- an assertion is exactly bound (`path`, `symbol`, `run`) or exactly owed (`owed`);
- no `path` or `symbol` ends in `:` followed by digits, and no key is `lines` or `line`;
- no `(path, symbol)` pair repeats within a binding, and one shared across bindings is a warning;
- a kind is never both `fully_bound` and `curated`;
- comments attach only at anchors (header, binding, locator, field, assertion, coverage,
  curated entry) by line adjacency, one carrier per anchor, non-empty text;
- the file is UTF-8 without BOM, LF-terminated, and laid out canonically (`lspd format`).

See [`CLAUDE.md`](CLAUDE.md) for how the standard and its tooling are laid out
in this repo.
