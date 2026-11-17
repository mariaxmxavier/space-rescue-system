"""Mobilisation documentation conformance against the domain model diagrams."""

import ast
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DIAGRAMS = (
    REPOSITORY_ROOT / "docs/architecture/diagrams/rescue-domain-model/namespaces/Mobilisation"
)
PACKAGE = REPOSITORY_ROOT / "rescue/mobilisation"
MODELS = PACKAGE / "models"
TRANSIENT_MODULES = ("candidate.py", "decision_context.py")


def _classes_defined_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


def _diagram_classes() -> set[str]:
    uml = (DIAGRAMS / "class-diagram.mmd").read_text(encoding="utf-8")
    er = (DIAGRAMS / "entity-relationship-diagram.mmd").read_text(encoding="utf-8")
    from_uml = set(re.findall(r"^\s*class (\w+) \{", uml, re.MULTILINE))
    enumerations = set(re.findall(r"^\s*class (\w+) \{\s*<<enumeration>>", uml, re.MULTILINE))
    from_er = set(re.findall(r"^\s{4}(\w+) \{", er, re.MULTILINE))
    assert from_uml, "no classes parsed from class-diagram.mmd"
    assert from_uml - enumerations == from_er
    return from_uml


def test_each_diagram_entity_has_exactly_one_documented_model_module() -> None:
    """Guards the diagram-to-file mapping: a diagram class without its own module fails."""
    modules = [path for path in MODELS.glob("*.py") if path.name != "__init__.py"]
    for entity in sorted(_diagram_classes()):
        owners = [path for path in modules if entity in _classes_defined_in(path)]
        assert len(owners) == 1, f"{entity} defined in {[p.name for p in owners]}"
        docstring = ast.get_docstring(ast.parse(owners[0].read_text(encoding="utf-8")))
        assert docstring is not None
        assert entity in docstring or "namespaces/Mobilisation" in docstring


def test_every_module_class_and_public_function_has_a_docstring() -> None:
    """Guards FR-002: any undocumented module, class or public function fails."""
    missing: list[str] = []
    for path in PACKAGE.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        name = path.relative_to(REPOSITORY_ROOT).as_posix()
        if ast.get_docstring(tree) is None:
            missing.append(name)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                if not node.name.startswith("_") and ast.get_docstring(node) is None:
                    missing.append(f"{name}:{node.name}")
    assert not missing, missing


def test_transient_values_are_marked_transient() -> None:
    """Guards the transient marking of values that are not diagram classes."""
    for filename in TRANSIENT_MODULES:
        tree = ast.parse((MODELS / filename).read_text(encoding="utf-8"))
        docstring = ast.get_docstring(tree)
        assert docstring is not None
        assert "transient" in docstring.lower()
