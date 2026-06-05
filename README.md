# bib-csl-xsl

Convert numeric CSL styles into standalone Microsoft Word bibliography XSL styles.

## Development

Install the development tools with `uv`:

```powershell
uv sync --group dev
```

## Usage

```powershell
uv run bib-csl-xsl .\tests\fixtures\ieee.csl --output .\ieee.xsl
```

You can also invoke the module directly:

```powershell
uv run python -m bib_csl_xsl .\tests\fixtures\ieee.csl --output .\ieee.xsl
```

## Current scope

The reconstructed converter targets the numeric CSL subset exercised
by the IEEE fixture:

- metadata from `<info>` for `Version`, `XslVersion`, `StyleName`, and `StyleNameLocalized`
- bibliography and citation layouts
- `text`, `number`, `label`, `date`, `group`, `choose`, and `names`
- creator substitution and `et al.` handling
- standalone output without copying Office's bundled IEEE XSL

## Common commands

```powershell
make lint
make typecheck
make test
make docs
uv build
```

## Versioning and changelog

This project follows [Semantic Versioning] and keeps
human-readable release notes in [CHANGELOG.md]. The changelog format
follows [Keep a Changelog].

[changelog.md]: CHANGELOG.md
[keep a changelog]: https://keepachangelog.com/en/1.1.0/
[semantic versioning]: https://semver.org/
