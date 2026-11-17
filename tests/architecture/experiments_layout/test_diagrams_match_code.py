"""Experiments diagrams list the same field names as the experiments dataclasses in code.

What: reads the four Mermaid diagrams that show experiments classes and compares each class's field
names with the dataclass field names under rescue/experiments/models.
When called: pytest collects it with the architecture suite and runs it on every test run.
Why: the diagrams are the reviewed domain model, so a field present in code but missing from a
diagram, or the reverse, misleads readers.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

import ast
import re
from itertools import chain
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODELS_PACKAGE = REPOSITORY_ROOT / "rescue" / "experiments" / "models"
MODEL_PACKAGES = (MODELS_PACKAGE / "scenario", MODELS_PACKAGE / "run")
DIAGRAM_ROOT = REPOSITORY_ROOT / "docs" / "architecture" / "diagrams" / "rescue-domain-model"
NAMESPACE_DIAGRAMS = (
    DIAGRAM_ROOT / "namespaces" / "Experiments" / "class-diagram.mmd",
    DIAGRAM_ROOT / "namespaces" / "Experiments" / "entity-relationship-diagram.mmd",
)
EXPERIMENTS_DIAGRAMS = (
    *NAMESPACE_DIAGRAMS,
    DIAGRAM_ROOT / "class-diagrams" / "scenario-model.mmd",
    DIAGRAM_ROOT / "entity-relationship-diagrams" / "scenario-model-er.mmd",
)
REQUIRED_IN_NAMESPACE = frozenset(
    {
        "RunBaseline",
        "ScriptedResponse",
        "RunSnapshot",
        "RescueScenario",
        "CommunicationProfile",
        "SimulationRun",
        "SimulationResult",
    }
)
RELATION_SHOWN = {
    "RescueScenario": frozenset(
        {"baseline", "response_rules", "availability_changes", "communication_profiles"}
    ),
    "RunBaseline": frozenset({"missions", "market"}),
    "RunSnapshot": frozenset({"run"}),
    "SimulationRun": frozenset({"result"}),
}
BLOCK = re.compile(
    r"^[ \t]*(?:class[ \t]+)?(\w+)[ \t]*\{[ \t]*\n(.*?)^[ \t]*\}[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
ENTITY_DIAGRAM = re.compile(r"^erDiagram[ \t]*$", re.MULTILINE)


def _is_dataclass(node: ast.ClassDef) -> bool:
    """Tells whether a class is declared with @dataclass.

    What: matches the decorator name, with or without arguments.
    Why: only dataclasses are the experiments values the diagrams describe.
    """
    return any(
        ast.unparse(decorator).partition("(")[0] == "dataclass" for decorator in node.decorator_list
    )


def _dataclass_fields(path: Path) -> dict[str, frozenset[str]]:
    """Maps each dataclass in one module to its field names.

    What: collects annotated class-body targets of every dataclass.
    Why: the code is the reference the diagrams must match.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name: frozenset(
            statement.target.id
            for statement in node.body
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
        )
        for node in tree.body
        if isinstance(node, ast.ClassDef) and _is_dataclass(node)
    }


def _code_fields() -> dict[str, frozenset[str]]:
    """Maps each experiments model dataclass name to its field names.

    What: merges the dataclasses of every module under the scenario and run model packages.
    Why: each model dataclass is defined once there, so the merge is a plain union keyed by name.
    """
    paths = sorted(chain.from_iterable(package.rglob("*.py") for package in MODEL_PACKAGES))
    return dict(chain.from_iterable(_dataclass_fields(path).items() for path in paths))


def _member_lines(body: str) -> tuple[str, ...]:
    """Returns the non-empty member lines of one diagram block.

    What: strips each line and drops blanks and Mermaid %% comments.
    Why: only real members name fields; comments and spacing do not.
    """
    stripped = (line.strip() for line in body.splitlines())
    return tuple(line for line in stripped if line and not line.startswith("%%"))


def _class_fields(body: str) -> frozenset[str]:
    """Reads attribute names from a classDiagram block.

    What: takes the last word of each member line that has no parenthesis.
    Why: a member with a parenthesis is a method, which is not a dataclass field.
    """
    return frozenset(
        line.lstrip("+-#~").split()[-1] for line in _member_lines(body) if "(" not in line
    )


def _entity_fields(body: str) -> frozenset[str]:
    """Reads attribute names from an erDiagram block.

    What: takes the second word of each attribute line, after its type.
    Why: an entity attribute is written as type then name, with optional key markers after.
    """
    return frozenset(line.split()[1] for line in _member_lines(body))


def _diagram_fields(text: str) -> dict[str, frozenset[str]]:
    """Maps each diagram block name to its field names.

    What: picks the class or entity member reader from the diagram kind, then reads every block.
    Why: the same block grammar holds for every experiments diagram, so one parser covers all four.
    """
    fields = _entity_fields if ENTITY_DIAGRAM.search(text) else _class_fields
    return {match.group(1): fields(match.group(2)) for match in BLOCK.finditer(text)}


def _shown(diagram: Path) -> dict[str, frozenset[str]]:
    """Reads one diagram file into its block fields.

    What: reads the file as UTF-8 and parses its blocks.
    Why: both tests parse the same diagrams the same way.
    """
    return _diagram_fields(diagram.read_text(encoding="utf-8"))


def _matches(shown: frozenset[str], code: frozenset[str], relation: frozenset[str]) -> bool:
    """Tells whether a diagram box lists the code fields it must list.

    What: the box may not invent a field, and must list every code field except those drawn as a
    relation edge, which may appear in the box or not.
    Why: the diagrams draw owned values as edges, so an exact field equality would demand
    duplicate attributes that the reviewed diagrams deliberately leave out.
    """
    return shown <= code and code - relation <= shown


def test_experiments_classes_in_diagrams_list_the_code_fields():
    """Each experiments class in the four diagrams lists the dataclass fields it must list.

    What: for every shown class that is an experiments model dataclass, checks its diagram box
    against its code fields, allowing the fields RELATION_SHOWN names to appear only as relations.
    When called: pytest runs it with the architecture suite on every test run.
    Why: a field missing from a box, or a field the code does not have, misleads readers of the
    reviewed domain model.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """
    code = _code_fields()
    mismatches = [
        f"{diagram.relative_to(DIAGRAM_ROOT).as_posix()} {name}: "
        f"diagram {sorted(fields)} does not match code {sorted(code[name])}"
        for diagram in EXPERIMENTS_DIAGRAMS
        for name, fields in _shown(diagram).items()
        if name in code and not _matches(fields, code[name], RELATION_SHOWN.get(name, frozenset()))
    ]
    assert not mismatches, "\n".join(mismatches)


def test_namespace_diagrams_show_every_experiments_model_class():
    """Both Experiments namespace diagrams show the seven scenario and run model classes.

    What: checks that each namespace diagram has a block for every required class.
    When called: pytest runs it with the architecture suite on every test run.
    Why: a dropped class hides a whole part of the experiments model from readers.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """
    missing = [
        f"{diagram.relative_to(DIAGRAM_ROOT).as_posix()}: missing "
        f"{sorted(REQUIRED_IN_NAMESPACE - _shown(diagram).keys())}"
        for diagram in NAMESPACE_DIAGRAMS
        if not REQUIRED_IN_NAMESPACE <= _shown(diagram).keys()
    ]
    assert not missing, "\n".join(missing)
