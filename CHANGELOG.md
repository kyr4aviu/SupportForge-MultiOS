# Changelog

## Unreleased

- Redact local home-directory and database-user identifiers from shared reports.
- Bound macOS unified-log evidence to keep incident bundles compact.
- Store provenance hashes and metadata without duplicating raw evidence.
- Report only launchd jobs with nonzero exit status as service findings.

## SupportForge Multi-OS 1.0.0 — 2026-08-15

- Added native cross-platform workstation diagnostics and health findings.
- Added Docker Desktop and PostgreSQL diagnostics.
- Added searchable evidence, local scan history, and side-by-side comparisons.
- Added strict-redacted JSON and HTML incident bundles with SHA-256 manifests.
- Added a double-clickable macOS launcher with a native application icon.
- Validated the macOS Intel build on macOS 14 with Python 3.13 and Tk 8.6.

Windows and Linux launchers and platform validation remain pending testing on
their respective target systems.
