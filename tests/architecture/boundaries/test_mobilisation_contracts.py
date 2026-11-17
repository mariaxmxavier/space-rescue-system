"""Seeded violations prove each mobilisation import contract fails when broken."""

import os
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Iterator
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MOBILISATION_CONTRACTS = (
    "mobilisation-peers-one-way",
    "mobilisation-allowed-imports",
    "mobilisation-layers",
    "mobilisation-solver-isolated",
)
PACKAGES = (
    "rescue",
    "rescue/mission",
    "rescue/market",
    "rescue/communication",
    "rescue/experiments",
    "rescue/application",
    "rescue/adapters",
    "rescue/mobilisation",
    "rescue/mobilisation/models",
    "rescue/mobilisation/algorithms",
    "rescue/mobilisation/services",
)
VIOLATIONS = {
    "mobilisation-peers-one-way": ("rescue/mission/leak.py", "import rescue.mobilisation\n"),
    "mobilisation-allowed-imports": (
        "rescue/mobilisation/leak.py",
        "import rescue.communication\n",
    ),
    "mobilisation-layers": (
        "rescue/mobilisation/models/leak.py",
        "import rescue.mobilisation.services\n",
    ),
    "mobilisation-solver-isolated": ("rescue/mobilisation/services/leak.py", "import ortools\n"),
}


def _contract_config() -> str:
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as file:
        contracts = tomllib.load(file)["tool"]["importlinter"]["contracts"]
    lines = ["[tool.importlinter]", 'root_package = "rescue"', "include_external_packages = true"]
    for contract in contracts:
        if contract["name"].split(":", 1)[0] not in MOBILISATION_CONTRACTS:
            continue
        lines += ["", "[[tool.importlinter.contracts]]", f'name = "{contract["name"]}"']
        lines.append(f'type = "{contract["type"]}"')
        for key in ("source_modules", "forbidden_modules", "layers"):
            if key in contract:
                lines.append(f"{key} = {contract[key]!r}".replace("'", '"'))
        if contract.get("allow_indirect_imports"):
            lines.append("allow_indirect_imports = true")
    return "\n".join(lines) + "\n"


def _seed(root: Path, violation: tuple[str, str] | None) -> None:
    for package in PACKAGES:
        (root / package).mkdir(parents=True, exist_ok=True)
        (root / package / "__init__.py").write_text("", encoding="utf-8")
    for module in ("bootstrap", "demo"):
        (root / "rescue" / f"{module}.py").write_text("", encoding="utf-8")
    (root / "pyproject.toml").write_text(_contract_config(), encoding="utf-8")
    if violation is not None:
        relative, source = violation
        (root / relative).write_text(source, encoding="utf-8")


def _run_lint_imports(root: Path) -> subprocess.CompletedProcess[str]:
    code = "import sys; from importlinter.cli import lint_imports_command as c; sys.exit(c())"
    return subprocess.run(
        [sys.executable, "-c", code, "--no-cache", "--no-logo"],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root)},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def tmp_path() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as directory:
        yield Path(directory)


@pytest.fixture
def clean_tree(tmp_path: Path) -> Path:
    _seed(tmp_path, None)
    return tmp_path


def test_the_unseeded_temporary_tree_keeps_every_mobilisation_contract(clean_tree: Path) -> None:
    result = _run_lint_imports(clean_tree)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Contracts: 4 kept, 0 broken." in result.stdout


@pytest.mark.parametrize("contract", MOBILISATION_CONTRACTS)
def test_seeded_violation_breaks_exactly_its_named_contract(contract: str, tmp_path: Path) -> None:
    _seed(tmp_path, VIOLATIONS[contract])

    result = _run_lint_imports(tmp_path)

    assert result.returncode != 0, result.stdout
    assert "Contracts: 3 kept, 1 broken." in result.stdout
    assert contract in result.stdout.split("BROKEN")[0].rsplit("KEPT", 1)[-1]
