from __future__ import annotations

import argparse
from pathlib import Path

from bib_csl_xsl.converter import convert_csl_file


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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    output = args.output or args.source.with_suffix(".xsl")
    convert_csl_file(args.source, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
