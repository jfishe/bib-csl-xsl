"""Notebook-friendly DataFrame display helpers.

Use these helpers when you want one table representation that renders well
inside JupyterLab and also exports cleanly through ``nbconvert``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


def configure_notebook_display(
    *, max_rows: int = 120, max_columns: int = 40, precision: int = 3
) -> None:
    """Set sensible pandas defaults for exploratory notebooks.

    Parameters
    ----------
    max_rows : int, default=120
        Maximum rows pandas shows for direct DataFrame display.
    max_columns : int, default=40
        Maximum columns pandas shows for direct DataFrame display.
    precision : int, default=3
        Default numeric precision for pandas and Styler output.
    """
    pd.set_option("display.max_rows", max_rows)
    pd.set_option("display.max_columns", max_columns)
    pd.set_option("display.precision", precision)
    pd.set_option("styler.format.precision", precision)


def display_dataframe(
    df: pd.DataFrame,
    *,
    caption: str | None = None,
    label: str | None = None,
    precision: int = 3,
    max_rows: int | None = 20,
    na_rep: str = "—",
) -> "DataFrameDisplay":
    """Return a rich display wrapper for notebook and nbconvert output.

    Parameters
    ----------
    df : pd.DataFrame
        Table to render.
    caption : str, optional
        Caption used in HTML and LaTeX output.
    label : str, optional
        LaTeX label for cross-references. Requires ``caption``.
    precision : int, default=3
        Numeric precision for rendered values.
    max_rows : int, optional
        Maximum rows to render. Use ``None`` to render the full DataFrame.
    na_rep : str, default="—"
        Replacement text for missing values.

    Returns
    -------
    DataFrameDisplay
        Wrapper with HTML, LaTeX, and plain-text representations.
    """
    if label is not None and caption is None:
        msg = "label requires a caption"
        raise ValueError(msg)

    preview = _preview_dataframe(df, max_rows=max_rows)
    return DataFrameDisplay(
        preview=preview,
        total_rows=len(df),
        caption=caption,
        label=label,
        precision=precision,
        na_rep=na_rep,
    )


def _preview_dataframe(df: pd.DataFrame, *, max_rows: int | None) -> pd.DataFrame:
    if max_rows is None or len(df) <= max_rows:
        return df.copy()
    return df.head(max_rows).copy()


def _require_styler_dependencies() -> None:
    try:
        import jinja2  # noqa: F401
    except ImportError as exc:
        msg = "display_dataframe() requires jinja2; install the notebooks group."
        raise RuntimeError(msg) from exc


@dataclass(slots=True)
class DataFrameDisplay:
    """Rich display wrapper that supports notebook and nbconvert exports."""

    preview: pd.DataFrame
    total_rows: int
    caption: str | None
    label: str | None
    precision: int
    na_rep: str

    def __repr__(self) -> str:
        return self._plain_text()

    def _repr_mimebundle_(
        self, include: object | None = None, exclude: object | None = None
    ) -> dict[str, str]:
        del include, exclude
        styler = self._styler()
        return {
            "text/plain": self._plain_text(),
            "text/html": styler.to_html(),
            "text/latex": styler.to_latex(
                hrules=True,
                caption=self.caption,
                label=self.label,
            ),
        }

    def _plain_text(self) -> str:
        body = self.preview.to_string()
        if len(self.preview) == self.total_rows:
            return body
        return (
            f"Showing first {len(self.preview)} of {self.total_rows} rows.\n\n"
            f"{body}"
        )

    def _styler(self) -> pd.io.formats.style.Styler:
        _require_styler_dependencies()
        styler = self.preview.style.format(precision=self.precision, na_rep=self.na_rep)
        if self.caption is not None:
            styler = styler.set_caption(self.caption)
        return styler
