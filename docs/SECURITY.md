# Security Notes

SupportForge is intended for read-only diagnostics and controlled security review in
isolated or restricted Linux environments.

## Design controls

- No telemetry
- No external network requests
- No automatic package installation
- No privilege escalation
- No `eval`, `exec`, dynamic code loading, or `shell=True`
- Fixed diagnostic commands
- Validated hostnames, ports, PostgreSQL identifiers, and device paths
- No password command-line arguments
- Redaction enabled by default
- SHA-256 manifests for incident bundles
- Offline CycloneDX SBOM generation
- Configuration hash baselines

## Deployment process

1. Review the complete source tree.
2. Run all tests in a disposable VM.
3. Generate and archive a release SHA-256 digest.
4. Generate an SBOM.
5. Sign the release using the organization's approved signing process.
6. Install from an approved offline repository.
7. Run as an unprivileged account.
8. Store reports according to data-classification policy.
9. Review all audit findings before applying changes.
10. Repeat security audits after updates and at least monthly.

## Important limitation

SupportForge does not claim compliance with any military, government, NATO, ISO, NIST,
or national standard. Compliance depends on the complete accredited environment,
approved procedures, configuration baseline, supply chain, and operational controls.
