# VARUNA — Scientific Figure Integration & Publication QA Report

**Document Title:** Evidence-Grounded Flood Inundation and Infrastructure Accessibility Mapping from Sentinel-1 SAR in High-Relief Mountain Terrain  
**Status:** Verification & Peer-Review Publication Ready  
**Date:** October 2026  
**Artifact Generated:** `VARUNA_Research_Paper_FINAL.pdf`  
**Reference Design Baseline:** `VARUNA_Research_Paper_REFINED.pdf`  

---

## 1. Executive Summary & Objective

In accordance with academic publication standards, this quality assurance report documents the targeted replacement of low-resolution raster placeholders (originally 66–92 DPI) with publication-grade scientific cartographic figures (>650 DPI) generated directly from the authentic VARUNA project processing pipeline.

The layout, typography, section hierarchy, table composition, and pagination of the approved 4-page A4 research paper have been strictly preserved. Zero artificial smoothing, generic stock imagery, or fabricated metrics were introduced.

---

## 2. Scientific Figure Provenance & Technical Specifications

All four figures were generated directly from authentic Level-1 GRD SAR data, calibrated change rasters, and Copernicus Emergency Management Service (EMS) EMSR927 activation layers using `scripts/generate_all_publication_figures.py`.

| Figure | Subject & Extent | Source Dataset(s) & Provenance | Pixel Dimensions | Target PDF Slot Size | Effective Print DPI | Aspect Ratio Match |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Figure 1** | Study Area & Geographic Context (Trishuli River Basin) | `aligned/aligned_post.tif`<br>`dashboard/layers/candidate_water_dashboard.geojson`<br>`dashboard/layers/major_highways_trishuli.geojson`<br>`dashboard/layers/emsr927_event_extents.geojson` | 2,250 × 2,250 px | 225.00 × 225.00 pt (3.125" × 3.125") | **720 DPI** | Exact 1.000000 (0.00% distortion) |
| **Figure 2** | Pre-Event vs Post-Event Sentinel-1 SAR Comparison | `aligned/aligned_pre.tif` (2026-08-24 00:18:44 UTC, Orbit 19)<br>`aligned/aligned_post.tif` (2026-09-05 00:18:44 UTC, Orbit 19) | 3,200 × 1,557 px | 349.49 × 170.00 pt (4.854" × 2.361") | **659 DPI** | Matched 2.05584 (0.02% diff) |
| **Figure 3** | SAR Surface Change Classification (CAG 1,526.05 km²) | `results/flood_change_classification.tif` (Band 2: Classes 1–4)<br>`aligned/aligned_post.tif` (Backscatter terrain backdrop)<br>`dashboard/layers/major_highways_trishuli.geojson` | 2,400 × 2,250 px | 234.66 × 220.00 pt (3.259" × 3.056") | **736 DPI** | Matched 1.06667 (0.00% diff) |
| **Figure 4** | Copernicus EMSR927 Reference Validation (Bidur AOI03) | `results/flood_change_classification.tif`<br>`dashboard/layers/emsr927_event_extents.geojson` (AOI03)<br>`dashboard/layers/exposed_buildings_dashboard.geojson`<br>`dashboard/layers/exposed_roads_dashboard.geojson` | 2,400 × 2,250 px | 234.66 × 220.00 pt (3.259" × 3.056") | **736 DPI** | Matched 1.06667 (0.00% diff) |

---

## 3. Targeted Image Replacement Architecture

To ensure zero layout drift, zero font reflow, and zero unintended page breaks, the integration was performed via in-place PDF XObject stream replacement (`scripts/build_final_research_paper.py`):

1. **Object 3 (Page 1):** Injected `figures/figure1_study_area_context.png` into `/FormXob.e712a5f9546488d0c3d113825b3644d8`.
2. **Object 5 (Page 2):** Injected `figures/figure2_s1_pre_post_comparison.png` into `/FormXob.397a0e28d9537f07e8b17361c59df759`.
3. **Object 7 (Page 3 Top):** Injected `figures/figure3_sar_surface_change_classification.png` into `/FormXob.21ef92fb53f5e1254f99430bf6795962`.  
   *Note: In the unrefined draft, images 7 and 8 were inverted relative to their captions. This final build places the Regional Surface Change Classification map directly above the Figure 3 caption.*
