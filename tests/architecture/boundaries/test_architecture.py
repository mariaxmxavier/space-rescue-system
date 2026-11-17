"""Import and side-effect boundaries for the rescue architecture."""

import ast
import contextlib
import io
import logging
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from importlib.util import resolve_name
from pathlib import Path

from importlinter.cli import lint_imports

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@contextlib.contextmanager
def _logger_enablement_preserved():
    loggers = [
        logger
        for logger in logging.root.manager.loggerDict.values()
        if isinstance(logger, logging.Logger)
    ]
    states = [(logger, logger.disabled) for logger in loggers]
    try:
        yield
    finally:
        for logger, disabled in states:
            logger.disabled = disabled


DOMAIN_PACKAGES = ("mission", "market", "mobilisation", "communication")
ADAPTER_IMPORT_ROOTS = (
    "rescue.adapters",
    "rescue.values",
    "rescue.state",
    "rescue.experiments.models",
    "rescue.mobilisation.models",
)
APPLICATION_IMPORT_ROOTS = (
    "rescue.values",
    "rescue.state",
    "rescue.adapters.ports",
    "rescue.mission",
    "rescue.market",
    "rescue.mobilisation",
    "rescue.communication",
    "rescue.experiments.models",
    "rescue.experiments.results",
    "rescue.application",
)
FORBIDDEN_IO_CALLS = {
    "open",
    "read_text",
    "write_text",
    "read_bytes",
    "write_bytes",
    "urlopen",
    "create_connection",
    "create_engine",
    "connect",
    "getenv",
    "putenv",
    "getenvb",
    "putenvb",
    "time",
    "sleep",
    "monotonic",
    "perf_counter",
    "process_time",
    "utcnow",
}


def _python_files(package: str) -> tuple[Path, ...]:
    directory = REPOSITORY_ROOT / "rescue" / package
    return tuple(sorted(directory.rglob("*.py")))


def _relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _module_name(path: Path) -> str:
    if isinstance(path, ast.Import):
        return path.names[0].name
    if isinstance(path, ast.ImportFrom):
        return "." * path.level + (path.module or "")
    return ""


def _call_name(node: ast.expr) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=_relative(path))


