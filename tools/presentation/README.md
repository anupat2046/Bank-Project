# Project presentation

The published PowerPoint and PDF are in [`output/presentation`](../../output/presentation/).
The current deck contains 16 main slides and 8 appendix slides. For a 12-minute talk,
use selected findings rather than reading every slide in full.

## Build

Requires Node.js and npm:

```sh
cd tools/presentation
npm ci
npm run build
node lib/clean_content_types.js ../../output/presentation/Thailand-Regional-Banking-Intelligence.pptx
```

The builder reads recorded CQ results from `docs/evidence/competency-results.json`.
Screenshots in `assets/`, narrative claims, dates, and validation counts need manual
review when the underlying application or evidence changes.

Export the PDF on Windows with Microsoft PowerPoint installed:

```powershell
./export_pdf.ps1 ../../output/presentation/Thailand-Regional-Banking-Intelligence.pptx
```

The export replaces the PDF at the destination. Keep an earlier copy if needed.
Review the exported slides for Thai text, chart labels, clipping, and source periods.

## Architecture diagrams

`architecture.js`, `architecture_lowlevel.js` and `data_flow.js` generate the SVG and
PNG diagrams under `docs/design/` (high-level and low-level architecture, and data
flow/lineage). They share `lib/render.js`, which requires the frontend's installed
`playwright-core` dependency and a Chromium browser. Set `CHROME_PATH` to a browser
executable if automatic discovery does not find one.

```sh
node architecture.js
node architecture_lowlevel.js
node data_flow.js
```

Rules, counts and names in the diagrams are written into the scripts; update them when
`bank/`, `compose.yaml` or the recorded warehouse counts change.

The package-cleanup utility removes orphaned content-type declarations only.
It preserves every other ZIP entry byte-for-byte and does not edit slide content.
