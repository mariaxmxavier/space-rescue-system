"""Mission and application modules, classes and functions carry the four-part docstring.

What: checks the docstring labels of rescue/mission and rescue/application.
When called: collected by pytest in tests/architecture, so it runs in make check-all.
Why: mission keeps two labels on private definitions; application needs all four everywhere (R9).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import ast
import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PACKAGES = ("mission", "application")
STRICT_PACKAGES = frozenset({"application"})
PUBLIC_LABELS = ("What:", "When called:", "Why:", "Diagram:")
PRIVATE_LABELS = ("What:", "Why:")
DEFINITION_NODES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _is_private_module(path: Path) -> bool:
    return path.stem.startswith("_") and path.stem != "__init__"


def _label_offset(docstring: str, label: str) -> int | None:
    match = re.search(rf"^[ \t]*{re.escape(label)}", docstring, re.MULTILINE)
    return match.start() if match else None


def _diagram_problems(location: str, docstring: str) -> tuple[str, ...]:
    paths = tuple(token for token in docstring.split("Diagram:", 1)[1].split() if "/" in token)
    if not paths:
        return (f"{location}: Diagram: names no path",)
    return tuple(
        f"{location}: Diagram path does not exist: {path}"
        for path in paths
        if not (REPOSITORY_ROOT / path).exists()
    )


def _docstring_problems(location: str, docstring: str | None, private: bool) -> tuple[str, ...]:
    if docstring is None:
        return (f"{location}: no docstring",)
    labels = PRIVATE_LABELS if private else PUBLIC_LABELS
    offsets = tuple(_label_offset(docstring, label) for label in labels)
    missing = tuple(
        f"{location}: missing {label}" for label, offset in zip(labels, offsets) if offset is None
    )
    if missing:
        return missing
    if list(offsets) != sorted(offsets):
        return (f"{location}: labels out of order",)
    if "Diagram:" in docstring:
        return _diagram_problems(location, docstring)
    return ()


def _subjects(path: Path, strict: bool) -> tuple[tuple[str, str | None, bool], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=_relative(path))
    private_module = _is_private_module(path) and not strict
    module = ((_relative(path), ast.get_docstring(tree), private_module),)
    definitions = tuple(
        (
            f"{_relative(path)}:{node.name}",
            ast.get_docstring(node),
            private_module or (node.name.startswith("_") and not strict),
        )
        for node in tree.body
        if isinstance(node, DEFINITION_NODES)
    )
    return module + definitions


@pytest.mark.parametrize("package", PACKAGES)
def test_every_module_class_and_function_has_the_required_docstring(package: str):
    strict = package in STRICT_PACKAGES
    problems = tuple(
        problem
        for path in sorted((REPOSITORY_ROOT / "rescue" / package).rglob("*.py"))
        for location, docstring, private in _subjects(path, strict)
        for problem in _docstring_problems(location, docstring, private)
    )
    assert not problems, "\n".join(problems)
