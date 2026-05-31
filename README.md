# bib-csl-xsl

Convert numeric CSL styles into standalone Microsoft Word bibliography XSL styles.

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

## Development

```powershell
uv run pytest tests\test_converter.py
uv run ruff check src\bib_csl_xsl\converter.py src\bib_csl_xsl\__main__.py tests\test_converter.py
```
