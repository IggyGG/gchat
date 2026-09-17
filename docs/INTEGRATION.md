# Integrating with GChat

`gchat-api` contains the shared service contract. Its generated Rust client and
TypeScript API are examples of GComs typed RPC, not an invitation to depend on
GChat's internal store or UI implementation.

GChat core owns the encrypted protocol profile, encrypted chat archive, lifecycle
and operation journal. A UI identifies an instance before sending requests and
pins that instance for its attachment. Unlock and disconnect are lifecycle actions;
query and operation routes are bound to the selected service.

The separated GComs repository is the protocol source of truth. Do not reconnect
GChat to the original private `gc-*` workspace to pick up transport changes. Keep
the `gcoms-*` registry dependencies in this application's manifests and validate
current-source development from GComs with:

```sh
python3 scripts/check-gchat.py --gchat /path/to/gchat --offline
```

That runner snapshots both repositories and applies temporary GComs source overrides.
Cargo may update the snapshot's lockfile without changing this repository's lockfiles.
It reports both source hashes and revisions and detects changes during the check. Actual
package-archive validation remains a separate distribution gate. The GC/2 protocol
implementation and qualification ledger lives in GComs; repository consolidation
alone does not change chat archives or the implemented GC/1 wire profile.

Use `ui/scripts/generate-rpc.mjs` after exporting the Rust schema with `gchat-types`.
The build-time import is `@gcoms/rpc-codegen`; the browser runtime is `@gcoms/rpc`.
Rebuild and check generated files after changing the contract. Wide integers use
lossless wire forms. Never hand-edit generated validators to accept a new shape.

Browser bridges authenticate the browser session and pin a local service endpoint.
Tauri passes through its native command bridge. Neither accepts arbitrary upstream
URLs, sockets or asserted caller identity from browser JSON. Addons should expose
their own namespaced GComs service and explicit grants instead of adding private
host operations to chat's parser.

Operation handles survive lost replies and reconnect. Resume the same handle;
`outcome_unknown` requires reconciliation. Local message acceptance is not proof of
remote display or application completion. Preserve this distinction in new UIs.
