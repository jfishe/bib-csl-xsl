"""Sphinx configuration for bib-csl-xsl."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "_ext"))

project = "bib-csl-xsl"
author = "John D. Fisher"
copyright = "2026, John D. Fisher"  # noqa: A001

extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

source_suffix = [".rst", ".md"]

autodoc2_packages = ["../src/bib_csl_xsl"]
autodoc2_docstring_parser_regexes = [
    (r".*", "napoleon_numpy_parser"),
]

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = False
napoleon_use_rtype = False

html_theme = "furo"

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

myst_heading_anchors = 5

latex_engine = "xelatex"

latex_elements = {}

latex_documents = [
    (
        "index",
        "bib-csl-xsl.tex",
        "bib-csl-xsl Documentation",
        "John D. Fisher",
        "manual",
    ),
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
