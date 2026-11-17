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
    "RescueScenario": {
        "baseline": "RunBaseline",
        "response_rules": "ScriptedResponse",
        "availability_changes": "ShipAvailability",
        "communication_profiles": "CommunicationProfile",
    },
    "RunBaseline": {"missions": "Mission", "market": "B3Market"},
    "RunSnapshot": {"run": "SimulationRun"},
    "SimulationRun": {"result": "SimulationResult"},
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


def _edge_drawn(text: str, owner: str, target: str) -> bool:
    """Tells whether the diagram draws a relation line that names both classes.

    What: looks for one line of the diagram text that mentions the owner and the target class.
    Why: a relation field that is left out of its box is only covered when the relation is drawn.
    """
    return any(
        re.search(rf"\b{owner}\b", line) and re.search(rf"\b{target}\b", line)
        for line in text.splitlines()
    )


def _matches(owner: str, shown: frozenset[str], code: frozenset[str], text: str) -> bool:
    """Tells whether a diagram box lists the code fields it must list.

    What: the box may not invent a field; every other code field must be listed in the box, or,
    when RELATION_SHOWN names it, drawn as a relation line between the owner and its target.
    Why: owned values are drawn as relations, so exact field equality would demand duplicate
    attributes, but a relation that is missing from the diagram must still fail.
    """
    relations = RELATION_SHOWN.get(owner, {})
    if not shown <= code:
        return False
    return all(
        field in shown or (field in relations and _edge_drawn(text, owner, relations[field]))
        for field in code
    )


def test_relation_field_may_be_left_out_of_the_box_only_when_its_edge_is_drawn():
    edge = 'RescueScenario ||..|| RunBaseline : "starts from"\n'
    assert _matches("RescueScenario", frozenset(), frozenset({"baseline"}), edge)
    assert not _matches(
        "RescueScenario", frozenset(), frozenset({"baseline"}), "RescueScenario {\n}\n"
    )
    assert _matches("RescueScenario", frozenset({"baseline"}), frozenset({"baseline"}), "")


def test_box_may_not_list_a_field_the_code_does_not_have():
    assert not _matches("RunSnapshot", frozenset({"extra"}), frozenset({"run"}), "RunSnapshot")


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
        for diagram_text in [diagram.read_text(encoding="utf-8")]
        for name, fields in _diagram_fields(diagram_text).items()
        if name in code and not _matches(name, fields, code[name], diagram_text)
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
