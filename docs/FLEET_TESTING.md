# Native file-transfer fleet driver

`crates/core/examples/fleet_probe.rs` is an operator test attachment. It calls the
same `ChatClient` file controls and bounded native binary I/O as the terminal and
desktop attachments. It generates reproducible sender-local fixtures, imports
them, and independently hashes exported receiver files. False completion, size
mismatch and digest mismatch are errors. Existing export paths are not overwritten.

The JSON command interface supports ordinary chat requests, fixture generation,
import, partial import for crash recovery, export-and-verify, and verification.
Every fixture name is one path component beneath the selected private directory.
Requests are limited to 64 KiB; file bytes never travel in coordinator JSON.
On Unix, `--serve <chat-endpoint> <fixture-directory> <probe-socket>` serves at most
16 bounded owner-local requests concurrently over a 0600 Unix socket, using
big-endian u32 length framing. This avoids a new process per progress sample.
The probe is an example executable, not a remotely exposed application API.

Build and run through GComs' `scripts/build-fleet-files.py` and
`scripts/fleet_files.py`; the paired GComs `docs/FLEET_FILES.md` owns the campaign,
resource limits, isolated deployment, evidence format and cleanup instructions.
The builder snapshots both repositories and leaves registry manifests and
canonical lockfiles untouched.

`GCHAT_FILE_DIAGNOSTICS=1` emits five-second local aggregate observations on
stderr: verified/rejected pieces, received blocks/bytes, retry counts, send failures
and timeouts, payload buffers, pending work and reserved cache bytes. Received
bytes are still unverified ciphertext until a whole piece passes verification.
It emits no member, route or share identifiers. Counts reset
with the engine; PID and time identify each observation interval. Diagnostic
write failure does not fail a transfer. Ordinary application behavior is unchanged
when the environment variable is absent. Embedded runtimes also include a
`protocol` aggregate: admitted/dispatched/failed work, queue and service latency
histograms, warmup latency and scheduler resource use. This distinguishes a file
worker timeout from stalled relay admission. No node handle is retained by the
blocking file worker for these observations; attached IPC-only runtimes report
`protocol: null`. Counters may omit work before diagnostics were enabled.

For an operator-controlled daemon, `GCHAT_PROTOCOL_METRICS=<private-file>` also
enables GComs' existing bounded local JSONL metrics writer. The fleet worker sets
this to a file inside its private test volume. These diagnostics help distinguish
channel admission and routing failures from file-engine failures. Review the raw
logs before sharing them. The probe preserves a failed typed submission's original
error through the retained v2 response using the same admitted operation ID; it
does not retry the command under a new identity.

The file worker continues consuming incoming events while up to four sends await
receipts. It also waits for transient session-lock contention instead of dropping
an already received block. A local regression holds outgoing receipts after the
peer receives its requests and requires a real encrypted-channel import/download
to complete before those receipts are released; shutdown must cancel held sends.
