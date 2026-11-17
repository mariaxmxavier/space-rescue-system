"""One public class or rule per experiments module, and the public import tables.

What: checks the file layout of rescue/experiments, the __all__ lists of its four public packages,
  the absence of _legacy modules and the length of the simulation functions.
When called: collected by pytest in tests/architecture, so it runs in make check-all.
Why: one public name per file keeps each concept findable by its path, and the export lists keep
  callers' import paths stable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS_ROOT = REPOSITORY_ROOT / "rescue" / "experiments"
SIMULATION_ROOT = EXPERIMENTS_ROOT / "simulation"
MAX_FUNCTION_LINES = 60
PUBLIC_PACKAGE_EXPORTS = {
    "rescue.experiments.models": frozenset(
        {
            "CommunicationProfile",
            "RescueScenario",
            "RunBaseline",
            "RunSnapshot",
            "ScriptedResponse",
            "SimulationResult",
            "SimulationRun",
        }
    ),
    "rescue.experiments.timeline": frozenset({"Timeline", "TimelineEvent"}),
    "rescue.experiments.results": frozenset({"summarize"}),
    "rescue.experiments.simulation": frozenset(
        {"simulate", "StartRun", "RunHandle", "SimulationCentral"}
    ),
}


def _public_modules() -> tuple[Path, ...]:
    """What: every .py file under rescue/experiments whose name does not start with an underscore.
    Why: private modules and package __init__ files are internal surfaces, so they are exempt.
    """
    return tuple(
        path for path in sorted(EXPERIMENTS_ROOT.rglob("*.py")) if not path.name.startswith("_")
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


class TestExperimentsLayout:
    """The experiments layout rules, checked on every test run.

    What: groups the structural checks of rescue/experiments: one public name per file, the
      export tables, the function length limit and the absence of legacy modules.
    When called: pytest runs it in the architecture suite, part of make check-all.
    Why: each rule is a structural invariant that must hold on every change.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """

    def test_each_public_experiments_module_defines_exactly_one_public_name(self) -> None:
        """Every public experiments module defines exactly one top-level public class or function.

        What: parses each public module under rescue/experiments and counts its public top-level
          names, failing if no public module is found at all.
        When called: pytest runs it in the architecture suite, part of make check-all.
        Why: a module with two public names mixes two concepts, and a module with none cannot be
          imported by name.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
        """
        modules = _public_modules()
        assert modules, "no public experiments modules found under rescue/experiments"
        for path in modules:
            names = _public_names(path)
            assert len(names) == 1, (
                f"{path.relative_to(REPOSITORY_ROOT).as_posix()} defines {names}"
            )

    @pytest.mark.parametrize("package", PUBLIC_PACKAGE_EXPORTS)
    def test_public_package_all_lists_exactly_the_contract_names(self, package: str) -> None:
        """Each public package exports exactly the names in the public import contract.

        What: imports the package and compares its __all__ with the contract table.
        When called: pytest runs it in the architecture suite, part of make check-all.
        Why: application, demo and the tests import these names, so a missing or extra export is a
          contract change that must be made deliberately.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
        """
        module = importlib.import_module(package)
        assert set(module.__all__) == PUBLIC_PACKAGE_EXPORTS[package]

    def test_no_simulation_function_exceeds_the_line_limit(self) -> None:
        """No function under rescue/experiments/simulation is longer than 60 lines.

        What: parses every module under the simulation package and measures each function from its
          first to its last line.
        When called: pytest runs it in the architecture suite, part of make check-all.
        Why: short functions keep the simulation steps readable and separately testable.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
        """
        too_long = []
        for path in sorted(SIMULATION_ROOT.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = node.end_lineno - node.lineno + 1
                    if length > MAX_FUNCTION_LINES:
                        too_long.append(f"{path.name}:{node.name} has {length} lines")
        assert not too_long, too_long

    def test_no_legacy_modules_remain(self) -> None:
        """No _legacy.py file is left under rescue/experiments.

        What: lists every file named _legacy.py under rescue/experiments.
        When called: pytest runs it in the architecture suite, part of make check-all.
        Why: the legacy modules hide public classes behind a private name, so the layout is not
          finished while any of them exists.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
        """
        legacy = [
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in sorted(EXPERIMENTS_ROOT.rglob("_legacy.py"))
        ]
        assert not legacy, legacy
