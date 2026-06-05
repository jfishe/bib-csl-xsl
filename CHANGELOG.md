# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

<!-- markdownlint-disable MD024 -->

## [Unreleased]

## [0.2.1] - 2026-06-05

### Added

- Added a CLI for converting numeric CSL styles into standalone Microsoft Word
  bibliography XSL styles.
- Added support for the IEEE fixture-driven subset of CSL used by the converter.
- Added regression tests covering CSL parsing, XSL generation, and CLI behavior.

### Changed

- Reworked generated Word styles to match Word's expectations for metadata,
  bibliography layout, citation fragments, and source dialog fields.
- Simplified the repository by removing unused scaffold modules and stale build
  artifacts.
- Updated the README to document the project's versioning and changelog policy.

### Fixed

- Fixed generated XSL validity issues that prevented Word from loading custom
  bibliography styles.

- Fixed bibliography numbering, table-based bibliography output, and citation
  locator handling for Word compatibility.

[0.2.1]: https://github.com/jfishe/bib-csl-xsl/releases/tag/v0.2.1
[keep a changelog]: https://keepachangelog.com/en/1.1.0/
[semantic versioning]: https://semver.org/
[unreleased]: https://github.com/jfishe/bib-csl-xsl/compare/v0.2.1...HEAD
