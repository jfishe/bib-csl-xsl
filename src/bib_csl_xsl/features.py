"""Feature engineering pipeline.

Add project-specific feature transforms here.  The entry point is
:func:`build_features`, which accepts a raw or interim DataFrame and
returns an enriched copy.
"""

from __future__ import annotations

import pandas as pd


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature engineering steps and return a new DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input data, typically loaded via
        :func:`bib_csl_xsl.dataset.load_raw`.

    Returns
    -------
    pd.DataFrame
        A copy of *df* with additional or transformed columns.
    """
    df = df.copy()
    # ----- Add feature transforms below -----
    # Example:
    # df["log_value"] = np.log1p(df["value"])
    return df
