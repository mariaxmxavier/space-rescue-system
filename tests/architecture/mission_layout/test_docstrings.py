"""Mission modules, classes and public functions carry the four-part docstring."""

import ast
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MISSION_ROOT = REPOSITORY_ROOT / "rescue" / "mission"
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


def _subjects(path: Path) -> tuple[tuple[str, str | None, bool], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=_relative(path))
    private_module = _is_private_module(path)
    module = ((_relative(path), ast.get_docstring(tree), private_module),)
    definitions = tuple(
        (
            f"{_relative(path)}:{node.name}",
            ast.get_docstring(node),
            private_module or node.name.startswith("_"),
        )
        for node in tree.body
        if isinstance(node, DEFINITION_NODES)
    )
    return module + definitions


def test_every_mission_module_class_and_public_function_has_the_four_part_docstring():
    problems = tuple(
        problem
        for path in sorted(MISSION_ROOT.rglob("*.py"))
        for location, docstring, private in _subjects(path)
        for problem in _docstring_problems(location, docstring, private)
    )
    assert not problems, "\n".join(problems)
