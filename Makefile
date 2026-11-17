.PHONY: install format lint check-architecture test test-unit test-integration test-e2e test-architecture check-all

install:
	uv sync --locked

format:
	uv run ruff format rescue tests

lint:
	uv run ruff format --check rescue tests
	uv run ruff check rescue tests

check-architecture:
	uv run lint-imports

test:
	uv run pytest --cov=rescue --cov-report=term-missing
	for p in mission market mobilisation communication experiments application adapters; do echo "== rescue/$$p"; uv run coverage report --include="rescue/$$p/*"; done
	echo "== root modules"
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
