---
artifact: product-doc
role: concern
concern-id: interfaces-and-contracts
behavior: core
trigger: always
in-scope-subaspects: [cli-surface, error-model-catalog, versioning-compatibility]
current-rung: contract-grade
status: published
version: 1.0.0
---

# Interfaces & Contracts — dictum-binder

> One-line: the `lspd` command surface — nineteen elements, their typed inputs with empty-value semantics, one JSON envelope with fixed projections, a total error catalog, and a compatibility promise — precise enough that an LLM agent drives it without ever opening `bindings.yaml`.

## Purpose & Scope

Owns the CLI surface (`cli-surface`), the error model (`error-model-catalog`), and the versioning of the machine-readable output (`versioning-compatibility`). The primary caller is `PERSONA-AGENT` from a shell; JSON on stdout is the primary contract and the `--human` rendering is secondary. Every element is owned by `COMPONENT-CLI`, served by `COMPONENT-COMMANDS`, and rendered by `COMPONENT-RENDERER`.

## Non-goals / Out-of-scope

- `http-rpc-api-surface` — `absent`: no network API.
- `library-sdk-surface` — `absent`: not consumed as a library; the package's modules are not a public API (Architecture).
- `event-surface` — `absent`: no events.
- `ui-entrypoints` — `absent`: no UI.
- `pagination-filtering-rate-limit-conventions` — `absent`: no API; `list` returns the full matching set in one document.
- No shell completion, colour, or interactive prompts. `absent` by decision (`ADR-ARGPARSE`).
- No stability promise for `--human` output beyond carrying the same codes and messages as the JSON envelope. `absent` by decision.
- No environment variables or configuration files influence behaviour; every input is an argument. `absent` by decision (no silent defaults).

## Requirements

### Global conventions

- **Binary** `lspd`. Invocation: `lspd [global options] <command> [subcommand] [arguments]`.
- **Global options**, valid before any command: `--file PATH` (target map; default `./bindings.yaml`; no upward search; symlinks resolved to the final target, `SEC-SYMLINK-FINAL-TARGET`); `--human` (readable rendering); `--check-paths` (enables `CAP-PATHCHECK` wherever validation runs); `--no-size-limit` (lifts the 10 MiB target-size cap, `SEC-FAIL-CLOSED`); `--debug` (traceback on stderr in addition to the envelope); `--help`; `--version` (plain text `lspd <semver>`).
- **Output**: exactly one document on stdout per invocation. JSON envelope (`OUT-ENVELOPE`) by default; `--human` rendering otherwise. Exceptions: `--help` and `--version` print plain text; `schema` prints the raw schema document or the raw checksum line. stderr carries only `--debug` tracebacks.
- **Exit codes** per `PATTERN-EXIT-CODES`: `0` clean or warnings only · `1` caller-fixable · `2` environment · `130` interrupted.
- **Empty values.** An empty-string argument anywhere is `ERR-USAGE`. There is no "unset" meaning for an empty value; unsetting is always an explicit command. An omitted optional argument means "not present", never a default value.
- **`--help`** at every level (`lspd --help`, `lspd <command> --help`, `lspd <command> <subcommand> --help`) lists every argument with its optionality and one-line meaning, the command's exit codes, and its error codes. `--help` on an unknown command is `ERR-USAGE`.
- **Pre/post findings.** Every write command reports `findings.pre` (loaded file) and `findings.post` (written file); read-only commands report `findings.pre` and an empty `findings.post`. Validation findings carry `INV-*` codes (Domain) and are not errors; only their severity moves the exit code.
- **Input for writes.** Per-field flags for single entries; a JSON document for a whole binding (`set`), via `--json '<doc>'` or `--json -` to read stdin. Every `set`/`add-*` input is checked with `validate_input` before mutation (`PATTERN-VALIDATE-AROUND-WRITE`); a shape error is `ERR-INPUT-INVALID` with nothing written.
- **Addressing entries.** A locator is addressed by `--path P` and, when it has one, `--symbol S`. An assertion by `--path P --symbol S` (bound) or `--owed REF` (owed), plus `--arm A` when it has one. A field by its name. Exact match on the identity (`ENTITY-LOCATOR`, `ENTITY-ASSERTION`); no match is `ERR-NOT-FOUND`.
- **Anchors** for `comment` commands are a positional anchor kind followed by its identity: `header` · `binding ID` · `locator ID --path P [--symbol S]` · `field ID NAME` · `assertion ID (--path P --symbol S | --owed REF) [--arm A]` · `coverage` · `curated KIND`.

