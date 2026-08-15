# Security Design

SupportForge MultiOS is intended for local, read-only diagnostics.

## Controls

- No telemetry or automatic external network requests
- No automatic package installation or privilege escalation
- No `eval`, dynamic code loading, or `shell=True`
- Fixed diagnostic commands with bounded execution time
- No password command-line arguments
- Redaction enabled for shared reports
- Bounded macOS unified-log output
- Compact provenance hashes instead of duplicated evidence
- SHA-256 manifests for incident bundles

## Operational guidance

1. Review the source and run the automated tests.
2. Validate the application on each target operating system.
3. Run it as an unprivileged account.
4. Review reports before sharing them.
5. Store reports according to the applicable data-classification policy.
6. Sign packaged artifacts using the organization's approved process.

SupportForge does not claim compliance certification. Compliance depends on the
complete environment, configuration baseline, procedures, supply chain, and
operational controls.
