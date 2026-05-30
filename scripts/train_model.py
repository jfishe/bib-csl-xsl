#!/usr/bin/env python
"""Train a model from the command line.

Usage::

    uv run python scripts/train_model.py -c configs/experiment.yaml
    uv run python scripts/train_model.py -c configs/experiment.yaml -vv

This script is the *production* entry point. Keep heavy logic in
``src/bib_csl_xsl/`` and call it from here so the
package stays testable and the script stays thin.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project imports (package is installed via `uv sync`)
# ---------------------------------------------------------------------------
import bib_csl_xsl
from bib_csl_xsl.dataset import load_processed
from bib_csl_xsl.features import build_features
from bib_csl_xsl.modeling import save_metrics, save_model

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config(path: Path) -> dict:
    """Load a YAML or JSON config file."""
    text = path.read_text()
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml  # optional dep
        except ImportError as exc:
            msg = "PyYAML is required to load YAML configs: uv add pyyaml"
            raise SystemExit(msg) from exc
        return yaml.safe_load(text)  # type: ignore[no-any-return]
    return json.loads(text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Train a model for bib-csl-xsl.",
    )
    parser.add_argument(
        "-c", "--config",
        required=True,
        type=Path,
        help="Path to a YAML/JSON config file (e.g. configs/experiment.yaml).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (-v = INFO, -vv = DEBUG).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s ({ cookiecutter.package_name }} {  bib_csl_xsl.__version__})",
    )
    args = parser.parse_args(argv)

    # ---- logging ----
    level = {0: logging.WARNING, 1: logging.INFO}.get(args.verbose, logging.DEBUG)
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        datefmt="%Y-%m-%d %H:%M",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    _logger.info("Loading config from %s", args.config)
    cfg = _load_config(args.config)
    _logger.debug("Config: %s", cfg)

    # -----------------------------------------------------------------
    # YOUR TRAINING LOGIC GOES HERE
    # -----------------------------------------------------------------
    # Example workflow:
    #
    #   df = load_processed(cfg["dataset"])
    #   df = build_features(df)
    #
    #   X = df.drop(columns=[cfg["target"]])
    #   y = df[cfg["target"]]
    #
    #   from sklearn.ensemble import RandomForestClassifier
    #   clf = RandomForestClassifier(**cfg.get("model_params", {}))
    #   clf.fit(X, y)
    #
    #   save_model(clf, cfg.get("model_file", "model.joblib"))
    #   save_metrics({"accuracy": clf.score(X, y)}, cfg.get("metrics_file", "metrics.json"))
    #
    _logger.warning(
        "train_model.py is a stub — implement your pipeline above. "
        "See the getting-started notebook for a worked example."
    )


if __name__ == "__main__":
    main()
