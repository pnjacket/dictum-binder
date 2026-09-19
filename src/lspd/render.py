"""COMPONENT-RENDERER — results, findings and errors to the envelope or the human form.

Never sees library objects: only Model values, findings and ERR-* exceptions.

DICT: COMPONENT-RENDERER
"""

from __future__ import annotations

import json
from typing import Any

from lspd.errors import LspdError
from lspd.model import Anchor, Finding


def anchor(a: Anchor) -> dict[str, Any]:
    """DICT: OUT-ANCHOR"""
    return a.to_plain()


def finding(f: Finding) -> dict[str, Any]:
    """DICT: OUT-FINDING"""
    return {
        "code": f.code,
        "severity": f.severity,
        "anchor": anchor(f.anchor),
        "message": f.message,
    }


def error(err: LspdError) -> dict[str, Any]:
    """DICT: OUT-ERROR"""
    details: dict[str, Any] = {}
    for key, value in err.details.items():
        if key == "findings":
            details[key] = [finding(f) for f in value]
        elif key == "anchor" and isinstance(value, Anchor):
            details[key] = anchor(value)
        else:
            details[key] = value
    return {"code": err.code, "message": err.message, "details": details}


def _envelope_object(
    command: str,
    result: dict[str, Any] | None,
    pre: list[Finding],
    post: list[Finding],
    err: LspdError | None,
    version: str,
    schema_version: int,
) -> dict[str, Any]:
    return {
        "lspd": {"version": version, "schema_version": schema_version},
        "ok": err is None,
        "command": command,
        "result": result,
        "findings": {"pre": [finding(f) for f in pre], "post": [finding(f) for f in post]},
        "error": None if err is None else error(err),
    }


def render(
    command: str,
    result: dict[str, Any] | None,
    pre: list[Finding],
    post: list[Finding],
    err: LspdError | None,
    *,
    version: str,
    schema_version: int,
    human: bool,
) -> str:
    """One document: the compact JSON envelope (OUT-ENVELOPE) or the readable form."""
    obj = _envelope_object(command, result, pre, post, err, version, schema_version)
    if not human:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    return _human(obj)


def _human(obj: dict[str, Any]) -> str:
    lines = [
        f"lspd {obj['lspd']['version']} · schema {obj['lspd']['schema_version']} · "
        f"{obj['command'] or '(no command)'} · {'ok' if obj['ok'] else obj['error']['code']}"
    ]
    if obj["error"] is not None:
        lines.append(f"error: {obj['error']['code']}: {obj['error']['message']}")
        for key, value in obj["error"]["details"].items():
            if key == "findings":
                lines.append("  findings:")
                lines += [f"    {_finding_line(f)}" for f in value]
            elif key == "usage":
                lines.append("  usage:")
                lines += ["    " + s for s in str(value).rstrip("\n").split("\n")]
            else:
                lines.append(f"  {key}: {json.dumps(value, ensure_ascii=False)}")
    if obj["result"] is not None:
        lines.append("result:")
        lines += [
            "  " + s for s in json.dumps(obj["result"], ensure_ascii=False, indent=2).split("\n")
        ]
    for phase in ("pre", "post"):
        items = obj["findings"][phase]
        if items:
            lines.append(f"findings.{phase}:")
            lines += [f"  {_finding_line(f)}" for f in items]
    return "\n".join(lines) + "\n"


def _finding_line(f: dict[str, Any]) -> str:
    a = f["anchor"]
    where = a["type"]
    for key in ("id", "path", "symbol", "arm", "owed", "field", "kind"):
        if a.get(key) is not None:
            where += f" {key}={a[key]}"
    return f"[{f['severity']}] {f['code']} @ {where}: {f['message']}"
