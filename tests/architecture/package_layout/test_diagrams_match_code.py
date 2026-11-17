"""Diagrams list the same names as the code they draw.

What: reads the eight mission Mermaid diagrams and compares each mission class's field names with
the dataclass field names under rescue/mission, then checks the Application class and entity
relationship diagrams against rescue/application and rescue/state.
When called: pytest collects it with the architecture suite and runs it on every test run.
Why: the diagrams are the reviewed domain model, so a field present in code but missing from a
diagram, or the reverse, misleads readers (FR-004).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

import ast
import re
from itertools import chain
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MISSION_PACKAGE = REPOSITORY_ROOT / "rescue" / "mission"
APPLICATION_PACKAGE = REPOSITORY_ROOT / "rescue" / "application"
RUN_STATE_MODULE = REPOSITORY_ROOT / "rescue" / "state" / "run_state.py"
DIAGRAM_ROOT = REPOSITORY_ROOT / "docs" / "architecture" / "diagrams" / "rescue-domain-model"
MISSION_DIAGRAMS = (
    DIAGRAM_ROOT / "namespaces" / "MissionOperations" / "class-diagram.mmd",
    DIAGRAM_ROOT / "namespaces" / "MissionOperations" / "entity-relationship-diagram.mmd",
    DIAGRAM_ROOT / "namespaces" / "CoreReferences" / "class-diagram.mmd",
    DIAGRAM_ROOT / "namespaces" / "CoreReferences" / "entity-relationship-diagram.mmd",
    DIAGRAM_ROOT / "class-diagrams" / "domain-model.mmd",
    DIAGRAM_ROOT / "class-diagrams" / "scenario-model.mmd",
    DIAGRAM_ROOT / "entity-relationship-diagrams" / "domain-model-er.mmd",
    DIAGRAM_ROOT / "entity-relationship-diagrams" / "scenario-model-er.mmd",
)
BLOCK = re.compile(
    r"^[ \t]*(?:class[ \t]+)?(\w+)[ \t]*\{[ \t]*\n(.*?)^[ \t]*\}[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
APPLICATION_DIAGRAMS = DIAGRAM_ROOT / "namespaces" / "Application"
DRAWN_CLASS = re.compile(r"^[ 	]*class[ 	]+(\w+)", re.MULTILINE)
ENTITY_DIAGRAM = re.compile(r"^erDiagram[ \t]*$", re.MULTILINE)
OWNED_COLLECTIONS = {"Mission": frozenset({"requests", "history"})}
SHOWN_MISSION_CLASSES = {
    "namespaces/MissionOperations/class-diagram.mmd": frozenset(
        {
            "Mission",
            "MissionData",
            "MissionProgress",
            "RequestHistoryEntry",
            "RequestTiming",
            "SeatRequest",
        }
    ),
    "namespaces/MissionOperations/entity-relationship-diagram.mmd": frozenset(
        {"Mission", "MissionProgress", "RequestHistoryEntry", "SeatRequest"}
    ),
    "namespaces/CoreReferences/class-diagram.mmd": frozenset(
        {"Mission", "MissionData", "RequestHistoryEntry", "RequestTiming", "SeatRequest"}
    ),
    "namespaces/CoreReferences/entity-relationship-diagram.mmd": frozenset(
        {"Mission", "MissionData", "RequestHistoryEntry", "RequestTiming", "SeatRequest"}
    ),
    "class-diagrams/domain-model.mmd": frozenset(
        {
            "Mission",
            "MissionData",
            "MissionProgress",
            "RequestHistoryEntry",
            "RequestTiming",
            "SeatRequest",
        }
    ),
    "class-diagrams/scenario-model.mmd": frozenset(
        {"Mission", "MissionData", "RequestHistoryEntry", "RequestTiming", "SeatRequest"}
    ),
    "entity-relationship-diagrams/domain-model-er.mmd": frozenset(
        {
            "Mission",
            "MissionData",
            "MissionProgress",
            "RequestHistoryEntry",
            "RequestTiming",
            "SeatRequest",
        }
    ),
    "entity-relationship-diagrams/scenario-model-er.mmd": frozenset(
        {"Mission", "MissionData", "RequestHistoryEntry", "RequestTiming", "SeatRequest"}
    ),
}


def _is_dataclass(node: ast.ClassDef) -> bool:
    """Tells whether a class is declared with @dataclass.

    What: matches the decorator name, with or without arguments.
    Why: only dataclasses are the mission values the diagrams describe.
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
    """Maps each mission dataclass name to its field names.

    What: merges the dataclasses of every module under rescue/mission.
    Why: each mission dataclass is defined once, so the merge is a plain union keyed by name.
    """
    paths = sorted(MISSION_PACKAGE.rglob("*.py"))
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
    Why: the same block grammar holds for every mission diagram, so one parser covers all eight.
    """
    fields = _entity_fields if ENTITY_DIAGRAM.search(text) else _class_fields
    return {match.group(1): fields(match.group(2)) for match in BLOCK.finditer(text)}


def test_mission_classes_in_diagrams_list_the_code_fields():
    """Each mission class in the domain diagrams has exactly the dataclass fields in code.

    What: for each diagram, checks that it shows exactly its pinned mission classes, and that every
    shown mission class has exactly the code's field names (owned collections excluded).
    When called: pytest runs it with the architecture suite on every test run.
    Why: a field present in code but absent from a diagram, or the reverse, misleads readers of
    the reviewed domain model, and a dropped class hides a whole part of it (FR-004).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    code = {
        name: fields - OWNED_COLLECTIONS.get(name, frozenset())
        for name, fields in _code_fields().items()
    }
    shown_by_diagram = {
        diagram.relative_to(DIAGRAM_ROOT).as_posix(): _diagram_fields(
            diagram.read_text(encoding="utf-8")
        )
        for diagram in MISSION_DIAGRAMS
    }
    class_mismatches = [
        f"{key}: shows {sorted(name for name in shown if name in code)}, "
        f"expected {sorted(SHOWN_MISSION_CLASSES[key])}"
        for key, shown in shown_by_diagram.items()
        if {name for name in shown if name in code} != SHOWN_MISSION_CLASSES[key]
    ]
    field_mismatches = [
        f"{key} {name}: diagram {sorted(fields)} != code {sorted(code[name])}"
        for key, shown in shown_by_diagram.items()
        for name, fields in shown.items()
        if name in code and fields != code[name]
    ]
    assert not class_mismatches and not field_mismatches, "\n".join(
        class_mismatches + field_mismatches
    )


