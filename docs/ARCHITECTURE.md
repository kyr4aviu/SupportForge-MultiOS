# SupportForge Multi-OS 1.0 Architecture

```text
GUI
 |
Workstation core
 |-- health rules
 |-- evidence/provenance
 |-- history/diff
 |-- redaction/report export
 |
Platform adapter
 |-- Linux
 |-- Windows
 `-- macOS

Optional collectors:
 |-- Docker
 `-- PostgreSQL
```

The host collector is native. Docker is optional and is not used as a privileged
bridge into the host operating system.

The GUI and workstation core are the product boundary. Legacy 1.x CLI workflows,
plugin execution, SBOM/SARIF generation, SMART tooling, policy engines, and
release-manifest features were deliberately removed from Multi-OS 1.0 to reduce
attack surface and maintenance cost.
