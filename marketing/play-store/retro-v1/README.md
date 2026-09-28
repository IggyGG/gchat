# GChat Play Store creative pack — retro v1

GCHAT-STORE-1, 2026-09-29. Review the complete pack in `index.html`.

The direction is **Old-school chat. Your people.** It leads with the actual
conversation experience, then channels, shared files and invitations. The pixel
art, navy background and mint highlights support the existing Fixedsys chat
interface. Production application code and the public website are unchanged.

## Deliverables

- `exports/feature.png`: 1024 × 500 opaque feature graphic.
- `exports/01-conversation.jpg` through `04-invitation.jpg`: four 1080 × 1920
  phone listing images; real shared UI with clearly identified sample content.
- `index.html`: responsive local review page with full-resolution image links.
- `listing.md`: proposed name, short/full description, alt text, upload order,
  native parity requirement, and measurement plan.
- `artboards.html`: editable HTML/CSS artwork masters, with text kept separate
  from both generated artwork and app captures.
- `source/`: original live listing captures, new browser fixture captures,
  artwork, and provenance. `prompts.md` records the exact artwork prompt.
- `validation.json`: render dimensions, browser errors and capture provenance.

## Reproduce

Use the project's existing npm dependencies (`npm ci --ignore-scripts` where
needed). No dependency is added. Start the existing browser fixture server in
one terminal, then render the small asset set in another:

```sh
node ui/browser/server.mjs
node marketing/play-store/retro-v1/export.mjs
```

The fixture uses loopback port 1428 and synthetic messages; it does not join a
real network or read an identity/archive. The renderer uses existing fixture
methods and the app's buttons, without changing the component or its CSS.
It captures the 450 × 730 browser view at 2× and places it at 900 × 1460 in each
portrait. The script exits unsuccessfully on browser exceptions, horizontal
capture overflow, missing images or incorrect artboard dimensions. Review the
images visually after changing the copy. The native Android screen match is a
separate check and is intentionally recorded as unverified.

For a shareable local review, serve the repository with
`python3 -m http.server 8080 --bind 127.0.0.1`, then open
`http://127.0.0.1:8080/marketing/play-store/retro-v1/`.

## Artwork provenance

The built-in imagegen tool created `source/pixel-night.webp`. Its original
1536 × 1024 PNG was encoded to WebP at quality 91 with ImageMagick for repository
size; its composition is unchanged. Original generation is retained in the
session's generated-images directory. The artwork contains no text or UI.
All visible app text and controls come from the real Svelte components. Fixedsys
comes from the project's existing font, with its existing licensing.

`source/provenance.json` records the public listing sources and capture revision.
No private conversations, real invitations or credentials are included.

## Validation scope

This is a marketing-only change. Run `node --check` on the renderer, render the
assets, inspect the gallery at desktop/mobile widths, check exported image
dimensions/formats and run `python3 scripts/check-source.py`. Application/native
release gates are unchanged. The workstation batch runner was attempted but
failed before execution because its sudo setup required interactive authentication;
the small browser capture/export was run directly. No compilation or heavy test
workload was started. Code comparison: `codematch=unreachable` (the tool is not
exposed in this session).
