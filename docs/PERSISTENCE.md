# Protocol persistence costs and barriers

The encrypted protocol profile is distinct from the chat archive and the file
engine's durable pieces/journal. Saving one does not make the others durable.
`ProtocolRuntime::save` asks the node to export its complete retained state. The
installed sink serializes and encrypts that export, writes and syncs a temporary
file, replaces the profile, then syncs the parent directory on Unix.

## Event audit

This review uses GChat `200cd7a` and the GComs runtime in `d6f5d97` (also present
in the paired fleet-files checkout). Event names alone are not a general promise
that every mutation preceding the event has already been committed.

| Event / operation | Persistence finding |
| --- | --- |
| Direct message, direct delivery, volatile application | Native direct receive/ACK paths commit ratchet and receipt state before emitting. Volatile bodies are deliberately excluded from retained state. |
| Channel message and channel delivery | Native MLS message and ACK paths commit before emitting; failed commits suppress these events. |
| Channel roster change | Some producers, including join and received MLS membership commits, emit before the GChat wrapper save. Retain a barrier before hosted subscribers observe them. |
| Channel removed | The removal path attempts a native save but still emits after a save error. The hosted barrier must remain fallible; never publish a failed event as durable. |
| Identity/session changes | Owner/session transactions have their own commits, but public identity refresh and alternate producers must be audited together. Retain the event barrier. |
| Presence changes | Observed presence and replay counters are RAM-only and reset on restore; opt-in policy is retained. Do not confuse observation events with policy commits. |
| Channel-direct text and delivery | `seen_direct` and pending direct receipts are RAM-only, omitted from protocol exports. Chat-body durability belongs to the separate archive. |
| File-piece channel-direct events | The piece disposition changes no exported per-piece protocol state. The file engine verifies and retains pieces itself. It consumes the embedded event stream, independent of hosted profile persistence. |
| Lag notifications | Not state mutations, and saving cannot recreate dropped events. Preserve explicit lag reporting and fail-closed delivery behavior. |
| Explicit API calls, periodic save, shutdown | These also cover mutations without an event or before a method returns. They require independent review before removal. |

The audit follows node `direct.rs`, `gc2_direct.rs`, `channels.rs`,
`channel_direct.rs`, `presence.rs`, `routing.rs`, and the actual export/restore
fields in `persist.rs`. An in-memory mutation does not automatically imply that
the protocol profile serializes it. Conversely, a prior ratchet commit does not
prove that later membership or policy mutations are durable.

The normal UI already subscribes to `ClientHandle`'s archive event bus. The
protocol-write multiplier is per `ProtocolClient` SDK subscriber, not necessarily
per attached UI. The file worker subscribes directly to the embedded stream.
Every outgoing file application still traverses the explicit
`ProtocolClient::send_channel_direct` save; that is a separate optimization lead.

## Instrumentation and baseline

`ProtocolRuntime::persistence_diagnostics()` returns process-local aggregate
counts by save caller and event class, plus actual encrypted-store costs. It
records no paths, identities, message IDs or payloads. Existing opt-in
`GCHAT_FILE_DIAGNOSTICS=1` output includes these values as `persistence`.

Store counters distinguish attempted and completed replacements, failures,
serialized bytes, bytes offered to atomic write and successfully committed
bytes. Timings include lock wait, serialization, encryption, the complete atomic
write and total save time. They do not measure device write amplification or
individual fsync syscalls. Runtime call time additionally includes node export
and command/lock waits. A canceled or in-flight request may have no completion;
concurrent snapshots are observational counters, not durability receipts.

An instrumented baseline injected one event through the existing background and
SDK forwarding paths while using the real encrypted profile sink:

| SDK subscribers | Completed profile replacements | Bytes committed |
| ---: | ---: | ---: |
| 0 | 1 | 22,984 |
| 1 | 2 | 45,968 |
| 4 | 5 | 114,920 |

This establishes duplicate writes in the small local fixture, not an end-to-end
file-throughput improvement. Baseline source hashes, timings and output are
retained in the paired GComs checkout's
`target/protocol-plan-persistence-baseline-01.log` and
`target/gchat-source-check/reports/test-gc-chat-ldoskyui.json`.

The next optimization consolidates subscriber barriers at the event publisher:
save once, then distribute that event. It must preserve every event class,
failed-save refusal, bounded queues and lag notifications, reserved-component
filtering, cancellation, immediate profile reopening, explicit API saves,
periodic checkpoints, and the final shutdown save. No debounce interval or
wire/cover setting is required. Skipping individual event classes or outgoing
file saves is a separate change requiring corresponding recovery evidence.
