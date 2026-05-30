"""Smoke tests — replace with real tests as the project grows."""

from __future__ import annotations


def test_version_is_string() -> None:
    from bib_csl_xsl import __version__

    assert isinstance(__version__, str)
    parts = __version__.split(".")
    assert len(parts) >= 2, "Version should be semver-ish (e.g. 0.1.0)"


def test_importable() -> None:
    """Verify the package can be imported without errors."""
    import bib_csl_xsl  # noqa: F401
    import bib_csl_xsl.dataset  # noqa: F401
    import bib_csl_xsl.features  # noqa: F401
    import bib_csl_xsl.modeling  # noqa: F401
