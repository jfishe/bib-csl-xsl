# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

<!-- markdownlint-disable MD024 -->

## [Unreleased]

## [0.3.0] - 2026-06-06

### Added

- Added an opt-in `reference-table` bibliography format that generates a
  five-column table:
  - Reference Number
  - Author
  - Issue Date, Edition or Revision
  - Title
  - Document Number
- Reference-table revision column prefers revision, then edition,
  then issue date.
- Document Number column hyperlinks URL are used as hyperlink targets without
  being displayed.
- Added a `make install-style` shortcut that writes both the default IEEE
  style and the reference-table variant to Word's standard bibliography style
  directory.
- Added a CLI for converting numeric CSL styles into standalone Microsoft Word
  bibliography XSL styles.
- Added support for the IEEE fixture-driven subset of CSL used by the converter.
- Added regression tests covering CSL parsing, XSL generation, and CLI behavior.

### Changed

- Kept the legacy Word bibliography layout as the default output and made the
  reference-table layout selectable through the CLI and converter API.
- Gave the reference-table output a unique `StyleName` and
  `StyleNameLocalized` so it can coexist with the default style in Word.
- Split the reference-table citation output so the Title column contains only
  title-like fields and the Document Number column contains the remaining
  citation details.
- Expanded `make help` with `install-style` variable details and a
  PowerShell example for downloading a CSL file and installing both Word style
  outputs.
- Changed `make install-style` to derive installed XSL filenames from the
  source CSL basename instead of always writing IEEE-specific names.
- Switched package `__version__` to read from installed distribution metadata
  instead of a stale hardcoded value in `__init__.py`.
- Reworked generated Word styles to match Word's expectations for metadata,
  bibliography layout, citation fragments, and source dialog fields.
- Simplified the repository by removing unused scaffold modules and stale build
  artifacts.
- Updated the README to document the project's versioning and changelog policy.

### Fixed

- Fixed duplicated `Available::` output in generated bibliography styles.
- Fixed generated Word bibliography styles so Corporate Author entries use
  Word's direct `b:Corporate` paths and display correctly.
- Fixed generated XSL validity issues that prevented Word from loading custom
  bibliography styles.
- Fixed bibliography numbering, table-based bibliography output, and citation
  locator handling for Word compatibility.

[0.3.0]: https://github.com/jfishe/bib-csl-xsl/releases/tag/v0.3.0
[keep a changelog]: https://keepachangelog.com/en/1.1.0/
[semantic versioning]: https://semver.org/
[unreleased]: https://github.com/jfishe/bib-csl-xsl/compare/v0.3.0...HEAD
