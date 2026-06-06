.DEFAULT_GOAL := help
SHELL := /bin/bash

# Default only if user does not override
SOURCE ?= tests/fixtures/ieee.csl
TARGET ?= $(APPDATA)/Microsoft/Bibliography/Style

# Normalize paths on Windows
ifeq ($(OS),Windows_NT)
SOURCE_POSIX := $(shell cygpath -u "$(SOURCE)")
TARGET_POSIX := $(shell cygpath -u "$(TARGET)")
else
SOURCE_POSIX := $(SOURCE)
TARGET_POSIX := $(TARGET)
endif
SOURCE_STEM := $(shell filename=$$(basename "$(SOURCE_POSIX)"); printf '%s' "$${filename%.*}")

# Ensure tools from the 'dev' dependency-group are available when
# running code-quality and test targets. Use uv sync --group to
# install only the needed groups quickly.
UV_SYNC_DEV ?= uv sync --group dev

.PHONY: help install install-style fmt lint typecheck test docs latexpdf clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\t\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@printf '\ninstall-style variables:\n'
	@printf '  SOURCE  CSL input file (default: %s)\n' "$(SOURCE_POSIX)"
	@printf '  TARGET  Output directory (default: %s)\n' "$(TARGET_POSIX)"
	@printf '  OUTPUTS $(SOURCE_STEM).xsl and $(SOURCE_STEM)_table.xsl\n'
	@printf '\nExample (PowerShell):\n'
	@printf '  $$source = Join-Path $$env:TEMP "ieee.csl"\n'
	@printf '  Invoke-WebRequest -Uri "https://www.zotero.org/styles/ieee" -OutFile $$source\n'
	@printf '  make install-style TARGET="$$env:APPDATA\Microsoft\Bibliography\Style" `\n'
	@printf '    SOURCE="$$source"\n'

install: ## Install all dependency-groups
	uv sync --all-groups

install-style: ## Install the converted styles into Word's standard style directory
	uv run bib-csl-xsl $(SOURCE_POSIX) --output "$(TARGET_POSIX)/$(SOURCE_STEM).xsl"
	uv run bib-csl-xsl $(SOURCE_POSIX) --output "$(TARGET_POSIX)/$(SOURCE_STEM)_table.xsl" \
		--bibliography-format reference-table

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

docs: ## Build Sphinx docs (ensure docs group installed)
	$(MAKE) -C docs html

latexpdf: ## Build Sphinx PDF docs (ensure docs group installed)
	$(MAKE) -C docs latexpdf

clean: ## Remove build artifacts and caches
	rm -rf dist/ build/ *.egg-info .venv/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ .ty_cache/ htmlcov/
	rm -rf docs/_build/ docs/apidocs/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
