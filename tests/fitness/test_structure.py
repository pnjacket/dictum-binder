"""Fitness tier: structural rules over src/dbind — imports, sole writer, orchestration, pragmas,
markers.
"""

from __future__ import annotations

import ast
import os
import re
import unittest

from tests._helpers import ROOT, SRC

STDLIB_OK_PREFIXES = ("dbind",)
FORBIDDEN_MODULES = {
    "socket",
    "http",
    "urllib",
    "requests",
    "ssl",
    "subprocess",
    "logging",
    "configparser",
    "dotenv",
    "asyncio",
}
FORBIDDEN_CALLS = {"eval", "exec", "compile"}
FORBIDDEN_ATTRS = {
    ("os", "system"),
    ("os", "environ"),
    ("os", "getenv"),
    ("os", "setuid"),
    ("os", "setgid"),
    ("os", "fork"),
    ("os", "execv"),
    ("os", "execvp"),
    ("os", "execl"),
    ("Path", "home"),
}


def _modules() -> dict[str, ast.Module]:
    out: dict[str, ast.Module] = {}
    for dirpath, _, files in os.walk(SRC):
        for name in files:
            if name.endswith(".py"):
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as handle:
                    out[os.path.relpath(path, SRC)] = ast.parse(handle.read(), path)
    return out


def _imports(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


class Imports(unittest.TestCase):
    """Architecture acceptance 1 and the import-level checks.

    ADR-LOAD-RUAMEL-EMIT-OWN, ADR-ARGPARSE, ADR-NO-LOGGING, SEC-*.
    """

    def test_ruamel_only_in_loader_and_no_other_third_party(self) -> None:
        import sys

        stdlib = set(sys.stdlib_module_names)
        for rel, tree in _modules().items():
            for name in _imports(tree):
                top = name.split(".")[0]
                if top == "ruamel":
                    self.assertEqual(rel, "loader.py", f"ruamel imported in {rel}")
                    continue
                self.assertTrue(
                    top in stdlib or top in STDLIB_OK_PREFIXES,
                    f"third-party import {name} in {rel}",
                )

    def test_forbidden_modules_and_calls(self) -> None:
        """DICT: SEC-ZERO-NETWORK / SEC-ZERO-EXEC / SEC-NO-AMBIENT-CONFIG / SEC-TRUST-BOUNDARY.

        Also ADR-NO-LOGGING.
        """
        for rel, tree in _modules().items():
            for name in _imports(tree):
                self.assertNotIn(name.split(".")[0], FORBIDDEN_MODULES, f"{name} in {rel}")
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.assertNotIn(
                            node.func.id, FORBIDDEN_CALLS, f"{node.func.id}() in {rel}"
                        )
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    self.assertNotIn(
                        (node.value.id, node.attr),
                        FORBIDDEN_ATTRS,
                        f"{node.value.id}.{node.attr} in {rel}",
                    )

    def test_argparse_only_in_cli(self) -> None:
        for rel, tree in _modules().items():
            if "argparse" in _imports(tree):
                self.assertEqual(rel, "cli.py")


class SoleWriter(unittest.TestCase):
    """Architecture acceptance 2 — only emitter.py opens a file for writing."""

    def test_only_emitter_writes(self) -> None:
        for rel, tree in _modules().items():
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = (
                    func.id
                    if isinstance(func, ast.Name)
                    else (func.attr if isinstance(func, ast.Attribute) else "")
                )
                is_os = (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "os"
                )
                if name in ("open", "fdopen") or (
                    is_os and name in ("mkstemp", "replace", "rename")
                ):
                    mode = next(
                        (a.value for a in node.args[1:2] if isinstance(a, ast.Constant)), "r"
                    )
                    if is_os or any(ch in str(mode) for ch in "wax"):
                        self.assertEqual(rel, "emitter.py", f"{name}() opens for writing in {rel}")


class Orchestration(unittest.TestCase):
    """Architecture acceptance 7.

    Flow components never import one another; cli.py imports all four; the graph is acyclic.
    """

    FLOW = {"loader", "commands", "emitter", "render"}
    LEAVES = {"model", "schema", "validator", "errors"}

    def _graph(self) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = {}
        for rel, tree in _modules().items():
            mod = rel[:-3].replace(os.sep, ".")
            comp = mod.split(".")[0]
            deps = set()
            for name in _imports(tree):
                if name.startswith("dbind."):
                    deps.add(name.split(".")[1])
                elif name == "dbind":
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom) and node.module == "dbind":
                            deps.update(alias.name for alias in node.names)
            graph.setdefault(comp, set()).update(d for d in deps if d != comp)
        return graph

    def test_flow_components_are_isolated_and_cli_orchestrates(self) -> None:
        graph = self._graph()
        for comp in self.FLOW:
            self.assertFalse(
                graph.get(comp, set()) & self.FLOW,
                f"{comp} imports a flow component: {graph.get(comp)}",
            )
        self.assertTrue(self.FLOW <= graph["cli"], graph["cli"])
        for leaf in self.LEAVES:
            self.assertFalse(graph.get(leaf, set()) & self.FLOW, leaf)
        self.assertFalse(graph.get("model", set()), "model imports nothing from dbind")

    def test_import_graph_is_acyclic(self) -> None:
        graph = self._graph()
        state: dict[str, int] = {}

        def visit(node: str, stack: list[str]) -> None:
            if state.get(node) == 1:
                self.fail(f"cycle: {' -> '.join(stack + [node])}")
            if state.get(node) == 2:
                return
            state[node] = 1
            for dep in graph.get(node, set()):
                visit(dep, stack + [node])
            state[node] = 2

        for node in graph:
            visit(node, [])


class PragmasAndMarkers(unittest.TestCase):
    """Quality gate 2 pragma rule; POLICY-SOURCE-MARKER; ADR-NO-LINE-NUMBERS on locators only."""

    TREES = ("src", "tests", "tools")

    def _files(self) -> list[str]:
        out: list[str] = []
        for tree in self.TREES:
            for dirpath, _, files in os.walk(os.path.join(ROOT, tree)):
                out += [
                    os.path.join(dirpath, f) for f in files if f.endswith((".py", ".yaml", ".yml"))
                ]
        return out

    PRAGMA = "pragma: " + "no cover"
    MARKER = "SOURCE" + ":"

    def test_every_no_cover_pragma_carries_a_reason(self) -> None:
        pattern = re.compile(self.PRAGMA + r"\s+—\s*\S")
        for path in self._files():
            with open(path, encoding="utf-8") as handle:
                for n, line in enumerate(handle, 1):
                    if self.PRAGMA in line:
                        self.assertRegex(line, pattern, f"{path}:{n} pragma without a reason")

    def test_source_markers_are_well_formed_and_mit(self) -> None:
        pattern = re.compile(self.MARKER + r"\s*(?P<origin>.+?)\s+—\s+(?P<license>\S+)")
        for path in self._files():
            with open(path, encoding="utf-8") as handle:
                for n, line in enumerate(handle, 1):
                    if self.MARKER in line and "POLICY-SOURCE-MARKER" not in line:
                        m = pattern.search(line)
                        self.assertIsNotNone(m, f"{path}:{n} malformed {self.MARKER} marker")
                        assert m is not None
                        self.assertEqual(
                            m.group("license"), "MIT", f"{path}:{n} non-MIT {self.MARKER} marker"
                        )


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
