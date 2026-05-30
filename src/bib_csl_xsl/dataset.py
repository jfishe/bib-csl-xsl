"""Data loading and persistence utilities.

Conventions
-----------
- **raw** data is immutable — never overwrite files in ``data/raw/``.
- **interim** data holds intermediate transforms.
- **processed** data is the final, analysis-ready output.
- **external** data comes from third-party sources.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_LAYER_MAP: dict[str, Path] = {
    "raw": _PROJECT_ROOT / "data" / "raw",
    "interim": _PROJECT_ROOT / "data" / "interim",
    "processed": _PROJECT_ROOT / "data" / "processed",
    "external": _PROJECT_ROOT / "data" / "external",
}

Layer = Literal["raw", "interim", "processed", "external"]


def _resolve(filename: str, layer: Layer) -> Path:
    return _LAYER_MAP[layer] / filename


# ------------------------------------------------------------------
# Loading
# ------------------------------------------------------------------

def load_raw(filename: str) -> pd.DataFrame:
    """Load a file from ``data/raw/``."""
    return _read(filename, "raw")


def load_processed(filename: str) -> pd.DataFrame:
    """Load a file from ``data/processed/``."""
    return _read(filename, "processed")


def _read(filename: str, layer: Layer) -> pd.DataFrame:
    path = _resolve(filename, layer)
    suffix = path.suffix.lower()
    readers: dict[str, Any] = {
        ".csv": pd.read_csv,
        ".parquet": pd.read_parquet,
        ".json": pd.read_json,
        ".xlsx": pd.read_excel,
    }
    reader = readers.get(suffix)
    if reader is None:
        msg = f"Unsupported file format: {suffix}"
        raise ValueError(msg)
    return reader(path)  # type: ignore[no-any-return]


# ------------------------------------------------------------------
# Saving
# ------------------------------------------------------------------

def save_processed(df: pd.DataFrame, filename: str) -> Path:
    """Persist a DataFrame to ``data/processed/``."""
    return _write(df, filename, "processed")


def save_interim(df: pd.DataFrame, filename: str) -> Path:
    """Persist a DataFrame to ``data/interim/``."""
    return _write(df, filename, "interim")


def _write(df: pd.DataFrame, filename: str, layer: Layer) -> Path:
    path = _resolve(filename, layer)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    writers: dict[str, str] = {
        ".csv": "to_csv",
        ".parquet": "to_parquet",
        ".json": "to_json",
        ".xlsx": "to_excel",
    }
    method_name = writers.get(suffix)
    if method_name is None:
        msg = f"Unsupported file format: {suffix}"
        raise ValueError(msg)
    getattr(df, method_name)(path, index=False)
    return path


# Allow ``from typing import Any`` to be deferred
from typing import Any  # noqa: E402
