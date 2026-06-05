# Copilot Instructions for `bib-csl-xsl`

## Build, test, lint, and docs commands

This repository uses `uv` for environment management and command
execution.

- Install dev tools: `uv sync --group dev`
- Build the package: `uv build`
- Run the full test suite: `uv run pytest -q`
- Run one test file: `uv run pytest tests\test_converter.py -q`
- Run one test case:
  `uv run pytest tests\test_converter.py::test_cli_writes_output_file -q`
- Run coverage locally: `uv run pytest --cov --cov-report=term-missing`
- Lint: `uv run ruff check src tests`
- Format check: `uv run ruff format --check src tests`
- Auto-format: `uv run ruff format src tests && uv run ruff check --fix src tests`
- Type-check: `uv run mypy src`
- Build docs: `uv sync --group docs && uv run sphinx-build -M html docs docs\_build`

If `make` is available, the root `Makefile` wraps the common workflows:
`make lint`, `make typecheck`, `make test`, and `make docs`.

## High-level architecture

The active product path is the CSL-to-XSL converter in
`src\bib_csl_xsl\converter.py`, exposed through the CLI in
`src\bib_csl_xsl\__main__.py` and re-exported from
`src\bib_csl_xsl\__init__.py`.

The conversion flow is:

1. `parse_csl_style()` parses the CSL XML with `defusedxml`, validates
   that only the supported CSL subset appears, and extracts the
   `<info>` metadata, `<citation>` / `<bibliography>` layouts, and named
   macros into a `CslStyle` dataclass.
1. `validate_style()` currently enforces the supported scope: only
   numeric CSL styles are accepted.
1. `write_word_bibliography_style()` instantiates the internal
   `_Compiler`, which recursively compiles CSL nodes into XSL fragments
   and emits a standalone Word bibliography stylesheet.

Within `converter.py`, the compiler is driven by mapping tables near the
top of the file:

- `PERSON_ROLE_PATHS`, `TEXT_VARIABLE_PATHS`, and
  `DATE_VARIABLE_PARTS` map supported CSL variables onto Word
  bibliography XML fields.
- `TERMS` and `CSL_TO_WORD_TYPES` translate CSL terms and item types
  into Word-compatible output.
- `SUPPORTED_TAGS` defines the allowed CSL subset before compilation starts.

`tests\test_converter.py` uses `tests\fixtures\ieee.csl` as the
canonical fixture. The current support envelope is the numeric CSL
subset exercised by that IEEE style, and tests assert that the
generated XSL is standalone rather than depending on Word's bundled IEEE
stylesheet.

The repository also contains `dataset.py`, `features.py`,
`modeling.py`, and `scripts\train_model.py`, but those are
scaffolding/stubbed data-science utilities and are not part of the
current converter execution path.

The documentation build is Sphinx-based (`docs\conf.py`) and
`docs\readme.md` pulls in the root `README.md`, so README changes also
affect the published docs.

## Key conventions

- Preserve the converter's fail-fast behavior. Unsupported CSL tags,
  variables, or incompatible styles should raise `ConversionError`
  rather than silently degrading.
- When adding CSL support, update the constant mapping tables near the
  top of `converter.py` and the relevant `_compile_*` / condition
  helpers together; support is intentionally centralized there.
- `_compile_*` methods return `Fragment` objects that represent content
  before outer formatting is applied. Prefix/suffix/quotes/text-case
  handling is centralized in `_apply_text_decorations()`,
  `_wrap_fragment()`, and `_wrap_existing_var()`. Reuse that path
  instead of duplicating formatting logic in new compiler branches.
- The CLI layer should stay thin: argument parsing belongs in
  `__main__.py`, while conversion logic stays in `converter.py`.
- NumPy-style docstrings are the repository standard (`ruff` is
  configured for `pydocstyle` with the NumPy convention, and Sphinx uses
  a custom Napoleon parser to render those docstrings).
- Keep typing strict. `mypy` runs in strict mode, and the existing code
  favors `Path`, dataclasses with `slots=True`, and explicit helper
  functions instead of loose dictionaries passed around at runtime.
- Treat `tests\fixtures\ieee.csl` as the primary regression fixture when
  changing converter behavior, and extend `tests\test_converter.py` when
  expanding the supported CSL subset.
