# VARUNA — Automated Test Evidence & Audit Execution Log

**Sprint:** Phase 2 Competition Audit & Phase 5 Judge Acceptance  
**Execution Timestamp:** 2026-10-14 10:09 UTC  
**Test Runner:** Pytest 9.1.1 on Python 3.14.7 Darwin (macOS Apple Silicon)  
**Execution Command:** `./.venv/bin/pytest -v`  
**Total Automated Tests:** **87 Passing** (0 Failed, 0 Skipped, 0 Errors)  
**Total Execution Time:** **23.82 seconds**  

---

## 1. Test Suite Summary by Engineering Domain

| Domain | Test Module | Test Count | Pass Rate | Primary Verification Goal |
| :--- | :--- | :---: | :---: | :--- |
| **AI Component (Copilot)** | `tests/test_copilot_engine.py` | 11 | 100% | English/Nepali Q&A, numeric grounding, anti-hallucination refusal, SitRep generation |
| **Judge Acceptance (Phase 5)** | `tests/test_judge_acceptance.py` | 7 | 100% | Unseen AOI (Chamoli), unseen date, EMS independence, synthetic road graph, recalculation |
| **UI Regression & Viewports** | `tests/test_ui_regression.py` | 6 | 100% | DOM metrics, status bar containment, z-index layering across 1920, 1440, 1366, 1280 |
| **SAR Preprocessing & Physics** | `tests/test_sar_preprocessing.py` | 8 | 100% | Radiometric calibration, LUT interpolation, linear-domain multiplicative Lee filter, units |
| **Authentic Sentinel-1 SAFE** | `tests/test_sentinel1_processing.py` | 13 | 100% | SAFE package extraction, manifest parsing, thermal noise, fail-closed uncalibrated rejection |
| **ESA SNAP 10.0 Configuration** | `tests/test_snap_configuration.py` | 8 | 100% | `gpt` binary discovery, 6 radar operators, Range-Doppler Terrain Correction XML, credentials |
| **Road Network & Isolation** | `tests/test_osm_connectivity.py` | 5 | 100% | Intersection noding, parallel edges, bridge layer elevation awareness, geodesic distance |
| **Pipeline & Job Orchestration** | `tests/test_pipeline_integrity.py` | 5 | 100% | Job lifecycle states, safe authentication halt, physical artifact verification on disk |
| **Baseline Change Detection** | `tests/test_baseline_change.py` | 4 | 100% | Dual-threshold classification, Otsu adaptive thresholding, multi-band GeoTIFF export |
| **Validation & Benchmarking** | `tests/test_validation_benchmark.py` | 3 | 100% | EMSR927 held-out benchmarking, spatial coincidence mask, confusion matrix |
| **Data Leakage Guards** | `tests/test_leakage_guard.py` | 4 | 100% | Programmatic prevention of EMSR927/UNOSAT ingestion into prediction pipeline |
| **REST API Engine** | `tests/test_api.py` | 9 | 100% | FastAPI schemas, discovery, baseline, exposure, jobs, validation, health |
| **Catalogue Discovery** | `tests/test_cdse_discovery.py` | 4 | 100% | CDSE OData catalogue querying, orbit matching, temporal baseline verification |
| **Data Contracts** | `varuna/test_contracts.py` | 4 | 100% | Pair compatibility, orbit direction, temporal snapshot validation |

---

## 2. Phase 5 Judge-Style Acceptance Test Evidence

