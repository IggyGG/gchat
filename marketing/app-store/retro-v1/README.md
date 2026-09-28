# GChat Apple App Store creative pack

GCHAT-STORE-2, 2026-09-29. The same “Old-school chat. Your people.” direction as
the Google Play pack, adapted to iPhone and iPad. Open `index.html` to review all
eight images. `listing.json` is the exact English (US) metadata; `listing.md` is
its readable copy. All eight images are uploaded and processed, and the refreshed
metadata and screenshot order are verified in the iOS draft. The final App Store
Connect receipt is `publication.json`.

## Assets

| Set | Output | App Store Connect display type |
| --- | --- | --- |
| iPhone | Four 1290 × 2796 JPEGs | `APP_IPHONE_67` |
| iPad | Four 2048 × 2732 JPEGs | `APP_IPAD_PRO_3GEN_129` |

Both sets use the existing App Store Connect screenshot slots. All exports are
opaque RGB images, ordered conversation → channels → files → invitations.
Dimensions follow [Apple's screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications).
Apple has no Play-style feature-graphic slot in this listing; only the eight
screenshots and supported metadata fields are updated.

The shared Svelte UI is captured in WebKit using synthetic conversations and
touch/mobile contexts. These are browser captures, not native device screenshots.
Source: `3d58012b08354181b3d72f30ba9b14060d3b48fe`. The iPhone view is 380 × 760
at 3×; the iPad view is 936 × 1000 at 2×. The artwork keeps the capture proportions
and puts marketing text outside the app frame. No app components or styles are
modified. Capture files live in `source/`, finished images in `exports/`.

The original generated background and its exact imagegen prompt are reused from
[`../../play-store/retro-v1/`](../../play-store/retro-v1/README.md). No new AI image
was generated. The editable layout is `artboards.html`; Fixedsys uses the
application's existing font and licensing.

## Reproduction and validation

Install the repository's existing npm dependencies and Playwright WebKit/Chromium
browsers, then start the local fixture:

```sh
node ui/browser/server.mjs
# In another terminal, with TMPDIR on SSD on the Linux workstation:
node marketing/app-store/retro-v1/export.mjs
```

`PW_DIR` can point to an existing `node_modules` containing Playwright. This run
used Playwright 1.62.1's installed WebKit. No dependency was added. Linux preview
checks used a private SSD temporary directory; the disposable directory was
removed after use. Existing workstation jobs and temporary files were preserved.

The exporter checks decodable images, layout bounds, text/frame overlap, capture
overflow and browser exceptions. `validation.json` also records the preview
checks at 1440, 768 and 375 pixels. Verify encoding/dimensions and run
`node --check marketing/app-store/retro-v1/export.mjs`,
`python3 scripts/check-source.py` and `git diff --check` before publication.
Checks passed: exporter syntax, source policy (656 paths), whitespace and all
eight local SHA-256/MD5 hashes against the upload receipt.
Code comparison: `codematch=unreachable` (no tool exposed in this session).

## App Store Connect update

Target: app `6814308446`, iOS version `1.0`, locale `en-US`. The original name,
subtitle, version text, screenshot metadata and screenshot images are backed up
in the release service under `/state/marketing/apple-store-retro-20260929/`.
Local retained evidence is `test-evidence/apple-store-retro-upload/`.
Credentials remain in the existing release service and are not copied here.

Each screenshot was reserved, uploaded using Apple's returned upload operations,
then committed with its original MD5. Apple must report `COMPLETE` before the
old draft screenshot is removed. The receipt records file sizes, dimensions,
SHA-256 values and screenshot order. The final processing readback provided
matching MD5 checksums for all eight images; intermediate responses may omit
that field. Upload procedure: [Apple asset upload documentation](https://developer.apple.com/documentation/appstoreconnectapi/uploading-assets-to-app-store-connect).

The metadata update includes name, subtitle, description, promotional text and
keywords. Support/privacy URLs, icon, binaries and release settings are preserved.
No build is attached to the iOS draft, and its encryption declaration is
`IN_REVIEW`. The release workflow must supply a qualified build and obtain
encryption approval before review submission/publication. Updating these listing
assets does not qualify an iOS binary or bypass those release gates.
