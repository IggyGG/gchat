# Production release policy

On 2026-09-20 the owner selected production rollout and removed statistical privacy thresholds and mandatory 24-hour campaigns as release gates. Releases use bounded delivery, authentication, persistence/reopen, artifact-signature and rollback checks. Reuse source-bound completed checks for unchanged code; extended research and soak campaigns run separately and never impose a minimum release duration. Failed historical evidence stays failed.

Linux is the current released desktop platform. macOS, Windows and mobile application delivery is now in progress, with separate native and installed-app checks before publishing each target. See CROSS_PLATFORM.md. Gh0st signs desktop artifacts with pinned release keys; self-signed distribution does not imply public-CA certification or Apple notarization.

## Privacy improvements still outstanding

Production status does not mean traffic-analysis resistance is qualified. The four profile-22 comparisons (idle/chat and matched bulk/mixed, for time windows and connection observations) are improvement targets, not release vetoes. Existing unfavorable/calibration reports remain retained. Further work includes reducing observable activity and volume differences, establishing repeatable whole-client measurements across startup, DNS/HTTPS bootstrap, protected catalog access, reconnect/reopen and connection lifetimes, and measuring adverse-link behavior without pooled-relay substitutions. No <=0.55 claim is made.

## Data and protocol selection

GC/2 uses profile 22 explicitly. Start the desktop with `gchat-desktop --gc2-carrier`; use a separate `--home` for an existing legacy installation. Existing legacy profiles are not silently converted, reset or overwritten. Authentication, exact retained outboxes, signed capabilities and expiry checks remain enforced. The production relays retain their identity/TLS keys; current bootstrap credentials are generated from those identities, never converted from legacy authority.

## Receipt scope

Production executables are bound to GComs 726172785baacc25781d427c75faada5f8849d6b and GChat 0b599cfaa880828b5b0a04c99467c5616afc5b2c. Later policy/documentation/tooling commits do not relabel the frozen native CI or artifact source. The original signing receipt calls its trust policy `self-signed-preview`; the key and signed bytes are unchanged, while this owner decision changes deployment status to production.

## 0.1.1 desktop startup correction

Automatic desktop listening previously passed a wildcard bind address into relay metadata, rejecting first unlock with `unusable relay address`. The companion Node now resolves a concrete candidate before attaching the service. Offline startup keeps an unpublished loopback candidate; only independent reachability verification can publish it. The bound listener, identity, protected routing and address validation are preserved. Creation and retained reopen are checked using the desktop default `0.0.0.0:0` configuration. A profile created before the failed startup must be reopened, not replaced.

## 0.1.2 workspace refinement

The desktop keeps one application header with the selected conversation, Network, Help and user/file counters. Join/Create move to the channel list footer; Users and Files share an initially closed panel. The composer has a paperclip and no self-nickname. `/font [fixedsys|readable]` and `/find [text]` are view-local commands, documented with existing `/lock` and `/disconnect` in Help. Native window decorations and the default IRC font remain.

First network setup is required before the desktop workspace becomes available. Only service-confirmed invitation import or authenticated retained configuration satisfies setup; browser storage cannot grant access. Established profiles retain their workspace while reconnecting or replacing an invitation. This is onboarding presentation, not a replacement for protocol authentication. The invitation text is cleared on submit/dismissal. The single status indicator distinguishes local service availability from the actual network state.

File operations belong to the unlocked attachment rather than the visible Files panel. Closing a panel or changing conversations keeps the original import ID/destination. Locking the view stops further import writes without claiming cancellation of an already submitted operation; retained imports remain available for explicit resume. No protocol, cryptography, daemon or relay behavior changes in this release.

UI validation: `npm run check`, `npm test`, and `npm run test:browser -w @gchat/ui`. Install the pinned Chromium test browser with `npm exec -w @gchat/ui -- playwright install chromium`. Browser fixtures are loopback-only, use synthetic profiles/transport, and are excluded from the production frontend entrypoint. They cover invitation rejection/acceptance, retained offline access, commands, focus and panels, import continuity and responsive layouts. Native Linux CI includes this suite before producing signed packages.
