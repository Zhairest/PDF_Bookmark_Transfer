# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Planned

- optional page-mapping support for PDFs with shifted pagination
- additional real-world validation samples

## [0.2.1] - 2026-04-16

### Fixed

- switched the GitHub release workflow from the retired `macos-13` runner to `macos-14`
- aligned release documentation with the supported macOS runner label

## [0.2.0] - 2026-04-16

### Added

- Windows desktop packaging via `PyInstaller`
- automated GitHub Actions workflow for macOS and Windows release assets
- release asset checksums and tag-driven GitHub Releases publishing
- expanded project documentation for downloads, release workflow, and public repository publishing

## [0.1.0] - 2026-04-10

### Added

- core PDF bookmark transfer logic based on `pypdf`
- command-line workflow for direct bookmark copying
- `PySide6 / Qt` desktop GUI for point-and-click conversion
- macOS `PyInstaller` packaging for `.app` and `.zip` output
- bilingual project documentation
- MIT license
