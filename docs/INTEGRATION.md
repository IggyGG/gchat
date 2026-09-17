# Integrating with GChat

`gchat-api` contains the shared service contract. Its generated Rust client and
TypeScript API are examples of GComs typed RPC, not an invitation to depend on
GChat's internal store or UI implementation.

GChat core owns the encrypted protocol profile, encrypted chat archive, lifecycle
and operation journal. A UI identifies an instance before sending requests and
pins that instance for its attachment. Unlock and disconnect are lifecycle actions;
query and operation routes are bound to the selected service.

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
