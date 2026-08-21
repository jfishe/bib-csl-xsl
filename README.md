# bib-csl-xsl

Convert Citation Style Language to XML Style Language, CSL to XSL,
for Microsoft Word bibliography.

## Development

Install the development tools with [uv]:

```powershell
uv lock --upgrade
uv sync --group dev
```

Optional, install external tools with [pixi]:

```powershell
pixi global install make miktex
```

You may need to run `mpm` and change
Settings for Package installation to Ask me.

## Usage

```powershell
make help

uv run bib-csl-xsl --help

uv run bib-csl-xsl .\tests\fixtures\ieee.csl --output .\ieee.xsl
```

To generate the five-column, reference-table layout instead of the
default bibliography output:

```powershell
uv run bib-csl-xsl .\tests\fixtures\ieee.csl --output .\ieee.xsl `
  --bibliography-format reference-table
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
# Install <source-basename>.xsl and <source-basename>_table.xsl
# into Word's style directory
$source = Join-Path $env:TEMP "ieee.csl"
Invoke-WebRequest -Uri "https://www.zotero.org/styles/ieee" -OutFile $source
make install-style TARGET="$env:APPDATA\Microsoft\Bibliography\Style" `
  SOURCE="$source"

make lint
make typecheck
make test
uv build
```

### Documentation

```powershell
make docs
$job = Start-Job -ScriptBlock {
    uv run python -m http.server --bind localhost 8000 `
      --directory docs/_build/html
}
Receive-Job $job -Keep
Start-Process "http://[::1]:8000/"
# Receive-Job $job -Wait
# Remove-Job $job -Force
```

## Versioning and ChangeLog

This project follows [Semantic Versioning] and keeps
human-readable release notes in [CHANGELOG.md]. The changelog format
follows [Keep a Changelog].

[changelog.md]: CHANGELOG.md
[keep a changelog]: https://keepachangelog.com/en/1.1.0/
[pixi]: https://prefix.dev/tools/pixi
[semantic versioning]: https://semver.org/
[uv]: https://docs.astral.sh/uv/
