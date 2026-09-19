"""Fitness tier: Interfaces acceptance 5 — the help tree walk yields exactly the CLI-* command
paths; and Interfaces acceptance 10 — every CLI-* names a CAP-* and every CAP-* is served."""

from __future__ import annotations

import os
import re
import unittest

from tests._helpers import DOCS, run_cli

ROW = re.compile(r"^\| `(CLI-[A-Z-]+)` \| `lspd ([^`]*)` \|(.*)\|\s*$")
LISTING_HEAD = re.compile(r"^  <(command|subcommand)>$")
LISTING_ITEM = re.compile(r"^    (\S+)\s{2,}\S")


def documented_paths() -> dict[str, str]:
    """CLI-* → command path: the leading lowercase tokens of the invocation cell (`--help` and
    `--version` are options, so their path is empty)."""
    out: dict[str, str] = {}
    with open(os.path.join(DOCS, "interfaces-and-contracts.md"), encoding="utf-8") as handle:
        for line in handle:
            m = ROW.match(line)
            if not m:
                continue
            tokens: list[str] = []
            for token in m.group(2).split():
                if re.match(r"^[a-z][a-z-]*$", token):
                    tokens.append(token)
                else:
                    break
            out[m.group(1)] = " ".join(tokens)
    return out


def walk(path: list[str]) -> set[str]:
    """Paths reachable from `lspd <path> --help`: the leaves of the listing tree."""
    run = run_cli([*path, "--help"])
    assert run.code == 0, run.stdout
    lines = run.stdout.split("\n")
    children: list[str] = []
    for index, line in enumerate(lines):
        if LISTING_HEAD.match(line):
            for later in lines[index + 1 :]:
                item = LISTING_ITEM.match(later)
                if item is None:
                    break
                children.append(item.group(1))
    if not children:
        return {" ".join(path)}
    found: set[str] = set()
    for child in children:
        found |= walk([*path, child])
    return found


class HelpTree(unittest.TestCase):
    def test_walk_yields_exactly_the_cli_command_paths(self) -> None:
        documented = {p for p in documented_paths().values() if p}
        self.assertEqual(len(documented), 17)
        self.assertEqual(walk([]), documented)

    def test_every_cli_names_a_cap_and_every_cap_is_served(self) -> None:
        served: set[str] = set()
        with open(os.path.join(DOCS, "interfaces-and-contracts.md"), encoding="utf-8") as handle:
            for line in handle:
                m = ROW.match(line)
                if m:
                    caps = re.findall(r"`(CAP-[A-Z-]+)`", m.group(3).split("|")[-1])
                    self.assertTrue(caps, m.group(1))
                    served.update(caps)
        with open(os.path.join(DOCS, "product-and-requirements.md"), encoding="utf-8") as handle:
            minted = set(re.findall(r"^\| `(CAP-[A-Z-]+)` \|", handle.read(), re.M))
        self.assertEqual(minted - served, set())


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
