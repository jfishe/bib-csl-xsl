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

# Sphinx's own `-M latexpdf` shells out to the generated make.bat via
# Python's subprocess.call(['make.bat', ...]), which cannot launch a .bat
# file without a shell (fails with "Error: Failed to run: make.bat" on
# Windows). Build the LaTeX sources with `-M latex`, then run the same
# `latexmk` command make.bat would have run, directly (a real .exe, so it
# needs no cmd.exe wrapper -- which itself mangles `/c` under MSYS/Git Bash).
ifeq ($(OS),Windows_NT)
latexpdf:
	@$(UV_SYNC_DOCS)
	@$(SPHINXBUILD) -M latex "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	cd "$(BUILDDIR)/latex" && for f in *.tex; do latexmk -pdf -dvi- -ps- "$$f"; done
endif

%: Makefile
	@$(UV_SYNC_DOCS)
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
