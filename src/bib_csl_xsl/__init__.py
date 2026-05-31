"""Convert CSL styles into Microsoft Word bibliography XSL styles."""

from bib_csl_xsl.converter import (
    ConversionError,
    CslStyle,
    convert_csl_file,
    parse_csl_style,
    validate_style,
    write_word_bibliography_style,
)

__all__ = [
    "ConversionError",
    "CslStyle",
    "convert_csl_file",
    "parse_csl_style",
    "validate_style",
    "write_word_bibliography_style",
]

__version__ = "0.1.0"