def _parse(path: Path) -> ast.Module:
    """Parses one Python module.

    What: reads the file as UTF-8 and returns its syntax tree.
    Why: names are derived from code structure, never typed by hand.
    """
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _contract_names() -> frozenset[str]:
    """Collects every class defined under rescue/application/contracts.

    What: walks the syntax tree of each contracts module for class definitions.
    Why: a new command, enum or result type must be drawn in the Application class diagram.
    """
    return frozenset(
        node.name
        for path in (APPLICATION_PACKAGE / "contracts").rglob("*.py")
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.ClassDef)
    )


def _service_names() -> frozenset[str]:
    """Collects every public service function under rescue/application/services.

    What: takes the public top-level function names of each services module.
    Why: services are drawn by their function name, so a new service must be drawn.
    """
    return frozenset(
        node.name
        for path in (APPLICATION_PACKAGE / "services").rglob("*.py")
        for node in _parse(path).body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    )


def _facade_methods() -> frozenset[str]:
    """Collects the public method names of RescueCentral.

    What: reads the RescueCentral class body in rescue/application/central.py.
    Why: the facade is drawn with one member per public method.
    """
    facade = next(
        node
        for node in _parse(APPLICATION_PACKAGE / "central.py").body
        if isinstance(node, ast.ClassDef) and node.name == "RescueCentral"
    )
    return frozenset(
        node.name
        for node in facade.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    )


def test_application_class_diagram_draws_contracts_services_and_facade_methods():
    """The Application class diagram draws every contract, service and facade method in code.

    What: derives class names under contracts, service function names and RescueCentral methods
    with ast, and checks each is drawn as a class or as a RescueCentral member.
    When called: pytest runs it with the architecture suite on every test run.
    Why: a command or service missing from the diagram hides part of the application layer (FR-004).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    text = (APPLICATION_DIAGRAMS / "class-diagram.mmd").read_text(encoding="utf-8")
    drawn_classes = frozenset(DRAWN_CLASS.findall(text))
    facade_block = next(
        match.group(2) for match in BLOCK.finditer(text) if match.group(1) == "RescueCentral"
    )
    drawn_methods = frozenset(
        line.lstrip("+-#~").partition("(")[0] for line in _member_lines(facade_block) if "(" in line
    )
    missing = (
        sorted(f"class {name}" for name in (_contract_names() | _service_names()) - drawn_classes)
        + sorted(f"facade method {name}" for name in _facade_methods() - drawn_methods)
        + sorted(f"facade member {name}" for name in drawn_methods - _facade_methods())
    )
    assert not missing, "not drawn or not in code: " + ", ".join(missing)


def test_run_state_entity_lists_the_run_state_fields():
    """The RunState entity in the Application ER diagram has exactly the dataclass fields in code.

    What: compares the RunState dataclass field names with the attributes of its erDiagram block.
    When called: pytest runs it with the architecture suite on every test run.
    Why: the published run state is documented by this entity, so a missing field misleads readers
    (FR-004).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/entity-relationship-diagram.mmd
    """
    text = (APPLICATION_DIAGRAMS / "entity-relationship-diagram.mmd").read_text(encoding="utf-8")
    drawn = _diagram_fields(text)["RunState"]
    assert drawn == _dataclass_fields(RUN_STATE_MODULE)["RunState"]
