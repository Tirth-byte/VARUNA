# VARUNA — Final Video Review and Submission Quality Audit

**Audited file:** `/Users/macbookair/Desktop/VARUNA.mp4`  
**Audit date:** 14 October 2026  
**Verdict:** **NOT READY**  
**Internal score:** **68/100**

## Executive verdict

The video presents a credible, visually polished, scientifically cautious demo. It successfully shows authentic before/after Sentinel-1 imagery, candidate change mapping, infrastructure intersections, modeled isolation, EMSR927 comparison, a bilingual copilot, and both required reports. Its strongest feature is responsible language: candidate detections and hypothetical road closures are not presented as confirmed destruction.

It is nevertheless **not submission-ready** because its exact duration is **03:49.600**, exceeding the Track B three-minute requirement by **49.600 seconds**. The video also leaves several mandatory capabilities implicit or absent: user-selected area/date, bridge exposure, explicit nearest-town/hospital reachability proof, pre-event OSM timing, raw-versus-filtered results, attribution, and reproducibility. A focused recut can correct these issues without remaking the demonstration.

## Review method and technical specifications

- Complete file decoded: all **6,888 frames** were read from first to last without a decode failure.
- Visual method: systematic frame extraction every **2.0 seconds** across the full runtime (116 frames), contact-sheet inspection, and transition-focused inspection. This was **not** a claim of continuous human-style playback.
- Audio method: the complete AAC track was extracted to 16 kHz mono PCM, signal-analyzed, and transcribed with timestamped `faster-whisper small.en` output.
- Evidence checked: original `Track B.pdf`; source code; experiment provenance and result JSON; README; scientific lineage/release/compliance documents; the actual SitRep and research PDFs.

| Property | Observed value |
|---|---|
| Container | MP4 (`isom`) |
| Duration | **229.600 s / 03:49.600** |
| Video | H.264/AVC, 1920×1080, progressive, yuv420p, BT.709 |
| Frame rate | Constant 30 fps |
| Video frames | 6,888 |
| Video bitrate | ~15.85 Mb/s |
| Audio | AAC, stereo, 48 kHz, ~192 kb/s |
| File size | 460,704,369 bytes (~439 MiB) |
| Audio level | ~−38.9 dBFS overall RMS; −15.25 dBFS sample peak; no clipping detected |

No sustained black frames or decode failures were found in the systematic inspection. The 29-second opening is intentionally static rather than frozen. Voice is intelligible and the noise floor is low, but the master level is quiet. Speech and visuals are generally synchronized: radar explanation accompanies the comparison, impacts accompany infrastructure, validation accompanies EMSR927, and report narration accompanies the PDFs.

## Exact observed timeline

| Start | End | Visual content | Spoken narration | Requirement demonstrated | Rating | Problem / recommended improvement |
|---:|---:|---|---|---|:---:|---|
| 00:00.000 | 00:28.900 | Branded VARUNA title card, Nepal/satellite imagery and workflow icons | Name/meaning, disaster-access problem, satellite concept | Story/problem framing | Good | Visually strong but far too long. Cut to 7–8 s and introduce radar/cloud advantage here. |
| 00:28.900 | 01:27.800 | Live Satellite Comparison; pre/post swipe; change highlighting; blue/orange overlay | Real Sentinel-1, before/after, cloud penetration, blue decrease and orange increase | Real SAR before/after and change interpretation | Good | Dates are visible but not narrated; exact product IDs, same orbit and 10-day lag are not communicated. “Yellow” conflicts with orange. |
| 01:27.800 | 01:49.000 | Surface Change workspace; raw class metrics and classification map | Possible flood/debris; 126 km² raw flood estimate; not confirmed damage | Floodwater/debris mapping and honesty | Fair | Does not narrate 108.21 km² debris or 62.86/46.93 km² filtered extents. Raw values can dominate interpretation. |
| 01:49.000 | 02:29.000 | Infrastructure Exposure workspace; building/road/highway layers and metrics | OSM overlay; 1,062 buildings; 35 km roads; road graph; six modeled disconnections | Infrastructure and settlement isolation | Good | Pre-event OSM date, bridge exposure, named nearest town/hospital, and explicit hypothetical closure mechanics are not visibly proved. |
| 02:29.000 | 02:47.000 | Reference Validation; EMSR927 footprint and 37.16/26.89/10.28/100% metrics | ~37% spatial overlap; explicitly not accuracy | Independent validation | Good | Properly cautious, but should name Bidur AOI03 and 10-day time offset. |
| 02:47.000 | 03:18.100 | Situation Copilot; English query/answer, Nepali mode/response | English/Nepali rescuer Q&A | Eligible bilingual AI component | Good | Visual proof is real, but grounding and refusal behavior are not explained. Phrase “rural people can also use it” is vague; say “supports Nepali-speaking responders.” |
| 03:18.100 | 03:29.400 | Actual one-page operational SitRep in Chromium PDF viewer | Two generated reports; one-page quick overview | One-page situation report | Good | **Visible from 03:18.100.** Title/map/findings are legible enough at 1080p, though the hold can be shorter. |
| 03:29.400 | 03:49.600 | Actual four-page research PDF; pages 1–4 shown | Research report: methods, results, limitations; closing/thanks | ≤6-page research report and limitations | Fair | **Visible from 03:29.400 to end.** Four pages confirmed. Paging is fast/small; page 3 retains a “replace with full-resolution map…” placeholder. No branded end card. |

Transition boundaries are frame-observed to the nearest 0.1 second; spoken intervals are documented separately in `VIDEO_TRANSCRIPT_TIMESTAMPED.md`.

