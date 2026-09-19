---
artifact: product-doc
role: concern
concern-id: interfaces-and-contracts
behavior: core
trigger: always
in-scope-subaspects: [cli-surface, error-model-catalog, versioning-compatibility]
current-rung: contract-grade
status: draft
version: 1.1.0
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
- **Global options**, accepted before **or after** the command (each subcommand mirrors them with suppressed defaults, so a value given before the command is never clobbered by the subcommand's parser): `--file PATH` (target map; default `./bindings.yaml`; no upward search; symlinks resolved to the final target, `SEC-SYMLINK-FINAL-TARGET`); `--human` (readable rendering); `--check-paths` (enables `CAP-PATHCHECK` wherever validation runs, including on write input: `INV-PATH-EXISTS`); `--no-size-limit` (lifts the 10 MiB target-size cap, `SEC-FAIL-CLOSED`); `--debug` (traceback on stderr in addition to the envelope); `--help`; `--version` (plain text `lspd <semver>`).
- **Output**: exactly one document on stdout per invocation. JSON envelope (`OUT-ENVELOPE`) by default; `--human` rendering otherwise. Exceptions: `--help` and `--version` print plain text; `schema` prints the raw schema document or the raw checksum line. stderr carries only `--debug` tracebacks. stdout is written as UTF-8 **bytes** regardless of locale or environment (`ensure_ascii=false` output must survive a C locale). `--help` and usage text are rendered with `prog` fixed to `lspd` and a fixed wrap width of 100 columns, never from `argv[0]`, `COLUMNS`, or the terminal, so their bytes are environment-independent.
- **Exit codes** per `PATTERN-EXIT-CODES`: `0` clean or warnings only · `1` caller-fixable · `2` environment · `130` interrupted. A read-only command on a file with error-level findings still returns its result (`ok: true`) and exits 1 by highest severity; reads are never refused, except by `ERR-SCHEMA-VERSION` (every element but `validate`). `--debug` adds a traceback on stderr for **every** `ERR-*`, including `ERR-USAGE` and `ERR-NOT-FOUND`, and nothing on success; the envelope is unchanged by it.
- **Empty values.** An empty-string argument anywhere is `ERR-USAGE`. There is no "unset" meaning for an empty value; unsetting is always an explicit command. An omitted optional argument means "not present", never a default value.
- **`--help`** at every level (`lspd --help`, `lspd <command> --help`, `lspd <command> <subcommand> --help`) lists every argument with its optionality and one-line meaning, the command's exit codes, and its error codes. `--help` on an unknown command is `ERR-USAGE`. A bare `lspd`, an unknown command, an unknown option, or a group without its subcommand (`lspd comment`) is `ERR-USAGE` whose `details.usage` carries the help text of the deepest level reached; the envelope's `command` is then the partial path parsed so far (`""` for bare `lspd`, `"comment"` for `lspd comment`). Anchors (`header`, `binding`, …) and the `add|remove` / `set|unset` choices are positional arguments, never a fourth parser level.
- **Pre/post findings.** Every write command reports `findings.pre` (loaded file) and `findings.post` (written file); read-only commands report `findings.pre` and an empty `findings.post`. Validation findings carry `INV-*` codes (Domain) and are not errors; only their severity moves the exit code. An **error envelope** still carries `findings.pre` — everything found before the error, warnings and errors alike — and `ERR-FILE-INVALID`'s `details.findings` repeats the error-level subset; `findings.post` is empty on every error envelope.
- **Input for writes.** Per-field flags for single entries; a JSON document for a whole binding (`set`), via `--json '<doc>'` or `--json -` to read stdin. An empty flag value is `ERR-USAGE` (the empty-argument rule). A flag value that violates a **value rule** — trailing whitespace or an empty first/last line in comment text (`INV-COMMENT-TEXT`), a control character or newline in any non-comment scalar (`INV-SYMBOL-NONEMPTY`), a control character in comment text (`INV-COMMENT-TEXT`), a malformed path (`INV-PATH-FORM`) — is `ERR-INPUT-INVALID` carrying that code, exactly as the same content inside `--json` is; the argument channel changes nothing about value rules. In a `--json` document an **omitted** optional key means the same as `null` (absent) — `set` replaces the whole binding, never merges. A `--json` text that is not valid JSON or not a JSON object is `ERR-USAGE`; an `id` or `kind` present but not matching the positional ID is `ERR-USAGE` too (the call contradicts itself). Every write re-emits the whole file through the Emitter, so a write on a valid but non-canonical file repairs its layout everywhere while preserving order (`INV-ORDER-PRESERVED`). Every `set`/`add-*` input is checked with `validate_input` before mutation (`PATTERN-VALIDATE-AROUND-WRITE`); a shape error is `ERR-INPUT-INVALID` with nothing written.
- **Addressing entries.** A locator is addressed by `--path P` and, when it has one, `--symbol S`. An assertion by `--path P --symbol S` (bound) or `--owed REF` (owed), plus `--arm A` when it has one. A field by its name. Exact match on the identity (`ENTITY-LOCATOR`, `ENTITY-ASSERTION`); no match is `ERR-NOT-FOUND`.
- **Error precedence** when one call could raise several codes, fixed so every contract test has one answer: argument grammar (`ERR-USAGE`) → file access (`ERR-FILE-MISSING`, `ERR-FILE-TOO-LARGE`, `ERR-IO`, `ERR-PARSE`) → `ERR-SCHEMA-VERSION` → pre-validation (`ERR-FILE-INVALID`) → target lookup (`ERR-NOT-FOUND`) → input validation (`ERR-INPUT-INVALID`) → identity (`ERR-DUPLICATE`) → post-validation (`ERR-INTERNAL`). The file-access group covers read-side failures; a write-side `ERR-IO` (unwritable directory, failed rename) is raised where it occurs, after validation — no pre-check is attempted. The target-file `path` — in `OUT-INIT-RESULT` and in the `details` of `ERR-FILE-MISSING`/`ERR-FILE-EXISTS`/`ERR-FILE-TOO-LARGE`/`ERR-IO`/`ERR-PARSE` — is the resolved absolute path; locator, field, assertion, and anchor `path` values are the repository-relative strings from the map.
- **`--human` minimums**: the rendering is not JSON, contains every code and message string of the envelope verbatim, and yields the same exit code; the layout of `result` is free. `schema`, `--help`, and `--version` are unaffected by the flag.
- **Anchors** for `comment` commands are a positional anchor kind followed by its identity: `header` · `binding ID` · `locator ID --path P [--symbol S]` · `field ID NAME` · `assertion ID (--path P --symbol S | --owed REF) [--arm A]` · `coverage` · `curated KIND`.

### CLI surface

Nineteen elements, minted in Contracts: `CLI-INIT`, `CLI-VALIDATE`, `CLI-FORMAT`, `CLI-GET`, `CLI-LIST`, `CLI-SET`, `CLI-ADD-LOCATOR`, `CLI-ADD-FIELD`, `CLI-ADD-ASSERTION`, `CLI-REMOVE`, `CLI-COVERAGE-GET`, `CLI-COVERAGE-FULLY-BOUND`, `CLI-COVERAGE-CURATED`, `CLI-COMMENT-GET`, `CLI-COMMENT-SET`, `CLI-COMMENT-UNSET`, `CLI-SCHEMA`, `CLI-HELP`, `CLI-VERSION`.

### Error model / catalog

Total and content-negotiated in the CLI sense (`PATTERN-ERROR-ENVELOPE`): every failure from every source, including argparse's own usage errors, file I/O, ruamel parse errors, and unexpected exceptions, is one of the twelve `ERR-*` codes in Contracts, rendered in the envelope (JSON) or the human form. A raw traceback or argparse's default stderr text reaching the caller is a contract violation.

### Versioning & compatibility

- `lspd` follows semantic versioning. The tool version appears in every envelope (`lspd.version`) and in `--version`; it is `1.0.0.dev0` until the release slice stamps `1.0.0`, and `lspd.schema_version` is `1` throughout.
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

1. **`get` with two IDs.** (The envelope is one compact line; wrapped here for readability.)
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
6. **A refused write.** The file has a `lines:` key on some other binding. `lspd add-locator ENTITY-Y --path src/y.py --symbol g` → `ok:false`, `error.code:"ERR-FILE-INVALID"`, `error.details.findings` naming `INV-CLOSED-KEYS` and `INV-NO-LINE-NUMBERS` at their anchors, exit 1, file untouched.
7. **Raw schema.** `lspd schema > lspd.schema.json` writes the exact shipped file; `lspd schema --checksum` prints one line, the 64-hex SHA-256.

## Design Decisions

| Decision | Rationale |
|---|---|
| Fixed projection shape: every optional key present, `null` when absent | Predictable tokens and no key-presence branching for the agent; a small size cost the operator accepts |
| Flags for single entries, JSON only for a whole binding | A locator is three fields; a binding is a document. Each channel matches its payload |
| `get` and `list` accept several targets | Fewer round trips at no loss of boundedness: output is still exactly the requested set |
| `set` accepts the `get` projection, comments included | `get` → edit → `set` is the natural whole-binding edit; forcing comments through a second call would split one intent |
| `schema` prints raw, everything else prints the envelope | The schema is a file for a converter author, not a result for an agent; wrapping it would make the shipped artifact and the printed one differ |
| Empty string is always a usage error | The no-silent-defaults rule applied to arguments |
| Writes refuse an invalid file; `format` too | Formatting or editing around error-level content would drop it silently; the agent runs `validate`, fixes, then writes. Warnings never block |
| `list` summaries by default, `--full` on request | Summaries are the bounded default; the full set is an explicit choice |

## Contracts

Register form: table row, ID in the first cell.

### Output documents (`OUT-*`)

| ID | Shape |
|---|---|
| `OUT-ENVELOPE` | The one JSON object every non-raw command prints. Keys, all always present: `lspd: {version: str (semver), schema_version: int}` · `ok: bool` (true iff `error` is null — findings never make it false; `validate` on a file with error findings is `ok: true`, exit 1) · `command: str` (the element's command path — the tokens before any positional choice — e.g. `"comment set"`, `"coverage fully-bound"`; `add|remove` and `set|unset` under `coverage` are positional choices, not path tokens) · `result: object \| null` (per element below; `null` on error) · `findings: {pre: [OUT-FINDING], post: [OUT-FINDING]}` · `error: OUT-ERROR \| null`. Serialised with `ensure_ascii=false`, keys in the order listed, no trailing whitespace, one trailing newline; not pretty-printed by default — compact separators `,` and `:` with no spaces, as the worked example shows (`--human` is the readable form) |
| `OUT-ERROR` | `{code: ERR-* id, message: str, details: object}`. `details` keys per code: `ERR-NOT-FOUND` → `{id, anchor: OUT-ANCHOR \| null}` · `ERR-DUPLICATE` → `{id, anchor: OUT-ANCHOR}` (for an ID-less target such as a `fully_bound` kind or the header, `id` is `null` and the anchor carries the identity, e.g. `{type: "coverage", kind: KIND}`) · `ERR-INPUT-INVALID` → `{findings: [OUT-FINDING]}` · `ERR-FILE-MISSING`/`ERR-FILE-EXISTS`/`ERR-FILE-TOO-LARGE`/`ERR-IO`/`ERR-PARSE` → `{path: str, reason: str}` · `ERR-FILE-INVALID` → `{findings: [OUT-FINDING]}` (the pre-write errors) · `ERR-SCHEMA-VERSION` → `{found: int \| null, expected: int}` (`null` when missing or not an integer) · `ERR-USAGE` → `{usage: str}` · `ERR-INTERNAL` → `{exception: str}` |
| `OUT-FINDING` | Projection of `ENTITY-FINDING`: `{code: INV-* id, severity: "error" \| "warning", anchor: OUT-ANCHOR, message: str}` |
| `OUT-ANCHOR` | Fixed-key object: `{type: "file" \| "header" \| "binding" \| "locator" \| "field" \| "assertion" \| "coverage" \| "curated", id: str \| null, path: str \| null, symbol: str \| null, arm: str \| null, owed: str \| null, field: str \| null, kind: str \| null}`; only the keys meaningful for `type` are non-null |
| `OUT-BINDING` | Projection of `ENTITY-BINDING` with its anchored comments: `{id, kind, comment: str \| null, locators: [OUT-LOCATOR], compare_via: str \| null, fields: {name: OUT-FIELD-LOCATOR} \| null, wire: {casing: str \| null, enums: str \| null, dates: str \| null} \| null, asserted_by: [OUT-ASSERTION] \| null}`. `locators` is `[]` for a stub. Used as the **input** projection of `CLI-SET` too: `id` and `kind` may be omitted; if present they must equal the positional ID and its derived kind (`ERR-USAGE` otherwise — the call contradicts itself) |
| `OUT-LOCATOR` | `{path: str, symbol: str \| null, role: "producer" \| "consumer" \| null, comment: str \| null}` |
| `OUT-FIELD-LOCATOR` | `{path: str, symbol: str \| null, comment: str \| null}` |
| `OUT-ASSERTION` | `{path: str \| null, symbol: str \| null, run: str \| null, arm: str \| null, owed: str \| null, comment: str \| null}`; exactly the bound or the owed subset is non-null per `INV-ASSERTION-SHAPE` |
| `OUT-BINDING-SUMMARY` | `{id, kind, stub: bool, locators: int, fields: int, assertions: int, has_comment: bool}` — `has_comment` is true when any comment exists anywhere in the binding (its own anchor, a locator, a field, or an assertion) |
| `OUT-COVERAGE` | `{comment: str \| null, fully_bound: [str], curated: {KIND: {reason: str, comment: str \| null}}}`; empty list / empty object when absent in the file |
| `OUT-COMMENT` | `{anchor: OUT-ANCHOR, text: str}` |
| `OUT-VALIDATE-RESULT` | `{errors: int, warnings: int, paths_checked: bool}` — the findings themselves are in `findings.pre` |
| `OUT-FORMAT-RESULT` | `{changed: bool, checked_only: bool}` |
| `OUT-INIT-RESULT` | `{path: str}` — the resolved path `init` created |
| `OUT-WRITE-RESULT` | For every mutating element except `format` and `init`: `{binding: OUT-BINDING}` after the write (`remove` of a whole binding returns `{binding: null, removed: str}`); coverage elements return `{coverage: OUT-COVERAGE}`; comment elements return `OUT-COMMENT` (or `{anchor, text: null}` after unset) |
| `OUT-SCHEMA` | Raw: the JSON Schema document (draft 2020-12) of `ENTITY-MAP`, serialised with sorted keys, two-space indent, `ensure_ascii=false`, one trailing newline — byte-identical to the shipped `lspd.schema.json`. With `--checksum`: one line, lowercase 64-hex SHA-256 of those bytes, newline |

### CLI elements (`CLI-*`)

Every element: owning component `COMPONENT-CLI`; served by `COMPONENT-COMMANDS`; global options apply. "Reads" = runs Loader + pre-validation; "writes" = the full pipeline with `PATTERN-VALIDATE-AROUND-WRITE` and `PATTERN-ATOMIC-REPLACE`. Common errors on every element that reads the file (all but `init`, `schema`, `--help`, `--version`): `ERR-FILE-MISSING`, `ERR-FILE-TOO-LARGE`, `ERR-IO`, `ERR-PARSE`, and — every reader except `validate` — `ERR-SCHEMA-VERSION`; on every element that writes an existing file (all writers but `init`) additionally `ERR-FILE-INVALID`; on every element: `ERR-USAGE`, `ERR-INTERNAL`. Rows list only the element-specific errors.

| ID | Signature | Inputs (required · optional) | Output (`result`) | Element-specific errors | Pre / post · side effects | Serves |
|---|---|---|---|---|---|---|
| `CLI-INIT` | `lspd init` | none | `OUT-INIT-RESULT` | `ERR-FILE-EXISTS` (the resolved target exists, any content); `ERR-IO` (unwritable) | Pre: the resolved target is absent — a dangling symlink resolves to a nonexistent final path, which `init` creates so the link becomes valid. Post: target is the canonical empty map (`schema_version: 1` from `SCHEMA_VERSION`, `bindings: {}`), umask-default mode, `findings.post` empty. Writes | `CAP-INIT` |
| `CLI-VALIDATE` | `lspd validate` | none | `OUT-VALIDATE-RESULT` | — (never `ERR-SCHEMA-VERSION`: a mismatch is reported as the `INV-SCHEMA-VERSION` finding) | Reads. Exit 1 iff any error finding. `--check-paths` adds `INV-PATH-EXISTS` findings (severity error). No side effects | `CAP-VALIDATE`, `CAP-PATHCHECK` |
| `CLI-FORMAT` | `lspd format [--check]` | · `--check` (flag) | `OUT-FORMAT-RESULT` | `ERR-FILE-INVALID` (error-level pre-findings, incl. `INV-PATH-EXISTS` under `--check-paths`; nothing written, also under `--check`) | Reads; writes unless `--check`. Post: file is the canonical layout (`INV-CANONICAL-FIXPOINT`); layout-class warnings (`INV-BYTES`, trailing whitespace) are repaired, other warnings kept and reported. `changed` = emitted bytes ≠ original bytes. Exit matrix: error-level pre-finding → `ERR-FILE-INVALID`, exit 1; otherwise `--check` and `changed: true` → exit 1 (`ok: true`); `--check` and unchanged → 0; a write → 0 (warnings do not raise it). Under `--check`, `findings.post` is the post-validation of the would-be-written model | `CAP-FORMAT` |
| `CLI-GET` | `lspd get ID [ID …]` | one or more IDs (each must satisfy `INV-ID-GRAMMAR`, else `ERR-USAGE`) | `{bindings: [OUT-BINDING]}` in argument order | `ERR-NOT-FOUND` (first unknown ID; nothing returned) | Reads (exit 1 if the file has error-level findings, result still returned). Repeated IDs return repeated copies in argument order. Output contains exactly the requested bindings (`SUCCESS-BOUNDED-OUTPUT`). No side effects | `CAP-QUERY` |
| `CLI-LIST` | `lspd list [--kind KIND …] [--full]` | · `--kind` repeatable (each `[A-Z][A-Z0-9]+`); `--full` (flag) | `{bindings: [OUT-BINDING-SUMMARY]}` or, with `--full`, `[OUT-BINDING]`; file order; empty list allowed | — | Reads. No kinds = all bindings; `--kind` is exact, case-sensitive equality on the derived kind, its argument must match `[A-Z][A-Z0-9]+` (else `ERR-USAGE`), and repeats form a union. A well-formed kind that matches nothing gives an empty result, exit 0. With `--full` the result is still `{bindings: [OUT-BINDING]}` | `CAP-QUERY` |
| `CLI-SET` | `lspd set ID --json DOC` | ID; `--json` (a document per `OUT-BINDING`, or `-` for stdin) | `OUT-WRITE-RESULT` | `ERR-USAGE` (invalid JSON, non-object, `id`/`kind` mismatch); `ERR-INPUT-INVALID` (shape or rule violation in the document) | Reads; writes. Unknown ID → created, appended last; known ID → replaced in place. Comments in the document are set at their anchors; absent comments (`null`) clear; a comment string that is empty or has trailing whitespace is `ERR-INPUT-INVALID` carrying `INV-COMMENT-TEXT`. Warnings in the input are written and reported in `findings.post` | `CAP-SET`, `CAP-COMMENT` |
| `CLI-ADD-LOCATOR` | `lspd add-locator ID --path P [--symbol S] [--role producer\|consumer] [--comment TEXT]` | ID, `--path` · `--symbol`, `--role`, `--comment` | `OUT-WRITE-RESULT` | `ERR-NOT-FOUND` (ID); `ERR-DUPLICATE` (same path+symbol present); `ERR-INPUT-INVALID` | Reads; writes. Appends last; order untouched (`INV-ORDER-PRESERVED`) | `CAP-ADD` |
| `CLI-ADD-FIELD` | `lspd add-field ID NAME --path P [--symbol S] [--comment TEXT]` | ID, NAME, `--path` · `--symbol`, `--comment` | `OUT-WRITE-RESULT` | `ERR-NOT-FOUND` (ID); `ERR-INPUT-INVALID` | Reads; writes. Existing NAME is replaced in place, keeping its comment unless `--comment` is given; new NAME appended last | `CAP-ADD` |
| `CLI-ADD-ASSERTION` | `lspd add-assertion ID (--path P --symbol S --run R \| --owed REF) [--arm A] [--comment TEXT]` | ID and exactly one shape · `--arm`, `--comment` | `OUT-WRITE-RESULT` | `ERR-NOT-FOUND` (ID); `ERR-DUPLICATE` (same identity present); `ERR-USAGE` (a partial shape on the command line: `--path` without `--symbol`/`--run`, `--run` alone, `--arm` alone, or both shapes at once — argument grammar); `ERR-INPUT-INVALID` (a value rule such as `INV-PATH-FORM`) | Reads; writes. Appends last | `CAP-ADD` |
| `CLI-REMOVE` | `lspd remove ID [--locator --path P [--symbol S] \| --field NAME \| --assertion (--path P --symbol S \| --owed REF) [--arm A]]` | ID · exactly one entry selector, or none for the whole binding | `OUT-WRITE-RESULT` | `ERR-NOT-FOUND` (ID or entry) | Reads; writes. Whole binding removed with its comments; removing the last locator leaves the stub; removing the last field or assertion removes that key | `CAP-REMOVE` |
| `CLI-COVERAGE-GET` | `lspd coverage get` | none | `{coverage: OUT-COVERAGE}` | — | Reads. No side effects | `CAP-COVERAGE` |
| `CLI-COVERAGE-FULLY-BOUND` | `lspd coverage fully-bound (add \| remove) KIND` | subcommand, KIND (`[A-Z][A-Z0-9]+`) | `OUT-WRITE-RESULT` (coverage) | `ERR-DUPLICATE` (add: already listed); `ERR-NOT-FOUND` (remove: not listed); `ERR-INPUT-INVALID` (add: kind is curated → `INV-COVERAGE-WELLFORMED`) | Reads; writes. `add` appends last; `remove` of the last kind removes the key; an empty coverage block is removed together with its comment (as `remove ID` drops a binding's comments) | `CAP-COVERAGE` |
| `CLI-COVERAGE-CURATED` | `lspd coverage curated (set KIND --reason TEXT [--comment TEXT] \| unset KIND)` | subcommand, KIND; `--reason` for set · `--comment` | `OUT-WRITE-RESULT` (coverage) | `ERR-NOT-FOUND` (unset: absent); `ERR-INPUT-INVALID` (set: kind is fully bound → `INV-COVERAGE-WELLFORMED`) | Reads; writes. `set` on an existing kind replaces the reason in place, keeping its comment unless `--comment` is given; `unset` drops the entry with its comment; unsetting the last entry removes the `curated` key, and an empty coverage block is removed with its comment | `CAP-COVERAGE` |
| `CLI-COMMENT-GET` | `lspd comment get <anchor>` | an anchor per *Global conventions* | `OUT-COMMENT` | `ERR-NOT-FOUND` (anchor's target absent, or no comment there) | Reads. No side effects | `CAP-COMMENT` |
| `CLI-COMMENT-SET` | `lspd comment set <anchor> --text TEXT` | anchor, `--text` (non-empty; may contain newlines → multi-line block; no line may carry trailing whitespace; first and last lines non-empty; a text of only empty lines, or one containing a control character, violates the value rule → `ERR-INPUT-INVALID` carrying `INV-COMMENT-TEXT`) | `OUT-COMMENT` | `ERR-NOT-FOUND` (anchor's target absent); `ERR-USAGE` (empty text); `ERR-INPUT-INVALID` carrying `INV-COMMENT-TEXT` (trailing whitespace on any line, an empty first or last line, a text of only empty lines, or a control character) | Reads; writes. Replaces any existing comment at the anchor, and the carrier form follows the new text (single-line → trailing on an entry, multi-line → block above) (a two-carrier anchor is an error-level finding, so the write is refused until the file is fixed by hand) | `CAP-COMMENT` |
| `CLI-COMMENT-UNSET` | `lspd comment unset <anchor>` | anchor | `{anchor: OUT-ANCHOR, text: null}` | `ERR-NOT-FOUND` (no comment there) | Reads; writes | `CAP-COMMENT` |
| `CLI-SCHEMA` | `lspd schema [--checksum]` | · `--checksum` (flag) | raw `OUT-SCHEMA` (no envelope) | — (no file is read) | No side effects; never reads the target or the shipped file | `CAP-SCHEMA` |
| `CLI-HELP` | `lspd --help`, `lspd <cmd> --help`, `lspd <cmd> <sub> --help` | none | plain text (no envelope), exit 0 | `ERR-USAGE` (unknown command) | No side effects; nothing is read | `CAP-HELP` |
| `CLI-VERSION` | `lspd --version` | none | plain text `lspd <semver>`, exit 0 | — | No side effects | `CAP-HELP` |

### Error catalog (`ERR-*`)

| ID | Meaning | Exit | Forced by (contract test) |
|---|---|---|---|
| `ERR-USAGE` | Unknown command or option, missing required argument, empty-string argument (incl. an empty `--text`/`--comment`), ID or kind failing its grammar on the command line, invalid or non-object `--json` text, an `id`/`kind` in the document contradicting the positional ID, a partial assertion shape on the command line, mutually exclusive selectors given together, a bare `lspd` or a group without its subcommand | 1 | each listed condition, one test per condition |
| `ERR-FILE-MISSING` | The target file does not exist (any element except `init`, `schema`, `--help`, `--version`) | 2 | run in an empty temporary directory |
| `ERR-FILE-EXISTS` | `init` when the target exists | 1 | `init` twice |
| `ERR-IO` | The target cannot be read or written: permission denied, is a directory, unwritable directory for the temporary file | 2 | a directory named `bindings.yaml`; a read-only directory for writes |
| `ERR-PARSE` | The bytes are not a YAML document the Loader can turn into a Model: syntax error, duplicate key, not a mapping at top level, non-UTF-8, BOM or CRLF (the unloadable half of `INV-BYTES`), a comment where no anchor exists (the unloadable half of `INV-COMMENT-ANCHORED`). Fixability drives the code: none of these can be fixed through `lspd` | 2 | one fixture per condition |
| `ERR-FILE-TOO-LARGE` | The target exceeds 10 MiB and `--no-size-limit` was not given (checked before parsing; `SEC-FAIL-CLOSED`) | 1 | a generated file of 10 MiB + 1 byte; the same with the flag passes |
| `ERR-SCHEMA-VERSION` | The file's `schema_version` is missing, not an integer, or differs from the binary's `SCHEMA_VERSION`; raised by every element except `validate` before any other work | 1 | a fixture with `schema_version: 2` under `get`, `set`, `format` |
| `ERR-FILE-INVALID` | A write element found error-level findings in the pre-validation pass; `details.findings` carries them; nothing written | 1 | `add-locator` against a fixture with a `lines:` key elsewhere in the file; `format` against the same fixture |
| `ERR-NOT-FOUND` | A named ID, entry, anchor, or coverage entry does not exist | 1 | `get` of an absent ID; `remove --locator` of an absent pair; `comment get` on a bare anchor |
| `ERR-DUPLICATE` | An `add-*` or `coverage … add` would create an entry whose identity already exists | 1 | `add-locator` twice with the same pair |
| `ERR-INPUT-INVALID` | Supplied input — from flags or from `--json` alike — fails shape or rule validation; `details.findings` carries the `INV-*` findings (including `INV-PATH-EXISTS` when `--check-paths` is on, `INV-COMMENT-TEXT` for comment text, `INV-SYMBOL-NONEMPTY` for a control character). Nothing written | 1 | `add-locator` with a `:41` suffix; `set` with an unknown key; `comment set --text "abc "`; `add-locator --symbol $'a\\nb'`; `add-locator` of a missing path with `--check-paths` |
| `ERR-INTERNAL` | Any exception not mapped above, including a post-write validation error (a tool bug by construction) | 2 | monkeypatch a command to raise; inject a post-validation error |

## Acceptance criteria

1. A contract test per `CLI-*` element exercising its happy path against a fixture and asserting the exact `result` projection and exit code.
2. A forced-condition test per row of the `ERR-*` catalog, asserting `ok:false`, the code, the `details` shape, the exit code, and that stdout holds exactly one JSON document and stderr is empty without `--debug`.
3. Envelope conformance for `OUT-ENVELOPE`: a test-side shape assertion (own helper: fixed key set, types, nullability) checks the output of every test in 1 and 2; key order is asserted textually.
4. Bounded output: with a fixture of at least fifty bindings, `get` of two IDs yields exactly two `OUT-BINDING`s and the document contains no other binding's ID string; `list --kind INV` yields only `INV` summaries.
5. `--help` at all three levels exits 0 with plain text naming every argument of that level; a fitness test walks the help tree (`lspd --help`, then `lspd <cmd> --help` for each listed command, then each listed subcommand) and asserts the union of paths equals the set of `CLI-*` command paths, `--help` and `--version` being options rather than paths.
6. `schema` raw output is byte-identical to `lspd.schema.json` and `schema --checksum` equals its SHA-256 (`SUCCESS-SCHEMA-MATCH`).
7. Empty-string arguments on every element produce `ERR-USAGE`.
8. `set` accepts the exact document `get` returned for the same ID (comments included) and the file is byte-identical afterwards when the fixture is canonical (round trip through the projection).
9. E2E and contract tests compare **parsed** JSON (codes, `ok`, `result`, exit code) and never byte-compare an envelope, since message texts are not contracted; file bytes are compared exactly.
10. Every `CLI-*` names a `CAP-*` it serves and every `CAP-*` is served by at least one `CLI-*`.