def _imports(tree: ast.Module) -> tuple[tuple[ast.AST, str], ...]:
    found: list[tuple[ast.AST, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            found.append((node, _module_name(node)))
    return tuple(found)


def _forbidden_market_imports(source: str, package: str) -> tuple[str, ...]:
    """Check every import, including guarded imports, against the market allowlist."""
    modules = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = resolve_name("." * node.level + (node.module or ""), package)
            if module == "rescue":
                modules.extend(f"rescue.{alias.name}" for alias in node.names)
            else:
                modules.append(module)
    return tuple(
        module
        for module in modules
        if module != "rescue.values"
        and module != "rescue.market"
        and not module.startswith("rescue.market.")
        and module.split(".")[0] not in sys.stdlib_module_names
    )


def _absolute_modules(tree: ast.Module) -> tuple[str, ...]:
    """List every module a file imports, one entry per imported name.

    What: returns each ``import`` target and each ``from`` module; relative imports keep their dots.

    When: called by the adapter and application import checks.

    Why: a file with ``import a, b`` must have both names checked, not only the first.
    """
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append("." * node.level + (node.module or ""))
    return tuple(modules)


def _adapter_import_allowed(module: str) -> bool:
    """Decide whether the adapters layer may import ``module``.

    What: allows the standard library, ``rescue.adapters`` itself, ``rescue.values``,
    ``rescue.state`` and the experiments and mobilisation models; refuses relative imports and
    everything else. The old ``rescue.application.state`` exception is gone.

    When: called for every import in ``rescue/adapters/`` by the allowlist test.

    Why: an allowlist catches third-party and new outward imports that a denylist does not name.
    """
    if module.startswith("."):
        return False
    if module.split(".", 1)[0] in sys.stdlib_module_names:
        return True
    return any(module == root or module.startswith(f"{root}.") for root in ADAPTER_IMPORT_ROOTS)


def _application_import_allowed(module: str) -> bool:
    """Decide whether the application layer may import ``module``.

    What: allows the standard library and the inward roots in contracts/application-boundary.md;
    refuses relative imports, ``rescue.experiments.simulator`` and everything else.

    When: called for every import in ``rescue/application/`` by the allowlist test.

    Why: an allowlist catches third-party and new outward imports that a denylist does not name.
    """
    if module.startswith("."):
        return False
    if module.split(".", 1)[0] in sys.stdlib_module_names:
        return True
    return any(module == root or module.startswith(f"{root}.") for root in APPLICATION_IMPORT_ROOTS)


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_market_imports_only_itself_values_and_the_standard_library(self):
        for path in _python_files("market"):
            package = ".".join(path.parent.relative_to(REPOSITORY_ROOT).parts)
            with self.subTest(file=_relative(path)):
                self.assertEqual(
                    _forbidden_market_imports(path.read_text(encoding="utf-8"), package),
                    (),
                    f"{_relative(path)} imports a dependency outside the market allowlist",
                )

    def test_market_allowlist_covers_guarded_relative_and_multiple_imports(self):
        probes = [
            ("from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n import pytest", ("pytest",)),
            ("import decimal, rescue.future_capability", ("rescue.future_capability",)),
            ("from rescue import values, future_capability", ("rescue.future_capability",)),
            ("from ....mission.models import Mission", ("rescue.mission.models",)),
            ("from rescue import *", ("rescue.*",)),
            ("import rescue", ("rescue",)),
            ("from rescue.values import TimePoint", ()),
            ("from rescue import values", ()),
            ("import rescue.market.models", ()),
            ("from ..fleet import Ship", ()),
            ("from . import rules", ()),
            ("from decimal import Decimal\nimport math, sys", ()),
        ]
        for source, forbidden in probes:
            with self.subTest(source=source):
                self.assertEqual(
                    _forbidden_market_imports(source, "rescue.market.models.quotes"), forbidden
                )

    def test_market_contract_rejects_type_only_and_new_sibling_dependencies(self):
        probes = {
            "mission type reference": (
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from rescue.mission.models import Mission\n"
                "def inspect(mission: 'Mission') -> None: ...\n",
                "rescue.mission.models",
            ),
            "new sibling": ("import rescue.future_capability\n", "rescue.future_capability"),
        }
        for label, (source, dependency) in probes.items():
            with self.subTest(import_kind=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copytree(
                    REPOSITORY_ROOT / "rescue",
                    root / "rescue",
                    ignore=shutil.ignore_patterns("__pycache__"),
                )
                shutil.copyfile(REPOSITORY_ROOT / "pyproject.toml", root / "pyproject.toml")
                (root / "rescue" / "future_capability.py").write_text("", encoding="utf-8")
                (root / "rescue" / "market" / "boundary_probe.py").write_text(
                    source, encoding="utf-8"
                )
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        "from importlinter.cli import lint_imports; "
                        "raise SystemExit(lint_imports(config_filename='pyproject.toml', "
                        "no_cache=True, no_logo=True))",
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("market-standalone", result.stdout)
                self.assertIn("BROKEN", result.stdout)
                self.assertIn(dependency, result.stdout)

    def test_domain_capabilities_do_not_read_environment_or_use_io_clocks_or_network(self):
        for package in DOMAIN_PACKAGES:
            for path in _python_files(package):
                tree = _parse(path)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        called = _call_name(node.func)
                        leaf = called.rsplit(".", 1)[-1]
                        forbidden = leaf in FORBIDDEN_IO_CALLS or called in {
                            "datetime.now",
                            "datetime.utcnow",
                            "date.today",
                            "os.environ.get",
                            "os.getenv",
                            "os.putenv",
                            "socket.socket",
                            "socket.create_connection",
                        }
                        with self.subTest(file=_relative(path), call=called):
                            self.assertFalse(
                                forbidden,
                                f"{_relative(path)} calls forbidden I/O or reads the wall clock via {called!r}",
                            )

                    if isinstance(node, ast.Attribute):
                        chain = _call_name(node)
                        with self.subTest(file=_relative(path), attribute=chain):
                            self.assertNotIn(
                                chain,
                                {"os.environ", "os.environb"},
                                f"{_relative(path)} reads process environment directly",
                            )

    def test_application_experiments_and_demo_do_not_import_memory_adapter_modules(self):
        """Check that no application, experiments or demo module imports the memory adapters.

        What: lists every import in those files and fails if one names ``rescue.adapters.memory``.

        When: run by pytest on every ``make check-all``.

        Why: only the composition root may choose the in-memory implementations.
        """
        sources = (
            *_python_files("application"),
            *_python_files("experiments"),
            REPOSITORY_ROOT / "rescue" / "demo.py",
        )
        for path in sources:
            for module in _absolute_modules(_parse(path)):
                with self.subTest(file=_relative(path), import_name=module):
                    self.assertFalse(
                        module == "rescue.adapters.memory"
                        or module.startswith("rescue.adapters.memory."),
                        f"{_relative(path)} imports the memory adapter module {module!r}",
                    )

    def test_transport_api_is_not_imported_by_application_or_domain(self):
        """Keep HTTP transport at the outer boundary."""
        for package in (*DOMAIN_PACKAGES, "application", "state"):
            for path in _python_files(package):
                for module in _absolute_modules(_parse(path)):
                    with self.subTest(file=_relative(path), import_name=module):
                        self.assertFalse(
                            module == "rescue.api" or module.startswith("rescue.api."),
                            f"{_relative(path)} imports transport module {module!r}",
                        )

    def test_adapters_import_only_allowed_modules(self):
        """Check that every import in ``rescue/adapters`` is on the allowlist.

        What: lists every import in the adapters layer and fails on any module the allowlist refuses.

        When: run by pytest on every ``make check-all``.

        Why: the adapters layer may depend only on the standard library and the inward modules named
        in FR-005 and FR-010; anything else would reverse the dependency direction.
        """
        for path in _python_files("adapters"):
            for module in _absolute_modules(_parse(path)):
                with self.subTest(file=_relative(path), import_name=module):
                    self.assertTrue(
                        _adapter_import_allowed(module),
                        f"{_relative(path)} imports {module!r}, which the adapters layer may not import",
                    )

    def test_adapter_import_allowlist_rejects_outward_and_third_party_imports(self):
        """Check that the allowlist itself accepts and refuses the right module names.

        What: refuses ``requests``, ``rescue.bootstrap``, ``rescue.application.ports``,
        ``rescue.application.central``, ``rescue.application.state``, ``rescue.experiments.simulation`` and a
        relative import; accepts ``decimal``, ``threading``, ``rescue.values``, ``rescue.state``,
        ``rescue.experiments.models``, ``rescue.mobilisation.models`` and ``rescue.adapters.ports.clock``.

        When: run by pytest on every ``make check-all``.

        Why: the allowlist test is only trustworthy if the function it calls is proven to refuse
        the cases it must refuse.
        """
        for module in (
            "requests",
            "rescue.bootstrap",
            "rescue.application.ports",
            "rescue.application.central",
            "rescue.application.state",
            "rescue.experiments.simulation",
            ".ports",
        ):
            with self.subTest(import_name=module):
                self.assertFalse(_adapter_import_allowed(module))
        for module in (
            "decimal",
            "threading",
            "rescue.values",
            "rescue.state",
            "rescue.experiments.models",
            "rescue.mobilisation.models",
            "rescue.adapters.ports.clock",
        ):
            with self.subTest(import_name=module):
                self.assertTrue(_adapter_import_allowed(module))

    def test_application_imports_only_allowed_modules(self):
        """Check that every import in ``rescue/application`` is on the allowlist.

        What: lists every import node in the application layer, function bodies included, and fails
        on any module the allowlist refuses.

        When: run by pytest on every ``make check-all``.

        Why: the application layer may depend only on the standard library and the inward modules
        named in contracts/application-boundary.md; a function-local import must not slip past.
        """
        for path in _python_files("application"):
            for module in _absolute_modules(_parse(path)):
                with self.subTest(file=_relative(path), import_name=module):
                    self.assertTrue(
                        _application_import_allowed(module),
                        f"{_relative(path)} imports {module!r}, which the application layer may not import",
                    )

    def test_application_import_allowlist_rejects_outward_and_third_party_imports(self):
        """Check that the allowlist itself accepts and refuses the right module names.

        What: refuses ``requests``, ``rescue.bootstrap``, ``rescue.demo``, ``rescue.adapters.memory``,
        ``rescue.experiments.simulator``, ``rescue.experiments.simulation`` and a relative import;
        accepts ``decimal``, ``rescue.values``, ``rescue.state``, ``rescue.adapters.ports.clock``,
        ``rescue.experiments.models`` and ``rescue.application.shared``.

        When: run by pytest on every ``make check-all``.

        Why: the allowlist test is only trustworthy if the function it calls is proven to refuse
        the cases it must refuse.
        """
        for module in (
            "requests",
            "rescue.bootstrap",
            "rescue.demo",
            "rescue.adapters.memory",
            "rescue.experiments.simulator",
            "rescue.experiments.simulation",
            ".shared",
        ):
            with self.subTest(import_name=module):
                self.assertFalse(_application_import_allowed(module))
        for module in (
            "decimal",
            "rescue.values",
            "rescue.state",
            "rescue.adapters.ports.clock",
            "rescue.experiments.models",
            "rescue.application.shared",
        ):
            with self.subTest(import_name=module):
                self.assertTrue(_application_import_allowed(module))

    def test_declared_import_contracts_are_kept(self):
        output = io.StringIO()
        with _logger_enablement_preserved(), contextlib.redirect_stdout(output):
            exit_code = lint_imports(
                config_filename=str(REPOSITORY_ROOT / "pyproject.toml"),
                no_cache=True,
                no_logo=True,
            )
        self.assertEqual(exit_code, 0, output.getvalue())
        self.assertIn("Contracts: 16 kept, 0 broken.", output.getvalue())

    def test_declared_import_contracts_match_the_reviewed_table(self):
        with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as file:
            contracts = tomllib.load(file)["tool"]["importlinter"]["contracts"]
        domain_sources = {f"rescue.{package}" for package in DOMAIN_PACKAGES} | {
            "rescue.experiments.models",
            "rescue.experiments.timeline",
            "rescue.experiments.results",
        }
        io_sources = domain_sources | {"rescue.state"}
        io_modules = {
            "os",
            "time",
            "socket",
            "urllib",
            "http",
            "subprocess",
            "sqlite3",
            "requests",
            "httpx",
            "sqlalchemy",
        }
        expected = {
            "domain-outward": (
                domain_sources,
                {"rescue.application", "rescue.adapters", "rescue.bootstrap"},
                False,
            ),
            "domain-io": (io_sources, io_modules, False),
            "market-standalone": (
                {"rescue.market"},
                {"rescue.*"},
                False,
            ),
            "application-inward": (
                {"rescue.application"},
                {
                    "rescue.adapters.memory",
                    "rescue.bootstrap",
                    "rescue.demo",
                    "rescue.experiments.simulation",
                    "rescue.experiments.simulator",
                    "rescue.experiments.timeline",
                },
                False,
            ),
            "state-inward": (
                {"rescue.state"},
                {
                    "rescue.application",
                    "rescue.adapters",
                    "rescue.bootstrap",
                    "rescue.demo",
                    "rescue.experiments",
                    "rescue.mobilisation",
                },
                False,
            ),
            "mobilisation-peers-one-way": (
                {"rescue.mission", "rescue.market"},
                {"rescue.mobilisation"},
                False,
            ),
            "mission-isolated": (
                {"rescue.mission"},
                {
                    "rescue.market",
                    "rescue.mobilisation",
                    "rescue.communication",
                    "rescue.experiments",
                    "rescue.application",
                    "rescue.adapters",
                    "rescue.bootstrap",
                    "rescue.demo",
                },
                False,
            ),
            "communication-isolated": (
                {"rescue.communication"},
                {
                    "rescue.mission",
                    "rescue.market",
                    "rescue.mobilisation",
                    "rescue.experiments",
                    "rescue.application",
                    "rescue.adapters",
                    "rescue.bootstrap",
                    "rescue.demo",
                },
                False,
            ),
            "mobilisation-allowed-imports": (
                {"rescue.mobilisation"},
                {
                    "rescue.communication",
                    "rescue.experiments",
                    "rescue.application",
                    "rescue.adapters",
                    "rescue.bootstrap",
                    "rescue.demo",
                },
                False,
            ),
            "mobilisation-solver-isolated": (
                {"rescue.mobilisation.models", "rescue.mobilisation.services"},
                {"ortools"},
                True,
            ),
            "adapters-inward": (
                {"rescue.adapters"},
                {
                    "rescue.bootstrap",
                    "rescue.demo",
                    "rescue.application",
                    "rescue.experiments.results",
                    "rescue.experiments.simulation",
                    "rescue.experiments.timeline",
                    "rescue.mobilisation.algorithms",
                    "rescue.mobilisation.services",
                    "rescue.mission",
                    "rescue.market",
                    "rescue.communication",
                },
                True,
            ),
            "experiments-pure-core": (
                {
                    "rescue.experiments.models",
                    "rescue.experiments.timeline",
                    "rescue.experiments.results",
                },
                {"rescue.experiments.simulation"},
                False,
            ),
            "experiments-no-bootstrap": (
                {"rescue.experiments"},
                {"rescue.bootstrap", "rescue.demo", "rescue.application.central"},
                False,
            ),
        }
        expected_layers = {
            "mobilisation-layers": [
                "rescue.mobilisation.services",
                "rescue.mobilisation.algorithms",
                "rescue.mobilisation.models",
            ],
            "mission-layers": ["rescue.mission.rules", "rescue.mission.models"],
            "communication-layers": ["rescue.communication.rules", "rescue.communication.models"],
        }
        declared = {}
        declared_layers = {}
        for contract in contracts:
            contract_id = contract["name"].split(":", 1)[0]
            if contract_id == "market-standalone":
                self.assertEqual(
                    contract.get("ignore_imports"), ["rescue.market.** -> rescue.values"]
                )
            else:
                self.assertNotIn("ignore_imports", contract, contract_id)
            if contract["type"] == "layers":
                declared_layers[contract_id] = contract["layers"]
                continue
            self.assertEqual(contract["type"], "forbidden", contract_id)
            declared[contract_id] = (
                set(contract["source_modules"]),
                set(contract["forbidden_modules"]),
                contract.get("allow_indirect_imports", False),
            )
        self.assertEqual(declared, expected)
        self.assertEqual(declared_layers, expected_layers)


if __name__ == "__main__":
    unittest.main()
