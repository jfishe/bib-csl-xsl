# Minimal Sphinx makefile for generated projects.

UV_SYNC_DOCS ?= uv sync --group docs
SPHINXBUILD ?= uv run sphinx-build
SPHINXOPTS ?=
SOURCEDIR = .
BUILDDIR = _build

.PHONY: help clean Makefile

help:
	@$(UV_SYNC_DOCS)
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf "$(BUILDDIR)" apidocs

%: Makefile
	@$(UV_SYNC_DOCS)
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
