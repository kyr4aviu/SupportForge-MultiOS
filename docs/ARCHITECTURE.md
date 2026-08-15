# Architecture

```text
Tk GUI
  |
Workstation core
  |-- normalized snapshot schema
  |-- health rules
  |-- searchable evidence
  |-- local history and comparison
  |-- redaction and report export
  |
Platform adapter
  |-- macOS
  |-- Linux
  `-- Windows

Optional collectors
  |-- Docker
  `-- PostgreSQL
```

Platform adapters execute fixed, read-only commands without `shell=True` and
normalize their results into one workstation snapshot. Docker and PostgreSQL
collectors are optional and report unavailable tools or permissions explicitly.

Snapshots remain local. History is stored under `.supportforge/history` in the
current user's home directory. Shared exports pass through a redaction profile;
incident bundles contain redacted JSON, redacted HTML, and a SHA-256 manifest.

Provenance records contain source metadata and evidence hashes rather than a
second copy of raw diagnostic output. Large macOS unified-log output is bounded
to keep reports usable.
