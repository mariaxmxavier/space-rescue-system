"""Import and side-effect boundaries for the rescue architecture."""

import ast
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_PACKAGES = ("mission", "market", "mobilisation", "communication")
FORBIDDEN_OUTER_IMPORTS = (
    "rescue.application",
    "rescue.adapters",
    "rescue.bootstrap",
)
FORBIDDEN_IO_IMPORTS = {
    "os",
    "time",
    "socket",
    "urllib",
    "http",
    "requests",
    "httpx",
    "subprocess",
    "sqlite3",
    "sqlalchemy",
}
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


def _is_under(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(f"{prefix}.")


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_domain_capabilities_do_not_import_application_adapters_or_bootstrap(self):
        for package in DOMAIN_PACKAGES:
            for path in _python_files(package):
                tree = _parse(path)
                for node, module in _imports(tree):
                    for forbidden in FORBIDDEN_OUTER_IMPORTS:
                        with self.subTest(file=_relative(path), import_name=module):
                            self.assertFalse(
                                _is_under(module, forbidden),
                                f"{_relative(path)} imports outward to {module!r}",
                            )

    def test_domain_capabilities_do_not_read_environment_or_use_io_clocks_or_network(self):
        for package in DOMAIN_PACKAGES:
            for path in _python_files(package):
                tree = _parse(path)
                for node, module in _imports(tree):
                    imported_root = module.lstrip(".").split(".", 1)[0]
                    with self.subTest(file=_relative(path), import_name=module):
                        self.assertNotIn(
                            imported_root,
                            FORBIDDEN_IO_IMPORTS,
                            f"{_relative(path)} imports an I/O, environment, clock, or network module",
                        )
                    for forbidden in FORBIDDEN_OUTER_IMPORTS:
                        with self.subTest(file=_relative(path), import_name=module):
                            self.assertFalse(
                                _is_under(module, forbidden),
                                f"{_relative(path)} imports outward to {module!r}",
                            )

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
                names = (
                    [item.name for item in node.names]
                    if isinstance(node, ast.Import)
                    else [item.name for item in node.names]
                )
                with self.subTest(file=_relative(path), import_name=module):
                    self.assertFalse(
                        _is_under(module, "rescue.adapters.memory")
                        or "MemoryTransactionStore" in names,
                        f"{_relative(path)} imports the concrete memory adapter",
                    )

    def test_experiment_models_and_results_remain_pure(self):
        for relative in (
            Path("rescue/experiments/models.py"),
            Path("rescue/experiments/results.py"),
        ):
            path = REPOSITORY_ROOT / relative
            tree = _parse(path)
            for node, module in _imports(tree):
                imported_root = module.lstrip(".").split(".", 1)[0]
                with self.subTest(file=_relative(path), import_name=module):
                    self.assertNotIn(
                        imported_root,
                        FORBIDDEN_IO_IMPORTS,
                        f"{_relative(path)} imports an external I/O module",
                    )
                    for forbidden in FORBIDDEN_OUTER_IMPORTS:
                        self.assertFalse(
                            _is_under(module, forbidden),
                            f"{_relative(path)} imports outward to {module!r}",
                        )


if __name__ == "__main__":
    unittest.main()
