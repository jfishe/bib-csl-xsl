# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

<!-- markdownlint-disable MD024 -->

## [Unreleased]

### Added

### Changed

- Updated the README to document the project's versioning and changelog policy.

## [0.1.0] - 2026-06-05

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

### Fixed

- Fixed generated XSL validity issues that prevented Word from loading custom
  bibliography styles.
- Fixed bibliography numbering, table-based bibliography output, and citation
  locator handling for Word compatibility.
