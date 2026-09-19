"""Shared test helpers: in-process CLI runs with byte-captured stdout, fixtures, temp dirs."""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
DOCS = os.path.join(ROOT, "docs")
SRC = os.path.join(ROOT, "src", "lspd")


def fixture(name: str) -> str:
    return os.path.join(FIXTURES, name)


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


@dataclass
class Run:
    code: int
    stdout: str
    stderr: str

    @property
    def envelope(self) -> dict[str, Any]:
        return json.loads(self.stdout)


def run_cli(argv: list[str], cwd: str | None = None) -> Run:
    """Run ``lspd.cli.main`` in-process with a binary-capable stdout, like a real process."""
    from lspd import cli

    out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    err = io.StringIO()
    old_out, old_err, old_cwd = sys.stdout, sys.stderr, os.getcwd()
    sys.stdout, sys.stderr = out, err
    try:
        if cwd is not None:
            os.chdir(cwd)
        code = cli.main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        os.chdir(old_cwd)
    out.flush()
    return Run(code, out.buffer.getvalue().decode("utf-8"), err.getvalue())


class TempDir:
    """A fresh temporary working directory, removed afterwards."""

    def __enter__(self) -> str:
        self.path = tempfile.mkdtemp(prefix="lspd-test-")
        return self.path

    def __exit__(self, *exc: object) -> None:
        shutil.rmtree(self.path, ignore_errors=True)


def copy_fixture(name: str, into: str, as_name: str = "bindings.yaml") -> str:
    target = os.path.join(into, as_name)
    shutil.copyfile(fixture(name), target)
    return target


KINDS = ("ENTITY", "INV", "API", "ROUTE", "CAP", "SCREEN", "COMPONENT", "POLICY", "SEC", "ADR")


def many_bindings(count: int = 50) -> bytes:
    """A deterministic canonical map with ``count`` bindings across ten kinds (bounded-output
    tests, Quality: generated, never committed)."""
    out = ["schema_version: 1", "", "bindings:", ""]
    for n in range(count):
        kind = KINDS[n % len(KINDS)]
        out += [
            f"  {kind}-GEN-N{n:03d}:",
            "    locators:",
            f"      - {{ path: src/gen/{kind.lower()}_{n:03d}.py, symbol: Gen{n:03d} }}",
            "",
        ]
    out[-1] = ""
    return ("\n".join(out)).rstrip("\n").encode("utf-8") + b"\n"
