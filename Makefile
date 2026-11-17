export UV_LOCKED := 1

.PHONY: install format lint check-architecture test test-unit test-integration test-e2e test-architecture check-all compare compare-trace

install:
	uv sync --locked

format:
	uv run ruff format rescue tests benchmarks

lint:
	uv run ruff format --check rescue tests benchmarks
	uv run ruff check rescue tests benchmarks

check-architecture:
	uv run lint-imports

test:
	uv run pytest --cov=rescue --cov-report=term-missing
	@echo == rescue/mission
	uv run coverage report --include="rescue/mission/*" --fail-under=100
	@echo == rescue/market
	uv run coverage report --include="rescue/market/*"
	@echo == rescue/mobilisation
	uv run coverage report --include="rescue/mobilisation/*"
	@echo == rescue/communication
	uv run coverage report --include="rescue/communication/*" --fail-under=100
	@echo == rescue/experiments
	uv run coverage report --include="rescue/experiments/models/*,rescue/experiments/timeline/*,rescue/experiments/results/*" --fail-under=100
	@echo == rescue/experiments/simulation
	uv run coverage report --include="rescue/experiments/simulation/*" --fail-under=95
	@echo == rescue/application
	uv run coverage report --include="rescue/application/*"
	@echo == rescue/adapters
	uv run coverage report --include="rescue/adapters/*"
	@echo == root modules
	uv run coverage report --include="rescue/values.py,rescue/bootstrap.py,rescue/demo.py"

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

test-e2e:
	uv run pytest tests/e2e

test-architecture:
	uv run pytest tests/architecture

check-all: lint check-architecture test

compare:
	uv run python -m benchmarks.mobilisation.compare

compare-trace:
	uv run python -m benchmarks.mobilisation.compare --trace
