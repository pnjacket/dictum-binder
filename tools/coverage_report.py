"""Gate 2 — 100 % line coverage of src/lspd via the standard library's ``trace``.

Runs the unit, golden, contract and fitness tiers in-process under
``trace.Trace``, then lists every executable line of ``src/lspd`` that never
ran. A line ending in ``# pragma: no cover — <reason>`` is excluded; a pragma
without a reason is left in (and the fitness tier rejects it). Exit 1 when
any line is uncovered.

Standard library only (the E2E tier runs in a subprocess and is not traced;
everything it exercises must also be reached in-process).
"""

from __future__ import annotations

import dis
import os
import re
import sys
import trace
import unittest
from types import CodeType

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "lspd")
PRAGMA = re.compile(r"#\s*pragma:\s*no cover\s+—\s*\S")
TIERS = ("unit", "golden", "contract", "fitness")


def _run_tiers() -> bool:
    suite = unittest.TestSuite()
    for tier in TIERS:
        suite.addTests(
            unittest.defaultTestLoader.discover(
                os.path.join(ROOT, "tests", tier), top_level_dir=ROOT
            )
        )
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=0).run(suite)
    return result.wasSuccessful()


class _IgnoreByFilename:
    """trace's own ``_Ignore`` caches decisions by module *basename*, so once the standard
    library's ``unittest/loader.py`` is ignored, ``lspd/loader.py`` is ignored too. This
    replacement decides by filename prefix and caches by filename."""

    def __init__(self, dirs: list[str]) -> None:
        self._dirs = [os.path.join(os.path.normpath(d), "") for d in dirs]
        self._cache: dict[str, int] = {}

    def names(self, filename: str, modulename: str) -> int:
        verdict = self._cache.get(filename)
        if verdict is None:
            verdict = int(any(filename.startswith(d) for d in self._dirs))
            self._cache[filename] = verdict
        return verdict


def _executable_lines(code: CodeType) -> set[int]:
    """Every line that owns bytecode in this code object or any nested one (what trace counts).

    Line 0 is the interpreter's RESUME prologue, not source."""
    lines = {lineno for _, lineno in dis.findlinestarts(code) if lineno}
    for const in code.co_consts:
        if isinstance(const, CodeType):
            lines |= _executable_lines(const)
    return lines


def _excluded_lines(lines: list[str]) -> set[int]:
    """Lines carrying a reasoned pragma; when such a line opens a block (ends in ``:``), the
    block's body is excluded with it, as coverage.py does."""
    excluded: set[int] = set()
    for index, line in enumerate(lines):
        if PRAGMA.search(line) is None:
            continue
        excluded.add(index + 1)
        code = line.split("#", 1)[0].rstrip()
        if not code.endswith(":"):
            continue
        indent = len(code) - len(code.lstrip())
        for later in range(index + 1, len(lines)):
            body = lines[later]
            if body.strip() == "":
                continue
            if len(body) - len(body.lstrip()) <= indent:
                break
            excluded.add(later + 1)
    return excluded


def report(counts: dict[tuple[str, int], int]) -> tuple[int, list[str]]:
    """Return (uncovered line count, report lines) over every module under src/lspd."""
    executed: dict[str, set[int]] = {}
    for (filename, lineno), _ in counts.items():
        if filename.startswith(SRC):
            executed.setdefault(filename, set()).add(lineno)
    out: list[str] = []
    missed_total = 0
    for dirpath, _, filenames in sorted(os.walk(SRC)):
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            filename = os.path.join(dirpath, name)
            with open(filename, encoding="utf-8") as handle:
                source = handle.read()
            lines = source.split("\n")
            executable = _executable_lines(compile(source, filename, "exec"))
            excluded = _excluded_lines(lines)
            missed = sorted(
                n
                for n in executable
                if n not in executed.get(filename, set()) and n not in excluded
            )
            rel = os.path.relpath(filename, ROOT)
            if missed:
                missed_total += len(missed)
                out.append(
                    f"{rel}: {len(missed)} uncovered line(s): {', '.join(str(n) for n in missed)}"
                )
            else:
                out.append(f"{rel}: 100%")
    return missed_total, out


def main() -> int:
    sys.path.insert(0, ROOT)
    sys.path.insert(0, os.path.join(ROOT, "src"))
    tracer = trace.Trace(count=1, trace=0)
    tracer.ignore = _IgnoreByFilename(  # pyrefly: ignore[bad-assignment] — duck-typed replacement
        [sys.prefix, sys.exec_prefix, sys.base_prefix, sys.base_exec_prefix]
    )
    ok = tracer.runfunc(_run_tiers)
    missed_total, lines = report(tracer.results().counts)
    print("\n".join(lines))
    if not ok:
        print("coverage report: the test run itself failed")
        return 1
    if missed_total:
        print(f"coverage report: {missed_total} uncovered line(s) in src/lspd")
        return 1
    print("coverage report: 100% line coverage of src/lspd")
    return 0


if __name__ == "__main__":  # pragma: no cover — script entry, exercised by CI
    sys.exit(main())