## Scientific and technical accuracy

### Verified claims

- Sentinel-1 scenes are authentic project inputs:
  - Pre: `S1D_IW_GRDH_1SDV_20260824T001844_20260824T001909_004260_007D5D_45FC_COG.SAFE`
  - Post: `S1D_IW_GRDH_1SDV_20260905T001844_20260905T001909_004435_00837B_60FD_COG.SAFE`
  - Relative orbit 19, descending; 24 August and 5 September 2026; 12-day pair and 10-day post-event lag.
- Blue/decreased backscatter is presented as **possible water**, and orange/increased backscatter as **possible debris or other surface change**. This is appropriately qualified.
- Raw candidates in project evidence are 126.60 km² floodwater and 108.21 km² debris/roughening. The narration rounds floodwater to 126 km² and explicitly calls it raw.
- Project-reported filtered MMU ≥1,000 m² values are 62.86 km² water and 46.93 km² debris; these are not narrated.
- Infrastructure result files support 1,062 potentially exposed buildings, 35.12 km unique exposed roads, and 9.62 km highway intersection.
- Six settlements are a **modeled scenario** under assumed road closure. The narration uses “could become disconnected if certain roads are blocked,” which is scientifically responsible.
- EMSR927 is used as a held-out check. Bidur’s 37.16% is correctly described as spatial overlap and explicitly **not accuracy**.
- Copilot answers shown in English and Nepali are rendered in the actual interface and use the project’s grounded fact path.

### Accuracy concerns

- The visible/raw areal estimates are screening candidates across steep terrain with substantial speckle and terrain ambiguity. The video should not leave raw numbers unpaired with filtered values and the 10-day/layover-shadow caveats.
- “Orange means [backscatter] increased, which could be debris” is acceptable only as a candidate surface-change interpretation, not a debris classification fact. The narration does add “or other changes,” which prevents a material overclaim.
- The EMS comparison is time-offset spatial coincidence, not a conventional accuracy metric. The video states this correctly, but “reference area” should be explicitly “Bidur AOI03.”
- The project’s four-page final research PDF includes a draft figure-caption instruction (“replace with full-resolution map, CRS, scale, legend and credits”) on page 3. This is a document-quality problem, not proof that the underlying metric is false.

**Scientific verdict:** **Mostly accurate and responsibly qualified**, with no observed claim of confirmed road closure or verified destruction. Improvements are needed to distinguish raw from filtered detections and to foreground temporal/terrain uncertainty.

## Track B requirement coverage

| Requirement | Video evidence | Verdict |
|---|---|:---:|
| User-selected area and disaster date | Nepal/August 2026 case is stated; no visible input workflow accepting an arbitrary area/date | **Partial** |
| Real Sentinel-1 before/after | Clearly shown and verbally identified | **Pass** |
| Floodwater and debris/surface-change mapping | Both visible and explained | **Pass** |
| Pre-event OpenStreetMap infrastructure | OSM is named, but snapshot date/pre-event constraint is not shown | **Partial** |
| Buildings, roads, bridges | Buildings/roads shown; bridges not separately demonstrated | **Partial** |
| Settlement isolation and hospital/town reachability | Six scenario settlements and hospitals mentioned; named hub/path result not shown | **Partial** |
| Eligible AI component | English/Nepali Situation Copilot shown | **Pass** |
| EMSR927 independent validation | Shown; non-accuracy caveat spoken | **Pass** |
| Limitations/responsible interpretation | Candidate/not-confirmed and hypothetical language used; 10-day and terrain caveats omitted from narration | **Partial** |
| One-page Situation Report | Actual one-page PDF visible at 03:18.100 | **Pass** |
| Research report ≤6 pages | Actual four-page PDF visible at 03:29.400 | **Pass** |
| Reproducibility/source attribution | Not readable or explained in the video | **Missing in video** |
| Three-minute demo | 03:49.600 | **Fail** |

The separate submission assets do exist locally: root README, one-page SitRep, four-page final research PDF, dashboard/source tree, and result artifacts. The README includes setup/reproduction guidance and required attribution text. Their presence does not cure the video-duration failure, and final upload/package completeness still must be checked in the actual submission portal.

## Score (internal rubric)

| Category | Score | Evidence for deductions |
|---|---:|---|
| Storytelling and introduction | **11/15** | Friendly founder-led opening and clear problem; static opening is 29 s and radar value/application arrive slowly. |
| Product demonstration clarity | **15/20** | Strong live UI progression; arbitrary area/date input, bridge result, and explicit reachability proof are absent. |
| Scientific accuracy and honesty | **17/20** | Candidate/confirmed distinction is strong; raw/filtered and temporal/terrain caveats are insufficiently communicated; color slip. |
| Hackathon requirement coverage | **11/20** | Most core functions appear, but several mandatory items are only partial and duration fails. |
| Audio and narration | **7/10** | Intelligible, calm and natural; quiet master, long gaps, several awkward phrases. |
| Editing, transitions, readability | **5/10** | Clean 1080p capture; overlong title, dense small UI, rapid report paging, unfinished PDF caption. |
| Closing and overall impact | **2/5** | Responsible mission statement and thanks, but closing sits on a dense PDF with no final branded/value card. |
| **Total** | **68/100** | |

## Final decision

**NOT READY.** The sole unavoidable critical fix is to deliver a compliant **≤3:00** recut. While recutting, add compact proof of input area/date, exact scene timing/orbit, filtered results, pre-event OSM/bridge status, named reachability modeling, grounding, attribution, and reproducibility. Remove the research-report placeholder and raise dialogue level. These are targeted edits; a full re-record is not necessary.
