# Shared GComs Rust integration

GChat is a consumer of the paired GComs facade/runtime consolidation.
The file UI maps conversation IDs to GComs channel/member scopes. Existing
archive and encrypted cache formats are preserved. GC/2 selection is explicit.

Implementation is in progress; compile checks passed before the latest dependency
cleanup. Full paired tests, generated contracts, desktop checks and native
platform qualification remain pending. See the paired GComs TESTPLAN.md.
