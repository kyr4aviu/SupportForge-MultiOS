# Contributing to SupportForge

Thank you for considering a contribution.

## Development principles

- Read-only diagnostics by default
- No telemetry
- No hidden network access
- No `shell=True`
- No password arguments
- No unreviewed dynamic downloads
- Clear error handling and deterministic exit codes
- Tests for every new command or regression fix
- Documentation for all user-visible behavior

## Offline development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m unittest discover -s tests -v
python3 -m supportforge --help
```

## Pull request checklist

- [ ] Code is formatted and readable.
- [ ] New behavior has tests.
- [ ] Existing tests pass.
- [ ] Security implications were reviewed.
- [ ] Documentation and changelog were updated.
- [ ] No secrets, customer data, or classified information are included.
- [ ] New external dependencies are justified and can be supplied offline.

## Commit style

Use concise imperative messages:

```text
Add PostgreSQL lock diagnostics
Fix strict IP redaction
Document offline installation
```
