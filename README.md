# SupportForge MultiOS

SupportForge MultiOS is an offline-first desktop application for collecting,
reviewing, comparing, and exporting technical-support diagnostics on macOS,
Linux, and Windows. Version 1.0.2 uses only the Python standard library at
runtime and does not send telemetry or diagnostic data to a cloud service.

## Features

- Native Tk desktop interface
- System, network, storage, service, and operating-system log diagnostics
- Security-state collection
- Optional Docker and PostgreSQL diagnostics
- Health findings and searchable evidence
- Local snapshot history with side-by-side comparison
- Strict-redacted JSON and HTML incident bundles with SHA-256 manifests

SupportForge never elevates privileges automatically. Unavailable or restricted
sources are reported without weakening host security controls.

## Requirements

- Python 3.10 or newer with Tk support
- Optional: Docker CLI and access to the Docker daemon
- Optional: PostgreSQL `pg_isready` and `psql` tools

## Install and run

From a fresh clone on macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m supportforge.gui
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m supportforge.gui
```

On macOS, after creating `.venv`, you can instead double-click
`Run SupportForge MultiOS.app`. The launcher discovers Docker Desktop and
Postgres.app command-line tools automatically.

## Validate

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/verify_release.py
.venv/bin/python scripts/validate_host.py
```

The Intel macOS build is validated on macOS 14. The Alpine container provides a
Linux GUI smoke test; native Linux and Windows host validation remains required
before publishing platform-specific launchers.

See [Architecture](docs/ARCHITECTURE.md),
[Permissions](docs/PERMISSIONS_MATRIX.md), and [Security](SECURITY.md).

## License

SupportForge MultiOS is released under the [MIT License](LICENSE).
