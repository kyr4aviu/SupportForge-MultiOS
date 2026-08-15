# SupportForge Multi-OS 1.0

SupportForge is an offline-first cross-platform desktop workstation for technical
support diagnostics.

The Multi-OS 1.0 release intentionally has a narrow scope:

- native GUI
- host system/network/storage/log diagnostics
- security-state collection
- optional Docker status
- optional PostgreSQL status
- health findings
- searchable evidence
- local scan history and snapshot comparison
- redacted JSON / HTML / incident bundle export

SupportForge does not automatically elevate privileges, does not require a cloud
service, and does not grant Docker privileged host access.

## Run from source

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m supportforge.gui
```

## Run on macOS

After creating `.venv` with the commands above, double-click
`Run SupportForge Multi-OS.app` in the project folder. The launcher uses the
project-local environment and automatically discovers Docker Desktop and
Postgres.app command-line tools.

## Validate

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_release.py
python3 scripts/validate_host.py
```

Windows and macOS must be validated on actual target hosts before their binaries
are described as validated releases.

See `docs/ARCHITECTURE.md` and `docs/PERMISSIONS_MATRIX.md`.