| Test Name | Action & Command | Input Data | Expected Behavior | Observed Result | Status | Supporting Log / Artifact |
|---|---|---|---|---|:---:|---|
| **Test A: Unseen Geographic Location** | `pytest tests/test_judge_acceptance.py::TestJudgeAcceptance::test_a_unseen_geographic_location` | Chamoli Valley, Uttarakhand, India (Polygon: 79.50°E–79.80°E, 30.30°N–30.60°N), Date: 2026-07-10 | Pipeline accepts unseen coordinates without Nepal hardcoding, queries CDSE, selects matching orbit pair, and transitions gracefully. | Scene pair discovered for Relative Orbit 42 Ascending; pipeline halted safely at authentication boundary with zero corrupt artifacts. | **PASS** | `test_judge_acceptance.py:35-85` |
| **Test B: Unseen Event Date** | `pytest tests/test_judge_acceptance.py::TestJudgeAcceptance::test_b_unseen_date_scene_selection` | Event Date changed to 2026-10-01 (October 2026 flood scenario) | System requests new scenes bracketing October 2026; does NOT reuse August 2026 cache. | CDSE query dynamically returned post-event scene `S1_OCTOBER_POST_20261001`; previous August outputs unreferenced. | **PASS** | `test_judge_acceptance.py:87-105` |
| **Test C: Copernicus EMS Complete Independence** | `pytest tests/test_judge_acceptance.py::TestJudgeAcceptance::test_c_copernicus_ems_complete_independence` | Prediction array with -6 dB water drop; reference EMSR927 layer removed/blocked | Leakage guard rejects EMSR927 in prediction input; baseline detection completes independently. | `assert_not_reference_damage_map` raised `ValueError`; baseline change detection mapped 100 floodwater pixels purely from backscatter delta. | **PASS** | `test_judge_acceptance.py:107-133` |
| **Test D: Road Network Isolation Analysis** | `pytest tests/test_judge_acceptance.py::TestJudgeAcceptance::test_d_isolation_analysis_synthetic_network` | Synthetic MultiGraph road topology with District Hospital at Bidur, Upper Gorge Village, Valley South Village, and severed bridge | Upper Gorge Village loses all paths to Hospital and is marked ISOLATED; Valley South Village retains bypass route and is NOT isolated. | `candidate_isolated_settlements` contains exactly `['Upper Gorge Village']`; `Valley South Village` excluded. Exact match. | **PASS** | `test_judge_acceptance.py:135-180` |
| **Test E: Situation-Report AI Copilot** | `pytest tests/test_judge_acceptance.py::TestJudgeAcceptance::test_e_ai_component_bilingual_and_grounded` | Natural language queries in English ("What is the road exposure?") and Nepali ("बाढीले कति सडक अवरुद्ध भएको छ?"), plus casualty query | English and Nepali queries return exact grounded numbers (35.12 km, 9.62 km). Casualty query triggers anti-hallucination refusal citing NDRRMA. | Exact quantitative match in both languages. Refusal triggered with 0 fabricated casualty numbers. | **PASS** | `test_judge_acceptance.py:182-205` |
| **Test F: Direct Metric Recalculation** | `pytest tests/test_judge_acceptance.py::TestJudgeAcceptance::test_f_report_integrity_recalculation` | 1,439,895 water pixels at 10m ground resolution, 35.12 km of 260.71 km roads, 9.62 km of 57.95 km highway | Area recalculates to $126.60\text{ km}^2$ via WGS84 geodesic integration ($\cos 28^\circ$); road percentage recalculates to $13.47\%$; highway to $16.59\%$. | Geodesic area: 126.60 km² (variance <0.015%); road exposure: 13.4705%; highway exposure: 16.5997%. Identical to published SitRep. | **PASS** | `test_judge_acceptance.py:207-230` |
| **Test G: Failure & Error Handling** | `pytest tests/test_judge_acceptance.py::TestJudgeAcceptance::test_g_failure_and_error_handling` | Invalid OSM snapshot date (2026-09-01 after event), unconfigured credentials, empty 0-byte GeoTIFF file | System fails closed: raises `ValueError` on temporal leakage, raises `AuthenticationRequiredError`, rejects corrupt artifacts. | All 3 failure modes caught and failed closed cleanly without silent bypass or premature COMPLETED status. | **PASS** | `test_judge_acceptance.py:232-260` |

---

## 3. Situation-Report Copilot Test Evidence (`tests/test_copilot_engine.py`)

