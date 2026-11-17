"""Import and side-effect boundaries for the rescue architecture."""

import ast
import contextlib
import io
import tomllib
import unittest
from pathlib import Path

from importlinter.cli import lint_imports

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_PACKAGES = ("mission", "market", "mobilisation", "communication")
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


class ArchitectureBoundaryTests(unittest.TestCase):
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

    def test_application_does_not_import_concrete_memory_adapter(self):
        for path in _python_files("application"):
            for node, module in _imports(_parse(path)):
                names = [item.name for item in node.names]
                with self.subTest(file=_relative(path), import_name=module):
                    self.assertNotIn(
                        "MemoryTransactionStore",
                        names,
                        f"{_relative(path)} imports the concrete memory adapter",
                    )

    def test_declared_import_contracts_are_kept(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = lint_imports(
                config_filename=str(REPOSITORY_ROOT / "pyproject.toml"),
                no_cache=True,
                no_logo=True,
            )
        self.assertEqual(exit_code, 0, output.getvalue())
        self.assertIn("Contracts: 3 kept, 0 broken.", output.getvalue())

    def test_declared_import_contracts_match_the_reviewed_table(self):
        with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as file:
            contracts = tomllib.load(file)["tool"]["importlinter"]["contracts"]
        domain_sources = {f"rescue.{package}" for package in DOMAIN_PACKAGES} | {
            "rescue.experiments.models",
            "rescue.experiments.results",
        }
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
            "domain-io": (domain_sources, io_modules, False),
            "application-no-memory": ({"rescue.application"}, {"rescue.adapters.memory"}, True),
        }
        declared = {}
        for contract in contracts:
            contract_id = contract["name"].split(":", 1)[0]
            self.assertNotIn("ignore_imports", contract, contract_id)
            self.assertEqual(contract["type"], "forbidden", contract_id)
            declared[contract_id] = (
                set(contract["source_modules"]),
                set(contract["forbidden_modules"]),
                contract.get("allow_indirect_imports", False),
            )
        self.assertEqual(declared, expected)


if __name__ == "__main__":
    unittest.main()
