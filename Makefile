.DEFAULT_GOAL := help
SHELL := /bin/bash

# Ensure tools from the 'dev' dependency-group are available when
# running code-quality and test targets. Use uv sync --group to
# install only the needed groups quickly.
UV_SYNC_DEV ?= uv sync --group dev

.PHONY: help install fmt lint typecheck test jupyter docs latexpdf clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\t\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependency-groups
	uv sync --all-groups

fmt: ## Auto-format code with Ruff (ensure dev tools installed)
	$(UV_SYNC_DEV)
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

lint: ## Lint code with Ruff (ensure dev tools installed)
	$(UV_SYNC_DEV)
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

typecheck: ## Type-check with mypy (ensure dev tools installed)
	$(UV_SYNC_DEV)
	uv run mypy src/

test: ## Run tests with coverage (ensure dev tools installed)
	$(UV_SYNC_DEV)
	uv run pytest --cov --cov-report=term-missing

jupyter: ## Launch JupyterLab (will try to install notebooks group)
	uv sync --group notebooks || true
	uv run jupyter lab --notebook-dir=notebooks

docs: ## Build Sphinx docs (ensure docs group installed)
	$(MAKE) -C docs html

latexpdf: ## Build Sphinx PDF docs (ensure docs group installed)
	$(MAKE) -C docs latexpdf

clean: ## Remove build artifacts and caches
	rm -rf dist/ build/ *.egg-info .venv/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ .ty_cache/ htmlcov/
	rm -rf docs/_build/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
