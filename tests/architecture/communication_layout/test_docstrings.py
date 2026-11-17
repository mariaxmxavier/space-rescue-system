"""Communication modules, classes, functions and methods carry the labelled docstring.

What: Walks every file under rescue/communication and checks each module, class, public function
and public method for What:, When called:, Why: and Diagram:, and each private helper for What:
and Why:, and that every Diagram: path exists.
When called: Runs in the architecture test suite on every make test.
Why: Keeps the Communication code explained in one fixed shape so a reader finds the purpose,
the trigger and the diagram without opening the callers.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

import ast
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
COMMUNICATION_ROOT = REPOSITORY_ROOT / "rescue" / "communication"
PUBLIC_LABELS = ("What:", "When called:", "Why:", "Diagram:")
PRIVATE_LABELS = ("What:", "Why:")
FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


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


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _definitions(
    nodes: list[ast.stmt], prefix: str, inherited_private: bool
) -> tuple[tuple[str, str | None, bool], ...]:
    found: tuple[tuple[str, str | None, bool], ...] = ()
    for node in nodes:
        if not isinstance(node, (ast.ClassDef, *FUNCTION_NODES)) or _is_dunder(node.name):
            continue
        private = inherited_private or node.name.startswith("_")
        location = f"{prefix}:{node.name}"
        found += ((location, ast.get_docstring(node), private),)
        if isinstance(node, ast.ClassDef):
            found += _definitions(node.body, location, private)
    return found


def _subjects(path: Path) -> tuple[tuple[str, str | None, bool], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=_relative(path))
    private_module = _is_private_module(path)
    module = ((_relative(path), ast.get_docstring(tree), private_module),)
    return module + _definitions(tree.body, _relative(path), private_module)


def test_every_communication_module_class_and_callable_has_the_labelled_docstring():
    problems = tuple(
        problem
        for path in sorted(COMMUNICATION_ROOT.rglob("*.py"))
        for location, docstring, private in _subjects(path)
        for problem in _docstring_problems(location, docstring, private)
    )
    assert not problems, "\n".join(problems)
