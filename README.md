# bib-csl-xsl

<!-- docs:badges:start -->
[![CI](https://github.com/jfishe/bib-csl-xsl/actions/workflows/ci.yml/badge.svg)](https://github.com/jfishe/bib-csl-xsl/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/jfishe/bib-csl-xsl/blob/main/LICENSE)
<!-- docs:badges:end -->

> Convert Citation Style Language to XML Style Language, CSL to XSL, for Microsoft Word bibliography.

## Project Layout

```text
├── src/bib_csl_xsl/
│   ├── __init__.py
│   ├── py.typed               ← PEP 561 type-checking marker
│   ├── dataset.py             ← data loading & saving
│   ├── features.py            ← feature engineering
│   └── modeling.py            ← model persistence & metrics
├── tests/
│   ├── __init__.py
│   └── test_placeholder.py
├── data/
│   ├── raw/                   ← immutable original data
│   ├── interim/               ← intermediate transforms
│   ├── processed/             ← final, analysis-ready data
│   └── external/              ← third-party reference data
├── models/                    ← serialised models & metrics
├── notebooks/
│   └── getting-started.ipynb  ← starter notebook (dsproject-style)
├── reports/
│   └── figures/               ← generated plots
├── scripts/
│   └── train_model.py         ← CLI training entry point
├── configs/
│   └── example.yaml           ← experiment configuration template
├── references/                ← data dictionaries, papers, manuals
├── docs/                      ← Sphinx + MyST documentation
├── .readthedocs.yaml          ← Read the Docs build config
├── .github/workflows/         ← CI & release pipelines
├── pyproject.toml             ← single source of truth
├── Makefile                   ← common task shortcuts
├── .pre-commit-config.yaml    ← ruff, mypy, standard hooks
│                                (includes pandas-stubs and joblib-stubs in dev)
├── .gitignore
├── LICENSE
└── README.md
```

## Quickstart

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtualenv & install all deps
make install          # or: uv sync --all-groups

# Run tests
make test             # or: uv run pytest

# Format & lint
make fmt lint
```

## Data Workflow

```python
from bib_csl_xsl.dataset import load_raw, save_processed
from bib_csl_xsl.features import build_features

df = load_raw("experiment_01.csv")
df = build_features(df)
save_processed(df, "experiment_01_features.parquet")
```

## Documentation

```bash
make docs             # builds to docs/_build/html/
make latexpdf         # builds docs/_build/latex/*.pdf
```

Read the Docs can use the bundled `.readthedocs.yaml`, which installs the
`docs` dependency group via `uv sync` and points RTD at `docs/conf.py`.

To build PDF docs, install a TeX toolchain first.
On Debian or Ubuntu, the minimum packages are typically:

```bash
sudo apt install latexmk texlive-xetex xindy
```

Then run:

```bash
make latexpdf
make -C docs clean    # removes Sphinx build artifacts
```

## Makefile Targets

| Target | Description |
|---|---|
| `install` | `uv sync --all-groups` |
| `fmt` | Auto-format with Ruff (installs dev group if needed) |
| `lint` | Lint with Ruff (installs dev group if needed) |
| `typecheck` | Run mypy (ensure dev group installed) |
| `test` | Run pytest with coverage (ensure dev group installed) |
| `jupyter` | Launch JupyterLab (syncs notebooks group) |
| `docs` | Build Sphinx docs (syncs docs group) |
| `latexpdf` | Build Sphinx PDF docs (syncs docs group) |
| `docker-build` | Build Docker image |
| `clean` | Remove caches & build artifacts |

## Contributing

1. Fork & clone
2. `make install`
3. Create a feature branch
4. `make fmt lint typecheck test`
5. Open a pull request

## License
[MIT](https://github.com/jfishe/bib-csl-xsl/blob/main/LICENSE)
