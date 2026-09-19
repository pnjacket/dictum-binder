"""E2E-STANDARD runner: the installed executable by explicit path in the environment under test."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

DBIND = os.path.join(sys.prefix, "Scripts" if os.name == "nt" else "bin", "dbind")
INVOCATIONS: list[list[str]] = []


@dataclass
class Result:
    code: int
    stdout: str
    stderr: str

    @property
    def envelope(self) -> dict[str, Any]:
        return json.loads(self.stdout)


def dbind(argv: list[str], cwd: str) -> Result:
    INVOCATIONS.append(list(argv))
    proc = subprocess.run([DBIND, *argv], cwd=cwd, capture_output=True, check=False)
    return Result(proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8"))
