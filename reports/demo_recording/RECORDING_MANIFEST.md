# VARUNA Demo Recording Manifest

## Production summary

- Recording date: 2026-10-14 (Asia/Kolkata)
- Source application: `http://localhost:8888`
- Method: Playwright-controlled Chromium, recording the live dashboard and Chromium's native PDF viewer. Computer Use was not exposed in the session.
- Delivery format: silent H.264/AVC MP4, 1920 × 1080, 30 fps, progressive, yuv420p.
- Source capture format: 1920 × 1080 VP9 WebM at 25 fps; delivery clips were conformed to 30 fps with FFmpeg.
- Delivered source-clip duration: 182.67 seconds (03:02.67).
- Rough-cut duration: 182.67 seconds (03:02.67).
- Rough-cut assembly: clean cuts in numerical clip order; no narration, music, titles, overlays, or artificial footage.
- Verification: every MP4 and the rough cut decoded fully without errors. Representative final-frame evidence is in `verification/final_frames/`; contact sheets are in `verification/contact_sheets/`.

## Clip inventory

### 01 — Dashboard Introduction

- Filename: `01_dashboard_intro.mp4`
- Duration: 00:12.00
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: VARUNA identity, Trishuli River Basin case-study header, Sentinel-1 comparison map, telemetry, navigation, legend, and analysis panel.
- UI actions: smooth pointer movement across the brand, main map, and contextual analysis panel; no disruptive navigation.
- Important visible information: Sentinel-1 C-SAR, Orbit 19 descending, August 24 / September 5 comparison dates, 10-day post-event lag note.
- Errors or missing features: none.
- Suggested narration topics: product purpose; real Earth-observation workflow; study location and event date.
- Recommended usable range: 00:00.50–00:11.50.

### 02 — Satellite Comparison

- Filename: `02_satellite_comparison.mp4`
- Duration: 00:28.97
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: authentic pre-event and post-event Sentinel-1 SAR rasters dated August 24 and September 5, 2026; comparison legend; authentic blue/orange change layer.
- UI actions: dragged the live comparison divider to approximately 20%, 50%, and 80% with pauses; enabled `Highlight Changes`; increased the application's own overlay opacity control to 75% for legibility; moved the divider again to reveal the overlay.
- Important visible information: blue candidate floodwater / radar-backscatter decrease; orange candidate debris or surface-change / backscatter increase; candidate-change legend and scientific caveats remain visible.
- Errors or missing features: none. The opacity adjustment changes only display transparency, not underlying imagery, classification, or statistics.
- Suggested narration topics: before/after acquisition timing; radar backscatter interpretation; candidate changes versus verified damage.
- Recommended usable range: 00:01.00–00:28.20.

### 03 — Surface Change Analysis

- Filename: `03_surface_change.mp4`
- Duration: 00:25.00
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: classified change raster, floodwater and debris/scour classes, legend, raw baseline statistics, and scientific caveats.
- UI actions: opened Surface Change; highlighted the two main metric cards; switched through Water, Debris, and back to the combined Hazard classification.
- Important visible information: raw candidate floodwater 126.60 km²; raw candidate debris/scour 108.21 km²; permanent-water and unchanged-surface context.
- Errors or missing features: none. Values shown are the live UI's raw 10 m baseline figures, not filtered MMU figures.
- Suggested narration topics: threshold-based classification; raw versus filtered morphology; terrain-speckle and 10-day-lag limitations.
- Recommended usable range: 00:01.00–00:24.50.

### 04 — Infrastructure Exposure

- Filename: `04_infrastructure_exposure.mp4`
- Duration: 00:25.00
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: exposed road and building overlays, Pasang Lhamu Highway, cluster/point symbology, cross-tabulation, and exposure caveat.
- UI actions: opened Infrastructure Exposure; highlighted the building and road metrics; changed the sector from the corridor to Bidur; zoomed once to improve infrastructure detail; held on the legend.
- Important visible information: 1,062 potentially exposed buildings; 35.12 km potentially exposed roads; 9.62 km highway intersection; 936 / 2,813 destroyed-building spatial overlap.
- Errors or missing features: no dedicated settlement-isolation graph/map is exposed in this workspace. The six-settlement modeled-connectivity result is instead captured in the genuine Copilot response and report scenes; it is presented as hypothetical, not confirmed physical isolation.
- Suggested narration topics: spatial intersection screening; unique asset counting; potential exposure versus confirmed damage; modeled access assumptions.
- Recommended usable range: 00:01.00–00:24.50.

### 05 — Independent Reference Validation

- Filename: `05_reference_validation.mp4`
- Duration: 00:22.00
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: Copernicus EMSR927 event footprint, SAR inundation/debris capture layers, Bidur overlap table, and the non-accuracy caveat.
- UI actions: opened Reference Validation; highlighted 37.16%; held on the validation legend; toggled the real SAR underlay for context; highlighted the accuracy-interpretation warning.
- Important visible information: Bidur observed-event spatial coincidence 37.16%; inundation capture 26.89%; debris/scour capture 10.28%; 100% spatial coverage.
- Errors or missing features: none. The UI explicitly states that 37.16% is time-offset spatial coincidence, not precision, recall, F1, or overall classifier accuracy.
- Suggested narration topics: independent Copernicus reference; time-offset comparison; why coincidence is not model accuracy.
- Recommended usable range: 00:01.00–00:21.50.