### CLI surface

Nineteen elements, minted in Contracts: `CLI-INIT`, `CLI-VALIDATE`, `CLI-FORMAT`, `CLI-GET`, `CLI-LIST`, `CLI-SET`, `CLI-ADD-LOCATOR`, `CLI-ADD-FIELD`, `CLI-ADD-ASSERTION`, `CLI-REMOVE`, `CLI-COVERAGE-GET`, `CLI-COVERAGE-FULLY-BOUND`, `CLI-COVERAGE-CURATED`, `CLI-COMMENT-GET`, `CLI-COMMENT-SET`, `CLI-COMMENT-UNSET`, `CLI-SCHEMA`, `CLI-HELP`, `CLI-VERSION`.

### Error model / catalog

Total and content-negotiated in the CLI sense (`PATTERN-ERROR-ENVELOPE`): every failure from every source, including argparse's own usage errors, file I/O, ruamel parse errors, and unexpected exceptions, is one of the ten `ERR-*` codes in Contracts, rendered in the envelope (JSON) or the human form. A raw traceback or argparse's default stderr text reaching the caller is a contract violation.

### Versioning & compatibility

- `lspd` follows semantic versioning. The tool version appears in every envelope (`lspd.version`) and in `--version`.
- **Within a major version**: no command, subcommand, argument, envelope field, projection field, error code, or finding code is removed or renamed; additions are allowed and are the only kind of change. A new required argument is a breaking change and therefore a major.
- **A Dictum template change is a major** (`ADR-MAJOR-PER-TEMPLATE`); `schema_version` in the file and `lspd.schema_version` in the envelope both track it.
- The raw output of `schema` is exactly the shipped `lspd.schema.json` (`SUCCESS-SCHEMA-MATCH`).

## Open Questions

None open.

## Dependencies & Cross-references

- Serves `CAP-INIT` … `CAP-HELP` (Product), one or more elements per capability; realises `SUCCESS-BOUNDED-OUTPUT`, `SUCCESS-COMPLETE-OPS`, `SUCCESS-SCHEMA-MATCH`.
- Projects `ENTITY-BINDING`, `ENTITY-LOCATOR`, `ENTITY-FIELD-LOCATOR`, `ENTITY-WIRE`, `ENTITY-ASSERTION`, `ENTITY-COVERAGE`, `ENTITY-COMMENT`, `ENTITY-FINDING` (Domain) onto the wire; validators honour `INV-ID-GRAMMAR` and `INV-PATH-FORM` on arguments.
- Owned by `COMPONENT-CLI`, served by `COMPONENT-COMMANDS`, rendered by `COMPONENT-RENDERER`; follows `PATTERN-ERROR-ENVELOPE`, `PATTERN-VALIDATE-AROUND-WRITE`, `PATTERN-EXIT-CODES`, `PATTERN-OUTPUT-MODE` (Architecture).
- Referenced by Quality (a contract test per `CLI-*`, a forced test per `ERR-*`), Delivery (slices realise elements), Security (the `ERR-*` fail-closed paths).

## Examples / Worked scenarios

1. **`get` with two IDs.**
   `lspd get ENTITY-USER INV-USER-EMAIL-UNIQUE` →
   ```json
   {"lspd":{"version":"1.0.0","schema_version":1},"ok":true,"command":"get",
    "result":{"bindings":[{"id":"ENTITY-USER","kind":"ENTITY","comment":null,
      "locators":[{"path":"src/models/user.py","symbol":"User","role":null,"comment":"ORM model"}],
      "compare_via":null,"fields":{"email":{"path":"src/models/user.py","symbol":"User.email","comment":null}},
      "wire":null,"asserted_by":null},
     {"id":"INV-USER-EMAIL-UNIQUE","kind":"INV","comment":null,"locators":[],"compare_via":null,"fields":null,"wire":null,
      "asserted_by":[{"path":"tests/test_user.py","symbol":"test_email_unique","run":"python3 -m pytest tests/test_user.py::test_email_unique","arm":null,"owed":null,"comment":null}]}]},
    "findings":{"pre":[],"post":[]},"error":null}
   ```
   Exit 0. Nothing else from the file is in the document.