4. **Object 8 (Page 3 Bottom):** Injected `figures/figure4_emsr927_validation_bidur.png` into `/FormXob.22bb07c67e1b3be6fe592a82a04d0c16`.  
   *Placed directly above the Figure 4 caption (Bidur Confluence AOI03 validation).*
5. **Page 4:** Intact academic text, building exposure cross-tabulation table (Table 4), limitations, reproducibility disclosure, and citations [1–7].

---

## 4. Quality Assurance & Visual Verification Checklist

All pages of `VARUNA_Research_Paper_FINAL.pdf` were rendered to 250 DPI PNG rasterizations via `pdftoppm` and inspected visually:

- [x] **Academic Serif Typography:** Preserved justified paragraphs, font families (`LiberationSerif`), headers, and footers.
- [x] **Page Count & Compact A4 Layout:** Verified exactly 4 pages (A4 dimensions: 595.28 × 841.89 pt). No overflow, orphan headings, or blank spaces.
- [x] **Page 1 Opening Composition:** Verified the large Figure 1 map on the upper right (225 × 225 pt) with abstract and introduction running along the left column and body text wrapping cleanly beneath.
- [x] **Figure-Caption Pairing:**
  - Figure 1 paired with Study Area & Reference Geography caption.
  - Figure 2 paired with Pre/Post Sentinel-1 comparison caption.
  - Figure 3 paired with Candidate SAR Surface Change classification caption.
  - Figure 4 paired with EMSR927 event footprint overlay at Bidur confluence caption.
- [x] **Table Integrity:** Tables 1, 2, 3, and 4 retain precise column widths, borders, and numbers matching the repository's verified metrics (126.60 km² floodwater, 108.21 km² debris, 66.40 km² permanent water, 37.16% AOI03 coincidence).
- [x] **Distortion & Sharpness:** All 4 figures have effective resolutions between 659 and 736 DPI (well above the 300 DPI minimum). Zero stretching or distortion.
- [x] **Geospatial Annotations:** Every map contains genuine geographic graticules (WGS 84 °E / °N), metric scale bars, north arrows, and scientific legends.

---

## 5. Scientific Rigor & Disclosed Limitations

1. **Revisit Lag:** The post-event acquisition (05 Sep 2026) was 10 days after the flood event (26 Aug 2026). Detections represent persistent backscatter anomalies, not peak inundation.
2. **Topographic Limitations:** In high-relief terrain (>25° slopes), geometric layover, shadow, and moisture changes induce radar ambiguities. The exported single-band raster lacks an operational auxiliary shadow mask.
3. **Validation Language:** Overlap with Copernicus EMSR927 optical footprints (37.16% in AOI03, 23.70% in AOI01) represents time-offset spatial coincidence, not conventional classifier accuracy, precision, or recall.
4. **Exposure vs Damage:** 1,062 intersected buildings and 35.12 km of intersected roads are spatial screening indicators, not field-confirmed structural failure or road closures.

---

## 6. Deliverables Summary

1. `VARUNA_Research_Paper_FINAL.pdf` (Workspace root, `docs/`, and `dashboard/docs/`)
2. `figures/`:
   - `figure1_study_area_context.png`
   - `figure2_s1_pre_post_comparison.png`
   - `figure3_sar_surface_change_classification.png`
   - `figure4_emsr927_validation_bidur.png`
3. Pipeline scripts:
   - `scripts/generate_all_publication_figures.py`
   - `scripts/build_final_research_paper.py`
4. Dashboard Integration:
   - Updated `dashboard/index.html` link `btnExportResearch` to target `docs/VARUNA_Research_Paper_FINAL.pdf`.
   - Situation Report `docs/SITUATION_REPORT_NEPAL_2026.pdf` remains completely untouched.
