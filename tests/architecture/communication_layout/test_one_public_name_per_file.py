"""One public class or rule per communication module, and the public import tables.

What: checks the file layout of rescue/communication and the __all__ lists of its two public packages.
When called: collected by pytest in tests/architecture, so it runs in make check-all.
Why: one public name per file keeps each concept findable by its path, and the export lists keep
  callers' import paths stable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  and docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
COMMUNICATION_ROOT = REPOSITORY_ROOT / "rescue" / "communication"
PUBLIC_PACKAGE_EXPORTS = {
    "rescue.communication.models": frozenset(
        {
            "CommunicationMessage",
            "MessageDelivery",
            "DeliveryDisposition",
            "DeliveryReason",
            "FlowDirection",
            "RecoveryRejection",
            "DeliveryFacts",
            "DeliveryDecision",
            "SessionEnvelope",
            "CommunicationSession",
            "NotApplied",
            "DecisionReport",
            "RecoveryRequest",
            "SequenceControl",
            "ReportCursor",
        }
    ),
    "rescue.communication.rules": frozenset(
        {
            "classify_delivery",
            "accept_inbound",
            "issue_report",
            "recover_reports",
            "synchronise_inbound",
            "receive_report",
        }
    ),
}


def _public_modules() -> tuple[Path, ...]:
    """What: every .py file under rescue/communication whose name does not start with an underscore.
    Why: private modules and package __init__ files are internal surfaces, so they are exempt.
    """
    return tuple(
        path for path in sorted(COMMUNICATION_ROOT.rglob("*.py")) if not path.name.startswith("_")
    )


def _public_names(path: Path) -> tuple[str, ...]:
    """What: names of the top-level classes and functions in a module that are not underscored.
    Why: only top-level names are importable from the file, so nested and private ones do not count.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )


def test_each_public_communication_module_defines_exactly_one_public_name() -> None:
    """Every public communication module defines exactly one top-level public class or function.

    What: parses each public module under rescue/communication and counts its public top-level
      names, failing if no public module is found at all.
    When called: pytest runs it in the architecture suite, part of make check-all.
    Why: a module with two public names mixes two concepts, and a module with none cannot be
      imported by name.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      and docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    modules = _public_modules()
    assert modules, "no public communication modules found under rescue/communication"
    for path in modules:
        names = _public_names(path)
        assert len(names) == 1, f"{path.relative_to(REPOSITORY_ROOT).as_posix()} defines {names}"


@pytest.mark.parametrize("package", PUBLIC_PACKAGE_EXPORTS)
def test_public_package_all_lists_exactly_the_contract_names(package: str) -> None:
    """Each public package exports exactly the names in the public import contract.

    What: imports the package and compares its __all__ with the contract table.
    When called: pytest runs it in the architecture suite, part of make check-all.
    Why: application, experiments and demo import these names, so a missing or extra export is a
      contract change that must be made deliberately.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      and docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    module = importlib.import_module(package)
    assert set(module.__all__) == PUBLIC_PACKAGE_EXPORTS[package]
