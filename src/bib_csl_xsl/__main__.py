from __future__ import annotations

import argparse
from pathlib import Path

from bib_csl_xsl.converter import BibliographyFormat, convert_csl_file


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="bib-csl-xsl",
        description="Convert a numeric CSL style into a Word bibliography XSL style.",
    )
    parser.add_argument("source", type=Path, help="Path to the input CSL file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to the generated XSL file. Defaults to the input path with an .xsl suffix.",
    )
    parser.add_argument(
        "--bibliography-format",
        choices=[format_.value for format_ in BibliographyFormat],
        default=BibliographyFormat.STANDARD.value,
        help="Bibliography output layout. Defaults to the original standard output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    output = args.output or args.source.with_suffix(".xsl")
    convert_csl_file(
        args.source,
        output,
        bibliography_format=BibliographyFormat(args.bibliography_format),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
