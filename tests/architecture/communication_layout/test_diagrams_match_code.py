"""Communication diagrams list the same fields as the communication dataclasses in code.

What: reads the Communication and scenario-model Mermaid diagrams and compares each drawn
communication class with the dataclass fields under rescue/communication.
When called: pytest collects it with the architecture suite and runs it on every test run.
Why: the diagrams are the reviewed domain model, so a field present in code but missing from a
class diagram, or an ER attribute that is not a persisted field, misleads readers (FR-009, FR-010).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

import ast
import re
from itertools import chain
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
COMMUNICATION_PACKAGE = REPOSITORY_ROOT / "rescue" / "communication"
DIAGRAM_ROOT = REPOSITORY_ROOT / "docs" / "architecture" / "diagrams" / "rescue-domain-model"
COMMUNICATION_CLASS_DIAGRAMS = (
    DIAGRAM_ROOT / "namespaces" / "Communication" / "class-diagram.mmd",
    DIAGRAM_ROOT / "class-diagrams" / "scenario-model.mmd",
)
COMMUNICATION_ER_DIAGRAMS = (
    DIAGRAM_ROOT / "namespaces" / "Communication" / "entity-relationship-diagram.mmd",
    DIAGRAM_ROOT / "entity-relationship-diagrams" / "scenario-model-er.mmd",
)
BLOCK = re.compile(
    r"^[ \t]*(?:class[ \t]+)?(\w+)[ \t]*\{[ \t]*\n(.*?)^[ \t]*\}[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
ER_ENTITY_TO_CLASS = {
    "COMMUNICATION_SESSION": "CommunicationSession",
    "DECISION_REPORT": "DecisionReport",
    "NOT_APPLIED": "NotApplied",
}


def _to_pascal(name: str) -> str:
    """Turns an ER entity name into its class name.

    What: maps known upper-snake entities through a table and passes other names unchanged.
    Why: ER entities are drawn in upper snake case while the code uses class names.
    """
    return ER_ENTITY_TO_CLASS.get(name, name)


def _is_dataclass(node: ast.ClassDef) -> bool:
    """Tells whether a class is declared with @dataclass.

    What: matches the decorator name, with or without arguments.
    Why: only dataclasses are the communication values the diagrams describe.
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
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and _is_dataclass(node)
    }


def _code_fields() -> dict[str, frozenset[str]]:
    """Maps each communication dataclass name to its field names.

    What: merges the dataclasses of every module under rescue/communication.
    Why: each dataclass is defined once, so the merge is a plain union keyed by name.
    """
    paths = sorted(COMMUNICATION_PACKAGE.rglob("*.py"))
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


def _blocks(path: Path, fields) -> dict[str, frozenset[str]]:
    """Maps each block name in one diagram file to its member names.

    What: reads every class or entity block with the given member reader.
    Why: one block grammar holds for all four communication diagrams.
    """
    text = path.read_text(encoding="utf-8")
    return {match.group(1): fields(match.group(2)) for match in BLOCK.finditer(text)}


def test_communication_diagrams_list_the_code_fields():
    """Drawn communication classes match code fields and drawn entities are persisted fields.

    What: for each class diagram, a drawn communication class must have exactly the code fields;
    for each ER diagram, a drawn entity's attributes must be a subset of the code fields.
    When called: pytest runs it with the architecture suite on every test run.
    Why: a field present in code but absent from a class diagram, or an ER attribute that code does
    not persist, misleads readers of the reviewed domain model (FR-009, FR-010).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    code = _code_fields()
    class_mismatches = [
        f"{diagram.relative_to(DIAGRAM_ROOT).as_posix()} {name}: "
        f"diagram {sorted(fields)} != code {sorted(code[name])}"
        for diagram in COMMUNICATION_CLASS_DIAGRAMS
        for name, fields in _blocks(diagram, _class_fields).items()
        if name in code and fields != code[name]
    ]
    er_mismatches = [
        f"{diagram.relative_to(DIAGRAM_ROOT).as_posix()} {name}: "
        f"attributes {sorted(fields - code[_to_pascal(name)])} are not persisted fields"
        for diagram in COMMUNICATION_ER_DIAGRAMS
        for name, fields in _blocks(diagram, _entity_fields).items()
        if _to_pascal(name) in code and not fields <= code[_to_pascal(name)]
    ]
    assert not class_mismatches and not er_mismatches, "\n".join(class_mismatches + er_mismatches)