2. **Rejected `add-locator`.** `lspd add-locator ENTITY-X --path "src/x.py:41" --symbol f` → `ok:false`, `error.code:"ERR-INPUT-INVALID"`, `error.details.findings:[{"code":"INV-NO-LINE-NUMBERS", …}]`, exit 1, file unchanged.
3. **Missing file.** `lspd validate` in a directory with no map → `error.code:"ERR-FILE-MISSING"`, `error.message` names the path and says to run `init`, exit 2.
4. **`format --check` in CI.** A canonical file → `result:{"changed":false}`, exit 0. A non-canonical file → `result:{"changed":true}`, exit 1, file untouched.
5. **Comment round trip.** `lspd comment set locator ENTITY-USER --path src/models/user.py --symbol User --text "ORM model"`; then `lspd comment get locator ENTITY-USER --path src/models/user.py --symbol User` → `result:{"anchor":{…},"text":"ORM model"}`.
6. **Raw schema.** `lspd schema > lspd.schema.json` writes the exact shipped file; `lspd schema --checksum` prints one line, the 64-hex SHA-256.

## Design Decisions

| Decision | Rationale |
|---|---|
| Fixed projection shape: every optional key present, `null` when absent | Predictable tokens and no key-presence branching for the agent; a small size cost the operator accepts |
| Flags for single entries, JSON only for a whole binding | A locator is three fields; a binding is a document. Each channel matches its payload |
| `get` and `list` accept several targets | Fewer round trips at no loss of boundedness: output is still exactly the requested set |
| `set` accepts the `get` projection, comments included | `get` → edit → `set` is the natural whole-binding edit; forcing comments through a second call would split one intent |
| `schema` prints raw, everything else prints the envelope | The schema is a file for a converter author, not a result for an agent; wrapping it would make the shipped artifact and the printed one differ |
| Empty string is always a usage error | The no-silent-defaults rule applied to arguments |
| `list` summaries by default, `--full` on request | Summaries are the bounded default; the full set is an explicit choice |

## Contracts

Register form: table row, ID in the first cell.

### Output documents (`OUT-*`)

