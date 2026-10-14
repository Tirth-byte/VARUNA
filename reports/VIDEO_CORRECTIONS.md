# VARUNA Final Video — Corrections

Corrections are ordered by submission risk. The source video was not modified.

## CRITICAL

| Timestamp | Problem | Why it matters | Smallest fix | Re-record? |
|---|---|---|---|---|
| 00:00.000–03:49.600 | The file is **3:49.60**, exceeding the required three-minute demo by **49.60 seconds**. | The Track B PDF explicitly requires a “3-minute demo video.” This is a direct submission-compliance risk. | Recut to **≤02:59.5**. Reduce the 29-second static opening to 7–8 seconds; remove repeated/idle map holds; compress report paging; retain all mandatory proof. | **No.** Existing narration can be tightened with ripple edits, though a short replacement voiceover would sound smoother. |

## IMPORTANT

| Timestamp | Problem | Why it matters | Smallest fix | Re-record? |
|---|---|---|---|---|
| 00:00.000–00:28.900 | Static title card occupies almost 29 seconds. | It consumes 16% of the allowed three minutes before the product appears. | Keep the strongest 7–8 seconds and enter the live dashboard while the problem statement continues. | No. |
| 00:26.460–00:49.520 | Narration says “real Sentinel-1” but does not state the exact pre/post dates, same-orbit geometry, or the 10-day post-event lag. | These facts establish authenticity and prevent a judge from interpreting the image as near-peak flood mapping. | Add a concise overlay/voice line: “24 Aug vs 5 Sep 2026, Sentinel-1 orbit 19 descending; the second pass is 10 days post-event.” | Voice pickup recommended; an overlay is the smallest fix. |
| 01:04.920–01:18.340 | Blue is first paired with “yellow,” then the second class is called orange. | Color inconsistency weakens map comprehension. | Replace “yellow” with “orange,” or remove “and one is yellow.” | Tiny audio pickup or subtitle patch. |
| 01:28.940–01:48.820 | Only raw floodwater (“126 square kilometers”) is narrated; debris extent and the filtered/MMU values are absent. | The raw 126.60/108.21 km² fields contain extensive speckle; the project itself reports filtered 62.86/46.93 km². A judge may mistake raw candidates for operational extents. | Show and name both raw and filtered values, explicitly labeling them candidate screening estimates. | Short voice pickup/overlay. |
| 01:56.700–02:26.640 | OSM buildings/roads and modeled isolation are discussed, but pre-event snapshot status, bridges, named nearest town/hospital reachability, and the hypothetical-closure basis are not fully demonstrated. | These are explicit Track B requirements, especially the 20% cut-off-settlement criterion. | Add one compact result panel: “pre-event OSM (27 Jul 2026); 6 scenario-isolated settlements; nearest hub: Nuwakot District Hospital/Bidur; exposed links assumed closed.” Show bridge count/status if supported, or state that bridge exposure was not separately quantified. | No if a verified overlay exists; otherwise a short screen capture is needed. |
| 02:30.540–02:45.600 | EMSR927 is named and correctly qualified, but “reference area” is vague. | The result is specifically Bidur AOI03, time-offset spatial coincidence—not general validation accuracy. | Label the result “Bidur AOI03; 37.16% observed-event spatial coincidence; 10-day time offset; not precision/recall/accuracy.” | No. |
| 02:47.760–03:06.720 | The copilot is shown, but the grounding/anti-hallucination mechanism is not demonstrated explicitly. | The selected AI track requires every number to come from system maps. | Retain the answer’s fact tags and add “answers are restricted to computed map facts; unsupported casualty claims are refused.” | No. |
| 03:20.620–03:34.320 | The four-page research PDF is paged quickly; page body text is too small at full-page view. Page 3 also contains the draft caption “replace with full-resolution map…” in the actual PDF. | Judges cannot reliably inspect methodology/results/limitations, and the placeholder undermines final-report polish. | Remove the placeholder from the PDF, rebuild it, and zoom to one readable method/result/limitation detail per page. | No narration re-record required. |
| Whole video | Required attribution and reproducibility evidence are not legible in the demo. | Track B requires source attribution; judges also need confidence in end-to-end reproducibility. | Add a 2–3 second end card: repository/README, raw-to-report pipeline, and the three mandatory attribution strings in readable type (or state that they are included in the submission package). | No. |
| 00:00.000–03:49.600 | Voice is intelligible but mastered quietly (mono-extracted RMS about **−38.9 dBFS**, peak **−15.25 dBFS**); pauses are long. | Low playback volume and loose pauses reduce energy and intelligibility in a noisy judging room. | Normalize dialogue to roughly −16 LUFS integrated with a true peak below −1 dBTP; tighten pauses after phrases. | No. |

## OPTIONAL

| Timestamp | Problem | Why it matters | Smallest fix | Re-record? |
|---|---|---|---|---|
| 00:29.000–03:18.000 | Browser chrome and dense side panels reduce usable map area. | Fine labels are difficult to read at normal laptop playback size. | Crop browser chrome or use a clean 1080p capture; enlarge the active metric/legend with punch-in zooms. | No. |
| 03:34.320–03:49.600 | Closing narration runs over the research PDF and ends without a branded closing frame. | The final impression is less intentional than the strong opening. | End on a 2–3 second VARUNA mark plus a one-line value statement and repository/submission cue. | No. |

## Minimal compliant recut

Target **02:55–02:59**:

1. 00:00–00:08 — VARUNA name/meaning/problem.
2. 00:08–00:40 — input area/date, real before/after Sentinel-1, dates/orbit/lag, slider, blue/orange meaning.
3. 00:40–01:10 — candidate water/debris, raw vs filtered, limitations.
4. 01:10–01:38 — pre-event OSM exposure, bridges if supported, modeled isolation/hospital reachability.
5. 01:38–01:58 — EMSR927 held-out comparison with 37.16% caveat.
6. 01:58–02:22 — bilingual grounded copilot.
7. 02:22–02:45 — one-page SitRep and ≤6-page research report, each readable.
8. 02:45–02:58 — reproducibility, attributions, responsible-use close.
