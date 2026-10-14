# VARUNA — Satellite-Powered Flood Intelligence System

**Track B: Mapping Flood Damage from Space — Multimodal AI Hackathon 2026**  
*Final Release Version: October 14, 2026 Submission-Ready*  
*Verified Case Study: August 26, 2026 Trishuli River GLOF & Flash Flood, Central Nepal*

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Copernicus](https://img.shields.io/badge/Copernicus-Sentinel--1%20SAR-orange.svg)](https://dataspace.copernicus.eu/)
[![ESA SNAP](https://img.shields.io/badge/ESA%20SNAP-10.0%20GPT-purple.svg)](https://step.esa.int/)
[![Tests](https://img.shields.io/badge/Tests-87%20Passing-brightgreen.svg)](tests/)

---

## 1. Executive Summary & Headline Results

VARUNA is an evidence-grounded satellite flood intelligence pipeline engineered to ingest raw Synthetic Aperture Radar (SAR) observations, perform rigorous terrain-corrected radiometric calibration, detect floodwater and debris hazards in high-relief mountain valleys, calculate infrastructure exposure without synthetic fabrication, and provide a bilingual Situation-Report Copilot that answers rescue queries with strict numeric grounding.

### Verified Scientific Headline Statistics (Trishuli River Study Domain)
* **Common Analysis Grid (CAG):** $1,526.05\text{ km}^2$ ($3,897 \times 4,454$ pixels, 100.0% valid spatial overlap, zero NoData within analysis bounds).
* **Candidate Flood Inundation:** **$126.60\text{ km}^2$** ($1,439,895$ pixels, $\Delta\sigma^0 \le -3.5\text{ dB}$).
  * Geodesic verification: Exact row-by-row WGS84 geodesic integration yields $126.61\text{ km}^2$ ($+0.015\%$ variance).
  * Equal-area metric reprojection: UTM Zone 45N yields $126.58\text{ km}^2$ ($-0.010\%$ variance).
* **Candidate Surface Debris / Roughening:** **$108.21\text{ km}^2$** ($1,230,733$ pixels, $\Delta\sigma^0 \ge +3.5\text{ dB}$ raw unconstrained coarsening across CAG; $46.93\text{ km}^2$ contiguous MMU $\ge 1,000\text{ m}^2$; $17.51\text{ km}^2$ filtered major clusters MMU $\ge 2,000\text{ m}^2$).
* **Copernicus EMS EMSR927 Cross-Validation:**
  * **AOI03 (Bidur Confluence):** $37.16\%$ total SAR anomaly capture within the optical event footprint ($26.89\%$ water, $10.28\%$ debris).
  * **AOI01 (Syapru Besi Gorge):** $23.70\%$ total SAR anomaly capture ($9.82\%$ water, $13.88\%$ debris).
  * *Methodological note:* Overlap is evaluated as *observed-event spatial coincidence*, not classic classifier precision/recall, due to the 10-day post-peak observation window.
* **Critical Infrastructure Exposure (EMSR927 & National Survey Data):**
  * **Buildings:** $1,062$ potentially exposed of $3,816$ surveyed structures ($27.83\%$), including $936$ of $2,813$ confirmed destroyed structures ($33.27\%$).
  * **Road Network:** $35.12\text{ km}$ unique exposed road length of $260.71\text{ km}$ ($13.47\%$, 605 segments; $0.00\text{ km}$ double-counting between hazard classes).
  * **Pasang Lhamu Highway:** $9.62\text{ km}$ of potential hazard intersection along the $57.95\text{ km}$ study corridor ($16.59\%$).
* **Candidate Isolated Settlements (Model-Derived):** 6 communities severed from vehicular access to the nearest hospital and municipal center (Syaphrubesi, Mailung, Betrawati, Ramche, Timure, Thambuchet) under simulated road closure. (Satellite exposure indicates potential vulnerability and does not constitute ground-confirmed physical destruction).

---

## 2. Key Submission Deliverables

| Deliverable Artifact | Format | Description / Link |
| :--- | :---: | :--- |
| **Emergency Situation Report (SITREP 01)** | Markdown & PDF (1 Page) | [`docs/SITUATION_REPORT_NEPAL_2026.md`](docs/SITUATION_REPORT_NEPAL_2026.md) & [`docs/SITUATION_REPORT_NEPAL_2026.pdf`](docs/SITUATION_REPORT_NEPAL_2026.pdf) |
| **Full Scientific Research Report** | Markdown & PDF (6 Pages) | [`docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.md`](docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.md) & [`docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.pdf`](docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.pdf) |
| **Interactive Web Dashboard** | HTML / JS / Leaflet | [`dashboard/index.html`](dashboard/index.html) (Live on port `8888`) |
| **Bilingual Situation Copilot** | Python & REST API | [`varuna/copilot/engine.py`](varuna/copilot/engine.py) (Bilingual EN/NE Q&A, grounded metrics, anti-hallucination) |
| **3-Minute Demonstration Script** | Markdown | [`docs/DEMO_PRESENTATION_SCRIPT.md`](docs/DEMO_PRESENTATION_SCRIPT.md) |
| **Classified Change GeoTIFF** | 128 MB 3-band GeoTIFF | `data/experiments/nepal_aug2026/2ed78818-f3c5-40de-aeea-9647dc7a68ee/results/flood_change_classification.tif` |
| **Original Polygon Archive** | 488 MB GeoJSON (782k feats) | `data/experiments/nepal_aug2026/2ed78818-f3c5-40de-aeea-9647dc7a68ee/results/candidate_hazard_polygons.geojson` |
| **Optimized Web Layers** | 10.8 MB total GeoJSON | `dashboard/layers/` (Water, Debris, EMSR927 truth, Buildings, Roads, Highway) |
| **Validation & Exposure JSON** | Machine-Readable JSON | [`independent_validation_emsr927.json`](data/experiments/nepal_aug2026/2ed78818-f3c5-40de-aeea-9647dc7a68ee/results/independent_validation_emsr927.json) |

---

## 3. Scientific Integrity & Disclosures

1. **10-Day Observation Window:** The post-event Sentinel-1 acquisition was recorded on **September 5, 2026 (10 days post-peak)**. In high-gradient Himalayan gorges, flash flood surges recede within 24–48 hours. SAR observes persistent water bodies, saturated mud terraces, and altered gravel beds, not the peak flood pulse.
2. **Orbit 19 vs Orbit 85 Evaluation:** The CDSE catalogue query also discovered Relative Orbit 85 (Ascending) acquired August 16 pre and August 28 post (+2.5 days / 48–60 hrs post-peak), which offers closer temporal proximity to peak inundation. Orbit 19 was selected for primary processing due to complete contiguous basin framing, with the 10-day lag explicitly declared.
3. **Potential Exposure vs Confirmed Destruction:** Satellite hazard intersection indicates **POTENTIAL EXPOSURE**. It does not prove physical collapse or road closure without on-site civil engineering verification.
4. **Highway Exposure Audit:** The $9.62\text{ km}$ of national highway hazard intersection must not be conflated with EMSR927 surveyed destroyed roads ($60.97\text{ km}$ of local riverbed access roads, of which only $0.30\text{ km}$ directly coincides within 50m of the national highway centerline).
5. **ESA SNAP Layover/Shadow Disclosure:** Range-Doppler Terrain Correction was orthorectified using the Copernicus 30m Global DEM; however, auxiliary shadow bands were omitted during single-band decibel GeoTIFF export, resulting in 0 pixels flagged as `TERRAIN_SHADOW_SUSPECT`. Backscatter changes on steep mountain faces ($>25^\circ$) require optical verification.
6. **SNAP Calibration Warning Provenance:** CloudFerro COG wrappers add an outer metadata node `<safe:processing name="COG Conversion">`, causing SNAP's version parser to emit a warning. Internal IPF 004.03 lookup tables were verified genuine.

---

## 4. Setup & Reproduction Guide

### A. Environment Installation
```bash
# Clone repository and enter directory
cd VARUNA

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### B. Running Automated Verification Tests
```bash
pytest -v
```
All **87 automated unit, integration, contract, and judge-acceptance tests** pass cleanly in under 25 seconds, verifying orbit matching, CDSE catalogue discovery, Lee speckle filtering, radiometric calibration, baseline change detection, road graph isolation, FastAPI schemas, data contracts, and Situation-Report Copilot bilingual grounding.

### C. Launching the Interactive Web Dashboard
```bash
# Start lightweight HTTP server for dashboard
python3 -m http.server 8888 --directory dashboard
```
Open **`http://localhost:8888/dashboard/index.html`** in your browser. The scientific workstation provides 5 dedicated Earth-observation workspaces:
1. **Satellite Comparison:** Authentic pre-event (Aug 24) vs post-event (Sept 5) Sentinel-1 SAR intensity imagery with an interactive split-swipe divider, telemetry readout, and decibel stretch controls.
2. **Surface Change:** Interpretable bitemporal change detection with native raster hazard overlays (transparent non-hazard pixels, 10m native spatial resolution), threshold physics controls, and disclosed terrain shadow caveats.
3. **Infrastructure Exposure:** Affected road and building overlays, geographic sector filtering (Bidur, Syapru Besi, Timure), and evidence-backed unique exposure statistics.
4. **Reference Validation:** Copernicus EMSR927 held-out benchmarking with geographically accurate vector extents and appropriately qualified metrics distinguishing 10-day recession overlap from classifier accuracy.
5. **Situation Copilot:** Bilingual operational AI assistant answering rescuer questions in English and Nepali, with strict numeric grounding in computed metrics and anti-hallucination guards.

### D. Exporting PDFs
```bash
# Re-render research report and situation report PDFs
python3 docs/build_reports.py
```

---

## 5. Repository Architecture

```
VARUNA/
├── dashboard/                      # Earth Observation Intelligence Workspace
│   ├── index.html                  # Responsive 5-workspace application
│   ├── styles.css                  # Apple-restrained scientific design system
│   ├── app.js                      # Multi-workspace logic, swipe curtain & telemetry
│   ├── rasters/                    # Reprojected S1 SAR intensity & hazard overlays
│   └── layers/                     # Optimized dashboard GeoJSON layers (10.8 MB)
├── data/
│   ├── experiments/nepal_aug2026/  # Authentic Sentinel-1 experiment run
│   │   └── 2ed78818-f3c5-40de-.../
│   │       ├── results/            # GeoTIFFs, vector polygons, validation JSON
│   │       └── raw/                # Calibrated pre/post terrain-corrected rasters
│   ├── reference/emsr927/          # Copernicus EMS EMSR927 ground truth vectors
│   ├── infrastructure/             # Nepal Survey Dept major roads & OSM vectors
│   └── demo_evidence/              # High-resolution maps and dashboard screenshots
├── docs/
│   ├── SITUATION_REPORT_NEPAL_2026.md   # 1-page Situation Report (and .pdf)
│   ├── RESEARCH_REPORT_TRISHULI_FLOOD_2026.md # 6-page Research Report (and .pdf)
│   ├── DEMO_PRESENTATION_SCRIPT.md     # 3-minute presentation script
│   ├── FINAL_COMPLIANCE_AUDIT.md       # Comprehensive requirements traceability matrix
│   ├── SCIENTIFIC_DATA_LINEAGE.md      # Data lineage & orbit trade-off analysis
│   ├── TEST_EVIDENCE.md                # 87 executed test results & audit logs
│   ├── REMAINING_RISKS.md              # Residual risks & operational constraints
│   └── build_reports.py                # Automated PDF rendering pipeline
├── varuna/                         # Production Python Package
│   ├── acquisition/                # CDSE OData discovery and authenticated download
│   ├── preprocessing/              # Radiometric calibration & ESA SNAP GPT wrappers
│   ├── detection/                  # Bitemporal decibel change detection & Otsu
│   ├── validation/                 # Held-out EMSR927 validation & leakage guards
│   ├── osm/                        # Road network routing and exposure analysis
│   ├── copilot/                    # Bilingual grounded Situation-Report Copilot
│   └── api/                        # FastAPI REST service
└── tests/                          # Automated pytest suite (87 tests passing)
```

---

## 6. Official Data Attributions & Required Licenses

In accordance with official hackathon submission requirements:

1. **"Contains modified Copernicus Sentinel data 2026."**
2. **"Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."**
3. **"© OpenStreetMap contributors."** (OpenStreetMap pre-event road network and building footprints under ODbL license).
4. **"European Union, Copernicus Emergency Management Service data."** (Activation EMSR927 *Flood in Nepal*, used exclusively for independent held-out checking).
5. **Training Dataset Benchmark Citation:** Bonafilia, D., et al. (2020). *Sen1Floods11: A Georeferenced Dataset to Train and Test Deep Learning Flood Algorithms for Sentinel-1*. IEEE/CVF CVPR Workshops 2020.
6. **Nepal Survey Department:** Government of Nepal, Ministry of Land Management, Geodetic Survey Branch.
