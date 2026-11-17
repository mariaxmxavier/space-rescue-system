"""One public class or rule per mission module, and the public import tables.

What: checks the file layout of rescue/mission and the __all__ lists of its two public packages.
When called: collected by pytest in tests/architecture, so it runs in make check-all.
Why: one public name per file keeps each concept findable by its path, and the export lists keep
  callers' import paths stable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MISSION_ROOT = REPOSITORY_ROOT / "rescue" / "mission"
PUBLIC_PACKAGE_EXPORTS = {
    "rescue.mission.models": frozenset(
        {
            "Mission",
            "MissionData",
            "SeatRequest",
            "RequestHistoryEntry",
            "MissionProgress",
            "RequestTiming",
            "RequestOutcome",
            "ProgressStatus",
            "HistoryAction",
        }
    ),
    "rescue.mission.rules": frozenset(
        {"register", "add_request", "apply_outcome", "progress", "timing"}
    ),
}


def _public_modules() -> tuple[Path, ...]:
    """What: every .py file under rescue/mission whose name does not start with an underscore.
    Why: private modules and package __init__ files are internal surfaces, so they are exempt.
    """
    return tuple(
        path for path in sorted(MISSION_ROOT.rglob("*.py")) if not path.name.startswith("_")
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


def test_each_public_mission_module_defines_exactly_one_public_name() -> None:
    """Every public mission module defines exactly one top-level public class or function.

    What: parses each public module under rescue/mission and counts its public top-level names,
      failing if no public module is found at all.
    When called: pytest runs it in the architecture suite, part of make check-all.
    Why: a module with two public names mixes two concepts, and a module with none cannot be
      imported by name.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    modules = _public_modules()
    assert modules, "no public mission modules found under rescue/mission"
    for path in modules:
        names = _public_names(path)
        assert len(names) == 1, f"{path.relative_to(REPOSITORY_ROOT).as_posix()} defines {names}"


@pytest.mark.parametrize("package", PUBLIC_PACKAGE_EXPORTS)
def test_public_package_all_lists_exactly_the_contract_names(package: str) -> None:
    """Each public package exports exactly the names in the public import contract.

    What: imports the package and compares its __all__ with the contract table.
    When called: pytest runs it in the architecture suite, part of make check-all.
    Why: application, experiments, market, mobilisation and demo import these names, so a missing
      or extra export is a contract change that must be made deliberately.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    module = importlib.import_module(package)
    assert set(module.__all__) == PUBLIC_PACKAGE_EXPORTS[package]
