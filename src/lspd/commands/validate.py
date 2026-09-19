"""CLI-VALIDATE — the findings summary. DICT: CLI-VALIDATE"""

from __future__ import annotations

from lspd.model import Finding


def result(findings: list[Finding], *, paths_checked: bool) -> dict[str, object]:
    """DICT: OUT-VALIDATE-RESULT"""
    errors = sum(1 for f in findings if f.severity == "error")
    return {"errors": errors, "warnings": len(findings) - errors, "paths_checked": paths_checked}