### 06 — Situation Copilot

- Filename: `06_situation_copilot.mp4`
- Duration: 00:25.00
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: real Situation-Report Copilot interface, exact requested English question, grounded English answer, Nepali mode, Nepali road-exposure question, and grounded Nepali answer.
- UI actions: typed `How much road infrastructure intersects the detected hazard areas?`; clicked Ask; waited for the complete response; switched to Nepali; selected the genuine road-exposure prompt; waited for the complete response.
- Important visible information: 35.12 km of 260.71 km road network; 9.62 km Pasang Lhamu Highway exposure; zero double-counting; six candidate isolated settlements; explicit potential-exposure and hypothetical-closure caveats.
- Errors or missing features: none. Responses were rendered by the application's real grounded query path; no static text was injected.
- Suggested narration topics: evidence-grounded operational Q&A; bilingual access; anti-hallucination constraints; hypothetical connectivity modeling.
- Recommended usable range: 00:01.20–00:24.50.

### 07 — Operational Situation Report

- Filename: `07_situation_report.mp4`
- Duration: 00:16.83
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: the actual `SITUATION_REPORT_NEPAL_2026.pdf` in Chromium's PDF viewer, framed at 100% with title, overview, metrics, map, independent-reference check, infrastructure findings, and operational constraints.
- UI actions: clicked the dashboard's actual `SitRep (PDF)` button; allowed the real PDF to open; moved deliberately across title, metrics/map, and findings.
- Important visible information: 126.60 km² candidate floodwater; 108.21 km² candidate debris/scour; 1,062 buildings; 35.12 km roads; 37.16% Bidur spatial coincidence.
- Errors or missing features: none. Verified with `pdfinfo`: exactly 1 A4 page.
- Suggested narration topics: concise operational synthesis; principal findings; decision-use limitations.
- Recommended usable range: 00:01.00–00:16.50.

### 08 — Scientific Research Report

- Filename: `08_research_report.mp4`
- Duration: 00:17.87
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: the dashboard-linked `VARUNA_Research_Paper_FINAL.pdf` in Chromium's PDF viewer. Page 1 shows title/abstract and study context; page 2 shows radar preprocessing, classification methodology, pre/post figure, and results; page 3 shows change classification and independent EMSR927 validation; page 4 shows infrastructure exposure, limitations, reproducibility, and conclusion.
- UI actions: clicked the dashboard's actual `Research Report (PDF)` button; deliberately selected PDF pages 1, 2, 3, and 4 in sequence.
- Important visible information: methodology, Sentinel-1 processing, 126.60 / 108.21 km² results, 37.16% Bidur coincidence, infrastructure figures, limitations, and conclusions.
- Errors or missing features: the first take ignored keyboard paging; it was rejected and recaptured using real PDF thumbnail clicks. The delivered clip contains all four pages. Verified with `pdfinfo`: 4 A4 pages, within the six-page limit.
- Suggested narration topics: reproducible scientific method; independent validation; limits of time-offset SAR screening; conclusions.
- Recommended usable range: 00:01.00–00:17.60.

### 09 — Closing Application Shot

- Filename: `09_closing_dashboard.mp4`
- Duration: 00:10.00
- Technical: 1920 × 1080, 30 fps, H.264 High, silent
- Shown: clean, stable Satellite Comparison view with the authentic Highlight Changes layer enabled and the pre/post divider centered near 38%.
- UI actions: enabled Highlight Changes; slowly repositioned the comparison divider; held the final frame.
- Important visible information: VARUNA identity, August 24 / September 5 scenes, SAR telemetry, candidate-change legend.
- Errors or missing features: none.
- Suggested narration topics: closing product value; transition to final logo in later editing.
- Recommended usable range: 00:00.50–00:09.50.

## Rough-cut timeline

| Rough-cut range | Clip |
|---|---|
| 00:00.00–00:12.00 | Dashboard Introduction |
| 00:12.00–00:40.97 | Satellite Comparison |
| 00:40.97–01:05.97 | Surface Change Analysis |
| 01:05.97–01:30.97 | Infrastructure Exposure |
| 01:30.97–01:52.97 | Independent Reference Validation |
| 01:52.97–02:17.97 | Situation Copilot |
| 02:17.97–02:34.80 | Operational Situation Report |
| 02:34.80–02:52.67 | Scientific Research Report |
| 02:52.67–03:02.67 | Closing Application Shot |

## Final verification record

- Nine numbered MP4 clips exist and fully decode.
- `VARUNA_RAW_DEMO.mp4` exists, fully decodes, and contains one 1920 × 1080 H.264 video stream at 30 fps with no audio stream.
- The comparison divider visibly reaches the requested approximate 20%, 50%, and 80% positions before Highlight Changes is enabled.
- The authentic blue/orange change layer is visible at 75% display opacity in Clip 02; no imagery or statistics were altered.
- The Copilot clip contains the exact English question, completed grounded answer, and completed Nepali response.
- The one-page SitRep is present in Clip 07.
- The four-page linked scientific paper is present in Clip 08, including methodology, validation, limitations, and conclusion.
- Final MP4 frames and source contact sheets were visually inspected.
