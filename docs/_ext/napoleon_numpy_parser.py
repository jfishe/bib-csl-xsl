"""Docutils parser that converts NumPy-style docstrings via Napoleon."""

from __future__ import annotations

from docutils.parsers.rst import Parser as RstParser
from sphinx.ext.napoleon import Config, NumpyDocstring


class Parser(RstParser):
    """Parse NumPy-style docstrings after converting them to reStructuredText."""

    def parse(self, inputstring: str, document) -> None:  # type: ignore[override]
        """Convert a NumPy-style docstring to reStructuredText before parsing."""
        config = Config(
            napoleon_google_docstring=False,
            napoleon_numpy_docstring=True,
            napoleon_use_param=False,
            napoleon_use_rtype=False,
        )
        converted = str(NumpyDocstring(inputstring, config=config))
        super().parse(converted, document)
