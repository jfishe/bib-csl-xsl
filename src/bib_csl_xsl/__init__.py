"""Convert CSL styles into Microsoft Word bibliography XSL styles."""

from importlib.metadata import version

from bib_csl_xsl.converter import (
    BibliographyFormat,
    ConversionError,
    CslStyle,
    convert_csl_file,
    parse_csl_style,
    validate_style,
    write_word_bibliography_style,
)

__all__ = [
    "BibliographyFormat",
    "ConversionError",
    "CslStyle",
    "convert_csl_file",
    "parse_csl_style",
    "validate_style",
    "write_word_bibliography_style",
]

__version__ = version("bib-csl-xsl")
