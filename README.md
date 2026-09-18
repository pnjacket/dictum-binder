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
Dictum v1.3.0 binding maps.

Status: doc set at Contract-grade, in re-draft after audit fixes, not yet re-published; no product code yet.

Licence: MIT (`LICENSE` is created by the first build slice). Contributions are
accepted under the same MIT terms; no CLA or sign-off. Vendored Dictum
material: prose CC BY 4.0, templates MIT — David H. Jung and the Dictum
contributors.

See [`CLAUDE.md`](CLAUDE.md) for how the standard and its tooling are laid out
in this repo.
