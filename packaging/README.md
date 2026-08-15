# Offline packaging

Build only in a pre-provisioned offline environment. SupportForge does not fetch
build dependencies.

Source execution requires only Python's standard library.

For a packaged desktop executable, use a locally approved/provisioned packager
on the target operating system and validate the resulting binary on that same OS.
Do not label cross-built artifacts as validated.