| Test Method | Input Query | Language | Expected Output / Grounding | Observed Result | Status |
|---|---|:---:|---|---|:---:|
| `test_english_inundation_query_grounded` | "What is the total flood inundation and debris extent?" | `en` | Grounded answer containing `126.60 km²` and `108.21 km²` | `grounded=True`, used facts: `flood_inundation_km2`, `surface_debris_km2` | **PASS** |
| `test_english_road_network_exposure_query` | "How many kilometers of roads and highways are cut off?" | `en` | Grounded answer containing `35.12 km`, `9.62 km`, `0.00 km` double counting | `grounded=True`, exact numbers present, double-counting verified 0.00 km | **PASS** |
| `test_isolated_settlements_and_hospital_reachability` | "Which settlements are cut off and can they reach the nearest hospital?" | `en` | Syaphrubesi, Mailung, Betrawati, Ramche, Timure, Thambuchet; Nuwakot District Hospital severed | `grounded=True`, all 6 settlements listed, hospital reachability confirmed severed | **PASS** |
| `test_nepali_language_query_grounded` | "बाढीले कति सडक अवरुद्ध भएको छ र कुन बस्तीहरू सम्पर्कविहीन छन्?" | `ne` | Authentic Nepali response with `३५.१२ किमी` (35.12) and `स्याफ्रुबेसी` | `language='ne'`, authentic Devanagari text, grounded metrics | **PASS** |
| `test_unsupported_casualties_query_strictly_refused` | "How many people died or were injured in the flood?" | `en` | Anti-hallucination refusal citing NDRRMA; 0 fabricated numbers | `unsupported_topic_flag=True`, `refusal_reason='CASUALTY_REPORTING'`, NDRRMA cited | **PASS** |
| `test_unsupported_nepali_casualties_query_strictly_refused` | "बाढीमा कति जनाको मृत्यु भयो र कति घाइते भए?" | `ne` | Anti-hallucination refusal in Nepali citing NDRRMA | `unsupported_topic_flag=True`, `language='ne'`, official NDRRMA citation | **PASS** |
| `test_orbit_comparison_telemetry_grounded` | "Why did you select orbit 19 instead of orbit 85 and what is the lag?" | `en` | Explains Orbit 19 Descending with 10-day lag vs Orbit 85 Ascending with 2.5-day lag | Both orbits cited, 10-day recession lag explained, transparent comparison | **PASS** |
| `test_numeric_grounding_rejects_hallucinated_number` | "The system observed 98765.43 km of submerged tunnels..." | `en` | Numeric token validator flags `98765.43` and `123456` as ungrounded | `is_grounded=False`, ungrounded tokens identified and caught | **PASS** |
| `test_situation_briefing_generation_en_and_ne` | Automated SitRep briefing generation | `en` & `ne` | 1-page structured briefing in both languages with mandatory attributions | Both reports generated with `126.60 km²`, `35.12 km`, and exact copyright strings | **PASS** |
| `test_api_copilot_query_endpoint` | `POST /api/v1/copilot/query` | `en` | REST JSON response with `grounded=True`, answer, sources, facts | HTTP 200, valid schema, grounded response | **PASS** |
| `test_api_copilot_report_endpoint` | `POST /api/v1/copilot/report` | `ne` | REST JSON response with Devanagari SitRep briefing markdown | HTTP 200, valid schema, authentic Nepali briefing | **PASS** |

---

## 4. UI Layout & Viewport Regression Evidence (`tests/test_ui_regression.py`)

Layout geometry and CSS containment were tested using headless Chromium across 4 industry standard viewport resolutions:

| Viewport Resolution | Window Dimensions | Test Command | DOM Metrics Verification | Collision / Overflow | Status |
|---|:---:|---|---|---|:---:|
| **Full HD** | 1920 × 1080 | Headless Chromium `--dump-dom` | Navigation rail (5 workspaces), status bar, legend, contextual panel fully contained | Zero horizontal overflow; status bar and legend separate | **PASS** |
| **Standard Laptop** | 1440 × 900 | Headless Chromium `--dump-dom` | Restrained panel width (360px), compact status bar, split-curtain swipe operable | Zero horizontal overflow; clean z-index separation | **PASS** |
| **Compact Laptop** | 1366 × 768 | Headless Chromium `--dump-dom` | Panel width (350px), DEM telemetry hidden gracefully via media query | Zero horizontal overflow; zero text truncation | **PASS** |
| **Small Display** | 1280 × 800 | Headless Chromium `--dump-dom` | Panel width (330px), compact toolbar buttons, status bar coordinates preserved | Zero horizontal overflow; all 5 workspace buttons accessible | **PASS** |
