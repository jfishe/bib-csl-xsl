"""Model persistence and metrics utilities.

Provides thin wrappers for saving / loading trained models and writing
structured metrics to JSON so they can be tracked in version control or
a metrics store.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MODELS_DIR = _PROJECT_ROOT / "models"


def save_model(model: Any, filename: str) -> Path:
    """Serialise *model* to ``models/<filename>`` using :mod:`joblib`.

    Parameters
    ----------
    model : Any
        A fitted estimator, such as a scikit-learn model.
    filename : str
        Destination filename, e.g. ``"clf_v1.joblib"``.

    Returns
    -------
    Path
        Absolute path to the saved file.
    """
    import joblib  # lazy import — not everyone needs it

    path = _MODELS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(filename: str) -> Any:
    """Load a model previously saved with :func:`save_model`.

    Parameters
    ----------
    filename : str
        File inside ``models/``.

    Returns
    -------
    Any
        The deserialised model object.
    """
    import joblib

    path = _MODELS_DIR / filename
    return joblib.load(path)


def save_metrics(metrics: dict[str, Any], filename: str = "metrics.json") -> Path:
    """Write a metrics dict to ``models/<filename>`` as pretty-printed JSON.

    Parameters
    ----------
    metrics : dict[str, Any]
        Arbitrary key-value pairs such as accuracy or RMSE.
    filename : str, default="metrics.json"
        Destination inside ``models/``.

    Returns
    -------
    Path
        Absolute path to the written file.
    """
    path = _MODELS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2) + "\n")
    return path