| ID | Shape |
|---|---|
| `OUT-ENVELOPE` | The one JSON object every non-raw command prints. Keys, all always present: `lspd: {version: str (semver), schema_version: int}` · `ok: bool` · `command: str` (the element's command path, e.g. `"comment set"`) · `result: object \| null` (per element below; `null` on error) · `findings: {pre: [OUT-FINDING], post: [OUT-FINDING]}` · `error: OUT-ERROR \| null`. Serialised with `ensure_ascii=false`, keys in the order listed, no trailing whitespace, one trailing newline; not pretty-printed by default (`--human` is the readable form) |
| `OUT-ERROR` | `{code: ERR-* id, message: str, details: object}`. `details` keys per code: `ERR-NOT-FOUND` → `{id, anchor: OUT-ANCHOR \| null}` · `ERR-DUPLICATE` → `{id, anchor: OUT-ANCHOR}` · `ERR-INPUT-INVALID` → `{findings: [OUT-FINDING]}` · `ERR-FILE-MISSING`/`ERR-FILE-EXISTS`/`ERR-FILE-TOO-LARGE`/`ERR-IO`/`ERR-PARSE` → `{path: str, reason: str}` · `ERR-USAGE` → `{usage: str}` · `ERR-INTERNAL` → `{exception: str}` |
| `OUT-FINDING` | Projection of `ENTITY-FINDING`: `{code: INV-* id, severity: "error" \| "warning", anchor: OUT-ANCHOR, message: str}` |
| `OUT-ANCHOR` | Fixed-key object: `{type: "file" \| "header" \| "binding" \| "locator" \| "field" \| "assertion" \| "coverage" \| "curated", id: str \| null, path: str \| null, symbol: str \| null, arm: str \| null, owed: str \| null, field: str \| null, kind: str \| null}`; only the keys meaningful for `type` are non-null |
| `OUT-BINDING` | Projection of `ENTITY-BINDING` with its anchored comments: `{id, kind, comment: str \| null, locators: [OUT-LOCATOR], compare_via: str \| null, fields: {name: OUT-FIELD-LOCATOR} \| null, wire: {casing: str \| null, enums: str \| null, dates: str \| null} \| null, asserted_by: [OUT-ASSERTION] \| null}`. `locators` is `[]` for a stub. Used as the **input** projection of `CLI-SET` too: `id` and `kind` may be omitted; if present they must equal the positional ID and its derived kind (`ERR-INPUT-INVALID` otherwise) |
| `OUT-LOCATOR` | `{path: str, symbol: str \| null, role: "producer" \| "consumer" \| null, comment: str \| null}` |
| `OUT-FIELD-LOCATOR` | `{path: str, symbol: str \| null, comment: str \| null}` |
| `OUT-ASSERTION` | `{path: str \| null, symbol: str \| null, run: str \| null, arm: str \| null, owed: str \| null, comment: str \| null}`; exactly the bound or the owed subset is non-null per `INV-ASSERTION-SHAPE` |
| `OUT-BINDING-SUMMARY` | `{id, kind, stub: bool, locators: int, fields: int, assertions: int, has_comment: bool}` |
| `OUT-COVERAGE` | `{comment: str \| null, fully_bound: [str], curated: {KIND: {reason: str, comment: str \| null}}}`; empty list / empty object when absent in the file |
| `OUT-COMMENT` | `{anchor: OUT-ANCHOR, text: str}` |
| `OUT-VALIDATE-RESULT` | `{errors: int, warnings: int, paths_checked: bool}` — the findings themselves are in `findings.pre` |
| `OUT-FORMAT-RESULT` | `{changed: bool, checked_only: bool}` |
| `OUT-WRITE-RESULT` | For every mutating element except `format` and `init`: `{binding: OUT-BINDING}` after the write (`remove` of a whole binding returns `{binding: null, removed: str}`); coverage elements return `{coverage: OUT-COVERAGE}`; comment elements return `OUT-COMMENT` (or `{anchor, text: null}` after unset) |
| `OUT-SCHEMA` | Raw: the JSON Schema document (draft 2020-12) of `ENTITY-MAP`, serialised with sorted keys, two-space indent, `ensure_ascii=false`, one trailing newline — byte-identical to the shipped `lspd.schema.json`. With `--checksum`: one line, lowercase 64-hex SHA-256 of those bytes, newline |

### CLI elements (`CLI-*`)

Every element: owning component `COMPONENT-CLI`; served by `COMPONENT-COMMANDS`; global options apply. "Reads" = runs Loader + pre-validation; "writes" = the full pipeline with `PATTERN-VALIDATE-AROUND-WRITE` and `PATTERN-ATOMIC-REPLACE`. Common errors on every reading element: `ERR-FILE-MISSING`, `ERR-FILE-TOO-LARGE`, `ERR-IO`, `ERR-PARSE`; on every element: `ERR-USAGE`, `ERR-INTERNAL`. Rows list only the element-specific errors.

| ID | Signature | Inputs (required · optional) | Output (`result`) | Element-specific errors | Pre / post · side effects | Serves |
|---|---|---|---|---|---|---|
| `CLI-INIT` | `lspd init` | none | `{path: str}` | `ERR-FILE-EXISTS` (target exists, any content); `ERR-IO` (unwritable) | Pre: target absent. Post: target is the canonical empty map (`schema_version: <major>`, `bindings: {}`), `findings.post` empty. Writes | `CAP-INIT` |
| `CLI-VALIDATE` | `lspd validate` | none | `OUT-VALIDATE-RESULT` | — | Reads. Exit 1 iff any error finding. `--check-paths` adds `CAP-PATHCHECK` findings under `INV-PATH-FORM` with severity error. No side effects | `CAP-VALIDATE`, `CAP-PATHCHECK` |
| `CLI-FORMAT` | `lspd format [--check]` | · `--check` (flag) | `OUT-FORMAT-RESULT` | — | Reads; writes unless `--check`. Post: file is the canonical layout (`INV-CANONICAL-FIXPOINT`); with `--check` nothing is written and exit 1 iff it would change. Pre-error findings are reported and formatting still proceeds on the loadable model | `CAP-FORMAT` |
| `CLI-GET` | `lspd get ID [ID …]` | one or more IDs (each must satisfy `INV-ID-GRAMMAR`, else `ERR-USAGE`) | `{bindings: [OUT-BINDING]}` in argument order | `ERR-NOT-FOUND` (first unknown ID; nothing returned) | Reads. Output contains exactly the requested bindings (`SUCCESS-BOUNDED-OUTPUT`). No side effects | `CAP-QUERY` |
| `CLI-LIST` | `lspd list [--kind KIND …] [--full]` | · `--kind` repeatable (each `[A-Z][A-Z0-9]+`); `--full` (flag) | `{bindings: [OUT-BINDING-SUMMARY]}` or, with `--full`, `[OUT-BINDING]`; file order; empty list allowed | — | Reads. No kinds = all bindings. An unknown kind matches nothing (empty result, exit 0) | `CAP-QUERY` |
| `CLI-SET` | `lspd set ID --json DOC` | ID; `--json` (a document per `OUT-BINDING`, or `-` for stdin) | `OUT-WRITE-RESULT` | `ERR-INPUT-INVALID` (shape, `id`/`kind` mismatch, invalid JSON) | Reads; writes. Unknown ID → created, appended last; known ID → replaced in place. Comments in the document are set at their anchors; absent comments (`null`) clear. Warnings in the input are written and reported in `findings.post` | `CAP-SET`, `CAP-COMMENT` |
| `CLI-ADD-LOCATOR` | `lspd add-locator ID --path P [--symbol S] [--role producer\|consumer] [--comment TEXT]` | ID, `--path` · `--symbol`, `--role`, `--comment` | `OUT-WRITE-RESULT` | `ERR-NOT-FOUND` (ID); `ERR-DUPLICATE` (same path+symbol present); `ERR-INPUT-INVALID` | Reads; writes. Appends last; order untouched (`INV-ORDER-PRESERVED`) | `CAP-ADD` |
| `CLI-ADD-FIELD` | `lspd add-field ID NAME --path P [--symbol S] [--comment TEXT]` | ID, NAME, `--path` · `--symbol`, `--comment` | `OUT-WRITE-RESULT` | `ERR-NOT-FOUND` (ID); `ERR-INPUT-INVALID` | Reads; writes. Existing NAME is replaced in place; new NAME appended last | `CAP-ADD` |
| `CLI-ADD-ASSERTION` | `lspd add-assertion ID (--path P --symbol S --run R \| --owed REF) [--arm A] [--comment TEXT]` | ID and exactly one shape · `--arm`, `--comment` | `OUT-WRITE-RESULT` | `ERR-NOT-FOUND` (ID); `ERR-DUPLICATE` (same identity present); `ERR-INPUT-INVALID` (mixed shape → `INV-ASSERTION-SHAPE`) | Reads; writes. Appends last | `CAP-ADD` |
| `CLI-REMOVE` | `lspd remove ID [--locator --path P [--symbol S] \| --field NAME \| --assertion (--path P --symbol S \| --owed REF) [--arm A]]` | ID · exactly one entry selector, or none for the whole binding | `OUT-WRITE-RESULT` | `ERR-NOT-FOUND` (ID or entry) | Reads; writes. Whole binding removed with its comments; removing the last locator leaves the stub; removing the last field or assertion removes that key | `CAP-REMOVE` |
| `CLI-COVERAGE-GET` | `lspd coverage get` | none | `{coverage: OUT-COVERAGE}` | — | Reads. No side effects | `CAP-COVERAGE` |
| `CLI-COVERAGE-FULLY-BOUND` | `lspd coverage fully-bound (add \| remove) KIND` | subcommand, KIND (`[A-Z][A-Z0-9]+`) | `OUT-WRITE-RESULT` (coverage) | `ERR-DUPLICATE` (add: already listed); `ERR-NOT-FOUND` (remove: not listed); `ERR-INPUT-INVALID` (add: kind is curated → `INV-COVERAGE-WELLFORMED`) | Reads; writes. `add` appends last; `remove` of the last kind removes the key; an empty coverage block is removed | `CAP-COVERAGE` |
| `CLI-COVERAGE-CURATED` | `lspd coverage curated (set KIND --reason TEXT [--comment TEXT] \| unset KIND)` | subcommand, KIND; `--reason` for set · `--comment` | `OUT-WRITE-RESULT` (coverage) | `ERR-NOT-FOUND` (unset: absent); `ERR-INPUT-INVALID` (set: kind is fully bound) | Reads; writes. `set` on an existing kind replaces the reason in place | `CAP-COVERAGE` |
| `CLI-COMMENT-GET` | `lspd comment get <anchor>` | an anchor per *Global conventions* | `OUT-COMMENT` | `ERR-NOT-FOUND` (anchor's target absent, or no comment there) | Reads. No side effects | `CAP-COMMENT` |
| `CLI-COMMENT-SET` | `lspd comment set <anchor> --text TEXT` | anchor, `--text` (non-empty; may contain newlines → multi-line block) | `OUT-COMMENT` | `ERR-NOT-FOUND` (anchor's target absent); `ERR-USAGE` (empty text) | Reads; writes. Replaces any existing comment at the anchor, including a two-carrier one | `CAP-COMMENT` |
| `CLI-COMMENT-UNSET` | `lspd comment unset <anchor>` | anchor | `{anchor: OUT-ANCHOR, text: null}` | `ERR-NOT-FOUND` (no comment there) | Reads; writes | `CAP-COMMENT` |
| `CLI-SCHEMA` | `lspd schema [--checksum]` | · `--checksum` (flag) | raw `OUT-SCHEMA` (no envelope) | — (no file is read) | No side effects; never reads the target or the shipped file | `CAP-SCHEMA` |
| `CLI-HELP` | `lspd --help`, `lspd <cmd> --help`, `lspd <cmd> <sub> --help` | none | plain text (no envelope), exit 0 | `ERR-USAGE` (unknown command) | No side effects; nothing is read | `CAP-HELP` |
| `CLI-VERSION` | `lspd --version` | none | plain text `lspd <semver>`, exit 0 | — | No side effects | `CAP-HELP` |

### Error catalog (`ERR-*`)

| ID | Meaning | Exit | Forced by (contract test) |
|---|---|---|---|
| `ERR-USAGE` | Unknown command or option, missing required argument, empty-string argument, ID or kind failing its grammar on the command line, invalid `--json` text, mutually exclusive selectors given together | 1 | each listed condition, one test per condition |
| `ERR-FILE-MISSING` | The target file does not exist (any element except `init`, `schema`, `--help`, `--version`) | 2 | run in an empty temporary directory |
| `ERR-FILE-EXISTS` | `init` when the target exists | 1 | `init` twice |
| `ERR-IO` | The target cannot be read or written: permission denied, is a directory, unwritable directory for the temporary file | 2 | a directory named `bindings.yaml`; a read-only directory for writes |
| `ERR-PARSE` | The bytes are not a YAML document the Loader accepts: syntax error, duplicate key, not a mapping at top level, BOM or CRLF (`INV-BYTES` at the byte edge), a comment with no anchor | 2 | one fixture per condition |
| `ERR-FILE-TOO-LARGE` | The target exceeds 10 MiB and `--no-size-limit` was not given (checked before parsing; `SEC-FAIL-CLOSED`) | 1 | a generated file of 10 MiB + 1 byte; the same with the flag passes |
| `ERR-NOT-FOUND` | A named ID, entry, anchor, or coverage entry does not exist | 1 | `get` of an absent ID; `remove --locator` of an absent pair; `comment get` on a bare anchor |
| `ERR-DUPLICATE` | An `add-*` or `coverage … add` would create an entry whose identity already exists | 1 | `add-locator` twice with the same pair |
| `ERR-INPUT-INVALID` | Supplied input fails shape or rule validation; `details.findings` carries the `INV-*` findings. Nothing written | 1 | `add-locator` with a `:41` suffix; `set` with an unknown key; `add-assertion` with both `--run` and `--owed` |
| `ERR-INTERNAL` | Any exception not mapped above, including a post-write validation error (a tool bug by construction) | 2 | monkeypatch a command to raise; inject a post-validation error |

## Acceptance criteria

1. A contract test per `CLI-*` element exercising its happy path against a fixture and asserting the exact `result` projection and exit code.
2. A forced-condition test per row of the `ERR-*` catalog, asserting `ok:false`, the code, the `details` shape, the exit code, and that stdout holds exactly one JSON document and stderr is empty without `--debug`.
3. `OUT-ENVELOPE` conformance: a test-side shape assertion (own helper: fixed key set, types, nullability) checks the output of every test in 1 and 2; key order is asserted textually.
4. Bounded output: with a fixture of at least fifty bindings, `get` of two IDs yields exactly two `OUT-BINDING`s and the document contains no other binding's ID string; `list --kind INV` yields only `INV` summaries.
5. `--help` at all three levels exits 0 with plain text naming every argument of that level; the set of commands in `lspd --help` equals the set of `CLI-*` command paths.
6. `schema` raw output is byte-identical to `lspd.schema.json` and `schema --checksum` equals its SHA-256 (`SUCCESS-SCHEMA-MATCH`).
7. Empty-string arguments on every element produce `ERR-USAGE`.
8. `set` accepts the exact document `get` returned for the same ID (comments included) and the file is byte-identical afterwards (round trip through the projection).
9. Every `CLI-*` names a `CAP-*` it serves and every `CAP-*` is served by at least one `CLI-*`.

