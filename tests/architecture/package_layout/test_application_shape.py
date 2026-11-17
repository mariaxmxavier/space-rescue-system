"""The shape of the application layer: a thin facade, small services and one public name per file.

What: checks by AST that every public RescueCentral method is one returned call, that it has no
  private methods, that each service file is at most 250 lines and that each application file
  defines at most one public top-level name.
When called: collected by pytest in tests/architecture, so it runs in make check-all.
Why: a facade that only delegates keeps the use cases in the services, and the size and name
  limits keep each file readable and findable by its path.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
APPLICATION = REPOSITORY_ROOT / "rescue" / "application"
SERVICES = APPLICATION / "services"
MAX_SERVICE_LINES = 250
EXEMPT_FROM_ONE_NAME = {
    APPLICATION / "contracts" / "__init__.py",
    APPLICATION / "contracts" / "snapshots.py",
}


def _relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _facade_methods() -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = _parse(APPLICATION / "central.py")
    facade = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "RescueCentral"
    )
    return [n for n in facade.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]


def _statements(method: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
    return method.body[1:] if ast.get_docstring(method) is not None else method.body


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _is_type_checking(node: ast.stmt) -> bool:
    return isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test)


def _assigned_names(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, ast.AnnAssign | ast.AugAssign):
        targets = [node.target]
    elif isinstance(node, ast.TypeAlias):
        targets = [node.name]
    else:
        return []
    return [t.id for target in targets for t in ast.walk(target) if isinstance(t, ast.Name)]


def _public_names(path: Path) -> list[str]:
    names: list[str] = []
    for node in _parse(path).body:
        if _is_type_checking(node):
            continue
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            names.append(node.name)
        else:
            names.extend(_assigned_names(node))
    return [n for n in names if not n.startswith("_")]


class ApplicationShapeTest(unittest.TestCase):
    def test_every_public_facade_method_returns_one_call(self) -> None:
        offenders = [
            f"rescue/application/central.py: RescueCentral.{method.name} (line {method.lineno})"
            for method in _facade_methods()
            if not method.name.startswith("_")
            and not (
                len(body := _statements(method)) == 1
                and isinstance(body[0], ast.Return)
                and isinstance(body[0].value, ast.Call)
            )
        ]
        self.assertEqual(
            [], offenders, f"facade methods that are not one returned call: {offenders}"
        )

    def test_facade_has_no_private_methods(self) -> None:
        offenders = [
            f"rescue/application/central.py: RescueCentral.{method.name} (line {method.lineno})"
            for method in _facade_methods()
            if method.name.startswith("_") and not _is_dunder(method.name)
        ]
        self.assertEqual([], offenders, f"private facade methods: {offenders}")

    def test_service_files_stay_within_the_line_limit(self) -> None:
        files = sorted(SERVICES.rglob("*.py"))
        self.assertTrue(files, "no service files found under rescue/application/services")
        offenders = [
            f"{_relative(path)}: {count} lines"
            for path in files
            if (count := len(path.read_text(encoding="utf-8").splitlines())) > MAX_SERVICE_LINES
        ]
        self.assertEqual(
            [], offenders, f"service files over {MAX_SERVICE_LINES} lines: {offenders}"
        )

    def test_each_application_file_has_at_most_one_public_name(self) -> None:
        offenders = [
            f"{_relative(path)}: {names}"
            for path in sorted(APPLICATION.rglob("*.py"))
            if path not in EXEMPT_FROM_ONE_NAME and len(names := _public_names(path)) > 1
        ]
        self.assertEqual([], offenders, f"files with more than one public name: {offenders}")
