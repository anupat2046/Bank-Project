# Narrated walkthrough verification — 24 October 2026

**Status: encoded media verified; final MP4 included in this repository.**

This record covers the narrated English walkthrough with Thai sentence subtitles, built from actual application recordings and verified screenshots captured on **24 October 2026 (Asia/Bangkok)**. See the [feature catalogue](../demo.md) and [application verification scope](../verification.md) for separate evidence.

## Composition and recorded scope

| Item | Recorded specification |
| --- | --- |
| Renderer | HyperFrames **0.8.192** |
| Timeline | **30 scenes**, grouped into **12 chapters** |
| Timeline duration | **280.1 seconds** — 4 minutes 40.1 seconds |
| Visual sources | **69 distinct captured interface states**, including material from **seven source recording files** and verified screenshots |
| Picture | 1920 × 1080, 30 fps; H.264 video and AAC narration |
| Narration | English; locally generated **Kokoro `af_heart`**, approved by the user |
| Subtitles | Thai sentence translations, up to two lines, outside the application viewport |

The initial hosted voice-generation request was refused; the user then selected local synthesis. No account identifiers or credentials are included in the delivery materials.

The chapters follow the analytical workflow: business context, overview controls, province details, comparison, screening, AI analysis, AI conversation, ten business questions, sources, Grafana, Airflow, and mobile/conclusion. Reading holds and close views make selected results inspectable; the film does not reproduce every application action in real time.

The recorded warehouse snapshot contains **77 provinces × 25 months = 1,925 province-month rows**, July 2024–July 2026. The walkthrough's assistant session uses Groq; narration synthesis is a separate media-production step.

## Visual evidence corrections

Review identified cases where the original framing or filename did not support its intended label. The composition was revised using actual interface states:

| Finding | Correction and evidence boundary |
| --- | --- |
| Scatter views cropped out the plotted evidence | Dedicated views retain plotted points and the selected/all-province scope, including Bangkok exclusion. |
| A supposed zero-result screenshot showed seven matches and an invalid numeric-step tooltip | Replaced with successfully submitted, step-valid criteria and a visible zero-result state. Invalid input is not presented as an empty query result. |
| A file named as historical empty evidence actually showed populated CQ10 results | Replaced with CQ01's actual insufficient-paired-history state for July 2024. |
| ETL history records were below the captured viewport | Dedicated expanded-history evidence shows recorded outcomes, row counts, and timestamps. |
| The coverage panel was clipped | Complete coverage evidence preserves GPP, population, and inflation availability counts and their explanation. |
| Formula and query details were collapsed, too small, or outside the crop | Dedicated detail views expose the relevant method and query sections. The new SQL view shows the **query prefix and complete parameters**, with horizontal scrolling available; it does not show every SQL character simultaneously. |

The visual review also checked Thai glyphs and line bounds, readable result headings, both CQ05 charts, the relation between assistant questions and results, and portrait-view proportions inside the landscape mobile chapter. Corrected source states must remain visible in the encoded delivery; HTML or screenshot inspection alone cannot establish that.

## Verification status

| Check | Status | Scope |
| --- | --- | --- |
| Draft HyperFrames check | **Passed: 0 errors reported** | Latest draft check following identification and correction of visual defects; not final encoded-video approval |
| Storyboard and review-sheet inspection | **Completed for the draft** | Scene flow, caption placement, selected close views, and evidence-label consistency |
| Final composition check | **Passed: 0 errors** | Browser ran; runtime, layout, motion, contrast and craft audits reported no findings at 30 sampled times. Twelve timeline-density warnings retain contiguous evidence shots within their narration scenes. |
| Final MP4 render | **Passed** | Complete 8,403-frame HyperFrames render; the corrected nine-second index-chart scene was rendered separately in HyperFrames and integrated at the same frame boundaries while retaining the master narration. |
| Encoded duration, streams, and complete decode | **Passed** | Video timeline 280.1 seconds; MP4 container 280.2 seconds. H.264 1920 × 1080 at 30 fps, AAC audio, optional English subtitle track and 12 chapters. All audio/video packets decoded without reported errors. |
| Decoded delivery-frame review | **Passed for the inspected samples** | 82 proof frames across all displayed proof shots and recording inserts; seven contact sheets, plus full-size checks covering every CQ, corrected states, Thai captions and mobile views. The final index chart includes both complete series, axes and legend. |
| Audio measurements | **Passed for numerical checks** | Measured integrated loudness −17.88 LUFS, true peak −1.69 dBTP, LRA 7 LU. Thirty English sentence clips total 198.23 seconds of speech; reading holds contain intentional silence, longest measured gap about 13.88 seconds. No listening review is claimed. |
| Listening review | **Not performed** | Sound quality and pronunciation are not established by numerical measurements |
| Repository delivery | **Versioned MP4** | [Open or download the film](../media/bank-intelligence-walkthrough-en-th.mp4); the final video and caption sidecars are stored directly in this repository. No HyperFrames-hosted publication is used. |

## Limits retained in the walkthrough

- A terse population-filter follow-up after a multi-metric question can still produce generic clarification. Restating the metric and threshold explicitly worked in the recorded flow; this limitation remains open.
- Source availability differs by vintage. Historical inflation remains unavailable in this snapshot under the documented timing rules; missing values are not treated as zero or filled using future information.
- Selected demonstrations and visual checks do not constitute an exhaustive application feature test, accessibility assessment, or live LLM accuracy evaluation.
- Airflow shows actual run history and a selected successful run. This does not establish a month of uninterrupted daily scheduling; ETL records and scheduler continuity are different evidence.
- The snapshot and recording dates describe the captured system. They do not establish current upstream freshness, current service health, or production-readiness.

The final composition checks are complemented by scene, transition and phone-size review sheets. Twelve additional corrected-shot snapshots include all seven source-recording inserts and the month selector, calculation method, actual zero-match result and SQL/parameters panel. After a complete FFmpeg build replaced a limited build without the required frame-selection filter, all recording inserts appeared in those snapshots without extraction warnings. Encoded-file checks are reported separately in the verification table above.

The index-trend crop was the only remaining defect found in the initial encoded-frame review. A fresh actual deposit-index panel for Chiang Mai and Chon Buri replaced it. Frames 1,227–1,496 were regenerated from the same HyperFrames scene; the surrounding video and original narration timing were retained, then complete decode, media measurements and proof-frame extraction were repeated. Frame 48.4 seconds in the corrected MP4 shows the full graph and legend.
