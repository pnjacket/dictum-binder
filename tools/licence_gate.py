"""Gate 7 — POLICY-INBOUND-MIT-ONLY over the resolved environment.

Standard library only. Every installed distribution must be exactly MIT by
the matching rule in Governance & Compliance; ``pip`` and ``setuptools`` are
the fixed infrastructure exemption (the scope statement encoded, not an
allowlist). Prints the resolved list; exits 1 on any failure.

DICT: POLICY-INBOUND-MIT-ONLY
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from importlib import metadata

INFRASTRUCTURE = frozenset({"pip", "setuptools"})
MIT_CLASSIFIER = "License :: OSI Approved :: MIT License"


def normalise_license_field(value: str) -> str:
    words = " ".join(value.lower().split()).split(" ")
    if words and words[-1] == "license":
        words = words[:-1]
    return " ".join(words)


def verdict(
    expression: str | None, classifiers: Iterable[str], license_field: str | None
) -> tuple[bool, str]:
    """Apply the three-channel matching rule; return (passes, reason)."""
    channels: list[tuple[str, bool]] = []
    if expression is not None and expression.strip():
        channels.append(("License-Expression", expression.strip() == "MIT"))
    license_classifiers = [c for c in classifiers if c.startswith("License ::")]
    if license_classifiers:
        channels.append(("classifier", license_classifiers == [MIT_CLASSIFIER]))
    if license_field is not None and license_field.strip():
        channels.append(("License", normalise_license_field(license_field) == "mit"))
    if not channels:
        return False, "missing: no licence metadata"
    results = {ok for _, ok in channels}
    if len(results) > 1:
        return False, "ambiguous: " + ", ".join(
            f"{name}={'MIT' if ok else 'not MIT'}" for name, ok in channels
        )
    ok = results.pop()
    return ok, ("MIT via " + channels[0][0]) if ok else ("not MIT via " + channels[0][0])


def _field(dist: metadata.Distribution, name: str) -> str | None:
    return dist.metadata[name] if name in dist.metadata else None


def check_distribution(dist: metadata.Distribution) -> tuple[str, bool, str]:
    name = dist.metadata["Name"] or "?"
    if name.lower() in INFRASTRUCTURE:
        return name, True, "infrastructure (exempt)"
    expression = _field(dist, "License-Expression")
    classifiers = dist.metadata.get_all("Classifier") or []
    license_field = _field(dist, "License")
    ok, reason = verdict(expression, classifiers, license_field)
    return name, ok, reason


def run(dists: Iterable[metadata.Distribution]) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    failures: list[str] = []
    for dist in sorted(dists, key=lambda d: (d.metadata["Name"] or "").lower()):
        name, ok, reason = check_distribution(dist)
        lines.append(f"{'PASS' if ok else 'FAIL'} {name} {dist.version}: {reason}")
        if not ok:
            failures.append(name)
    return lines, failures


def main() -> int:
    lines, failures = run(metadata.distributions())
    print("\n".join(lines))
    if failures:
        print(f"licence gate: {len(failures)} distribution(s) are not MIT: {', '.join(failures)}")
        return 1
    print("licence gate: every distribution is MIT (infrastructure exempt: pip, setuptools)")
    return 0


if __name__ == "__main__":  # pragma: no cover — script entry, exercised by CI
    sys.exit(main())
