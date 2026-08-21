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

# Sphinx's "colorrows" table style patches colortbl's internal \CT@everycr
# token list directly. Newer colortbl releases (which switch to LaTeX3
# hooks internally) conflict with that patch and cause infinite macro
# recursion ("TeX capacity exceeded, sorry [input stack size=...]") inside
# longtable headers on MiKTeX. Disable it; booktabs rules are unaffected.
latex_table_style = ["booktabs"]

# xelatex defaults to xindy for the index, but xindy is a Perl script whose
# Windows-vs-TeXLive detection breaks under MiKTeX whenever a non-Windows
# perl.exe (e.g. Git for Windows' bundled Perl) precedes MiKTeX's own on
# PATH ("not a symlink as required for TeX Live"). All index entries here
# are ASCII Python identifiers, so plain makeindex works fine and sidesteps
# the issue entirely.
latex_use_xindy = False

# latex_elements = {}
latex_elements = {
    "preamble": r"""
        % Ensure paths are treated with forward slashes
        \usepackage{grffile} % Helps with complex filenames if needed
    """
}

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
