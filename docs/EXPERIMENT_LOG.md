# VARUNA — Scientific Experiment Log

**Sprint:** Phase 1.7 Authentic Sentinel-1 Flood Mapping & Defect Elimination  
**Experiment ID:** `EXP-2026-08-TRISHULI-AUTHENTIC-01`  
**Target Event:** August 26, 2026 Trishuli Flood, Central Nepal  
**Case Study Geography:** Trishuli River Valley & Gorge (Rasuwa & Nuwakot Districts, Central Nepal)  
**Execution Timestamp:** 2026-10-11T13:42:07Z  
**Starting Commit:** `8a4cf0e`  
**Core Scientific Principle:** *"Accuracy before appearance. Evidence before claims. If we cannot verify it, we do not present it as fact."*

---

## 1. Study Area Geography & Case Study Boundaries

- **Geographic Extent (AOI):**
  - Latitude: $27.90^\circ\text{N}$ to $28.20^\circ\text{N}$
  - Longitude: $85.10^\circ\text{E}$ to $85.35^\circ\text{E}$
- **Geographic Coverage Description:**
  - Encompasses the Trishuli River drainage from the confluence with Tadi Khola at Bidur/Battar ($27.91^\circ\text{N}, 85.16^\circ\text{E}$), north through Trishuli Bazar, Betrawati, Mailung, Dhunche ($28.11^\circ\text{N}, 85.30^\circ\text{E}$), and Syaphrubesi ($28.16^\circ\text{N}, 85.33^\circ\text{E}$).
- **Topographic Context:**
  - Steep, high-relief Himalayan gorge prone to torrential flash floods, debris flows, and rainfall-triggered landslides.
  - Critical radar imaging constraints: Mountain slopes cause severe radar layover and shadow on steep flanks, requiring topographic slope masking ($\ge 25^\circ$) to avoid false-positive water classifications.

---

## 2. Authentic Sentinel-1 Satellite Orbit Pair Evaluation

Queried directly against the live European Space Agency (ESA) Copernicus Data Space Ecosystem (CDSE) production catalogue:

| Observation Pair | Relative Orbit & Pass | Pre-Event Acquisition (UTC) | Post-Event Acquisition (UTC) | Post-Event Lag (Proximity to Event) | Baseline | Polarizations | AOI Coverage |
|---|---|---|---|---|---|---|---|
| **Primary Scientific Choice** | **Orbit 85 (ASCENDING)** | **2026-08-16 12:21:41** | **2026-08-28 12:21:41** | **+2.5 days (48–60 hrs)** | **12.0 days** | **VV & VH** | **100.0%** |
| **Alternate Choice** | **Orbit 19 (DESCENDING)** | **2026-08-24 00:18:44** | **2026-09-05 00:18:44** | **+10.0 days** | **12.0 days** | **VV & VH** | **100.0%** |
| Rejected Partial | Orbit 121 (DESCENDING) | 2026-08-19 00:10:36 | 2026-08-31 00:10:37 | +5.0 days | 12.0 days | VV & VH | 11.8% (REJECTED) |

### Scientific Comparability & Selection Rationale:
1. **Primary Recommended Pair: Relative Orbit 85 (ASCENDING)**
   - **Post-Event Timing:** Captured on **August 28, 2026 at 12:21:41 UTC**, only **2.5 days (~48 hours)** after the peak flooding event of August 26, 2026. In steep Himalayan river gorges, flash flood inundation rapidly recedes; capturing observations within 48 hours is critical to observing genuine inundation extents before drainage occurs.
   - **Pre-Event Timing:** Captured on August 16, 2026 at 12:21:41 UTC (9.5 days prior to the event).
   - **Geometry:** Identical ascending orbital trajectory and look angle, exactly 12.0 days apart (one full Sentinel-1 repeat cycle).
   - **Authentic CDSE Product Identifiers:**
     - Pre-event: `S1D_IW_GRDH_1SDV_20260816T122141_20260816T122206_004151_007980_B091_COG.SAFE`
     - Post-event: `S1D_IW_GRDH_1SDV_20260828T122141_20260828T122206_004326_007FA4_01B4.SAFE`

2. **Alternate Baseline Pair: Relative Orbit 19 (DESCENDING)**
   - Pre-event acquisition on August 24, 2026 (only 2 days prior to event).
   - Post-event acquisition on September 5, 2026 (10 days post-event; substantial water recession expected).
   - **Authentic CDSE Product Identifiers:**
     - Pre-event: `S1D_IW_GRDH_1SDV_20260824T001844_20260824T001909_004260_007D5D_45FC_COG.SAFE`
     - Post-event: `S1D_IW_GRDH_1SDV_20260905T001844_20260905T001909_004435_00837B_60FD_COG.SAFE`

---

## 3. Scientific Defect Resolutions (Phase 1.7)

### Defect A — Pixel-Value Guessing Removal
- **Defect:** `varuna/jobs/pipeline.py` previously contained an empirical fallback that inspected min and max pixel values (`np.nanmin(arr) < -2.0 and np.nanmax(arr) <= 10.0`) to guess whether an untagged raster was in decibels.
- **Resolution:** The guessing fallback has been completely removed. Every production input raster MUST provide explicit, trustworthy calibration metadata (`SAR_UNIT="DECIBELS_DB"` or `SAR_UNIT="LINEAR_POWER"`). Ambiguous or untagged rasters fail closed immediately with `MissingCalibrationError`.

### Defect B — Missing Terrain Correction & Scientific Rigor
- **Defect:** Python-native calibration and spatial resampling were previously presented without clear delineation from rigorous SAR Range-Doppler Terrain Correction.
- **Resolution:**
  - Range-Doppler Terrain Correction requires the European Space Agency SNAP Graph Processing Tool (`gpt`), utilizing precise orbit state vectors and Digital Elevation Models (SRTM 3Sec or Copernicus 30m Global DEM).
  - Added `TerrainCorrectionUnavailableError`: when research-grade Range-Doppler Terrain Correction is demanded (`require_range_doppler=True`) on a system lacking ESA SNAP, the engine fails closed rather than silently downgrading to an unverified method.
  - When running Python-native Level-1 calibration, exported GeoTIFF metadata explicitly records:
    - `TERRAIN_CORRECTION="NONE_PYTHON_NATIVE_APPROXIMATION"`
    - `RANGE_DOPPLER_APPLIED="FALSE"`
    - `DEM_SOURCE="NONE"`
    - `TARGET_CRS="EPSG:4326"`
    - `RESOLUTION_METERS="10.0"`

### Defect C — Invented Metadata Defaults Elimination
- **Defect:** `varuna/preprocessing/sentinel1.py` previously provided fallback default assumptions (`sensor_mode="IW"`, `orbit_dir="DESCENDING"`, `rel_orbit=0`) when annotation XML parsing failed.
- **Resolution:**
  - Fallbacks have been eliminated. The SAFE inspector strictly parses `<mode>`, `<productType>`, `<pass>`, `<relativeOrbitNumber>`, `<startTime>`, and `<stopTime>` directly from the annotation XML.
  - If any critical XML tag is missing, corrupted, or invalid, parsing fails closed with `CorruptSAFEProductError`.
  - Added `Sentinel1ProductInspector.validate_pair_compatibility()` to strictly reject incompatible pre/post pairs (mismatched relative orbits, opposing pass directions, or conflicting sensor modes) via `IncompatibleSAFEProductPairError`.

### Defect D — Polarization Substitution Prohibition
- **Defect:** `varuna/preprocessing/sentinel1.py` previously fell back to `meta.polarizations[0]` if the requested polarization was unavailable.
- **Resolution:**
  - Silent polarization switching has been completely eliminated.
  - If the requested polarization (e.g. `VV`) is not present in the SAFE product, the processor raises `IncompatiblePolarizationError`.
  - Pair compatibility validation requires explicit common polarization across both pre and post acquisitions.

---

## 4. Copernicus Data Space Authentication & Environment Setup

To execute full binary downloads from the Copernicus Data Space Ecosystem:

1. **Create a Free Account:**
   - Register at the Copernicus Data Space portal: `https://dataspace.copernicus.eu`
   - Complete email verification and activate your Copernicus Keycloak account.

2. **Configure Environment Variables:**
   Create or edit a local `.env` file in the repository root (which is `.gitignore`d to prevent accidental credential leakage):
   ```bash
   # .env
   CDSE_USERNAME="your-registered-email@example.com"
   CDSE_PASSWORD="your-copernicus-password"
   ```

3. **Security Safeguards:**
   - Never print, log, or commit `.env` credentials.
   - If credentials are absent, VARUNA automatically halts at the authentication boundary in `JobStatus.AWAITING_AUTHENTICATION` without fabricating dummy data or claiming completed processing.

---

## 5. ESA SNAP Installation Instructions for Range-Doppler Terrain Correction

For full Range-Doppler Terrain Correction:
1. Download ESA SNAP from: `https://step.esa.int/main/download/snap-download/`
2. Install SNAP and ensure `gpt` (Graph Processing Tool) is added to your system `PATH`:
   ```bash
   export PATH="/Applications/snap/bin:$PATH"  # macOS
   # or
   export PATH="/usr/local/snap/bin:$PATH"       # Linux
   ```
3. Test availability:
   ```bash
   gpt -h
   ```
   VARUNA automatically verifies that `gpt` is the ESA SNAP Graph Processing Tool (and distinguishes it from the macOS GUID partition table command `/usr/sbin/gpt`).

---

## 6. Independent Reference Validation (Copernicus EMS EMSR927)

### Verification of EMSR927 Activation:
- **Event Match:** Copernicus EMS activation **EMSR927** was requested on **August 26, 2026** specifically for the **Rasuwa District, Central Nepal flash flood / GLOF event**.
- **Area of Interest Match:** EMSR927 delineated the exact Trishuli River corridor encompassing **Syapru Besi**, **Timure**, and **Bidur**.
- **Sensor & Observation Period Discrepancy:**
  - EMSR927 damage grading products were produced using ultra-high-resolution optical imagery (**WorldView-3 at 0.3m**, **Pléiades Neo**) captured during clear sky conditions.
  - Flash floods in the steep Himalayan Trishuli gorge recede rapidly; high-resolution optical grading captures the high-water debris/scour line, whereas Sentinel-1 SAR repeat-pass captures standing surface water 48 hours post-peak.
- **Local Reference Vector Availability:**
  - Ground-truth GIS shapefiles/GeoJSON vectors from EMSR927 are not present locally in the repository.
  - **Scientific Rule:** Because authentic vector layers are not present locally, **no synthetic validation metrics or fabricated confusion matrices are reported**.
  - All satellite-detected backscatter anomalies are strictly reported as **candidate inundation**, and distinguished from confirmed inundation.

---

## 7. Scientific Safety Checks (Mandatory Protocols)

1. **Radar Brightening $\ne$ Confirmed Debris:**
   Radar backscatter increases ($\ge +3.5\text{ dB}$) are classified as `CANDIDATE_DEBRIS_OR_ROUGHENING` (radar surface coarsening). They must never be reported as confirmed structural debris flows without optical or field verification.
2. **Water Intersections $\ne$ Confirmed Road Closures:**
   Intersections between candidate water polygons and OpenStreetMap road vectors are classified as `POTENTIAL_INFRASTRUCTURE_EXPOSURE`, not confirmed physical closures.
3. **Settlement Accessibility Requires Defensible Road Models:**
   Settlements are only evaluated for isolation using topological graph analysis (`MultiGraph` routing with geodesic distance and elevation/bridge layering). Settlements must not be reported as isolated without a defensible road network model.
4. **Heuristic Uncertainty $\ne$ Calibrated Confidence:**
   Empirical margin indices are uncalibrated classification metrics, not Bayesian posterior probabilities.
5. **Valid File Exports $\ne$ Ground-Truth Accuracy:**
   Successfully exporting valid GeoTIFFs verifies spatial integrity, CRS, and formatting, but does NOT constitute evidence of accurate physical predictions.
6. **Synthetic Fixtures $\ne$ Real Observations:**
   Synthetic NumPy fixtures are strictly confined to `tests/fixtures/` and are rejected with errors in research runs.

---

## 8. Execution Evidence & Blocker Status

Executed live via `scripts/run_nepal_experiment.py` on 2026-10-11:

### Authentic CDSE Query & Authentication Boundary Halt
- **Endpoint Queried:** `https://catalogue.dataspace.copernicus.eu/odata/v1/Products` (`HTTP 200 OK`)
- **Products Discovered:** 16 authentic Sentinel-1 GRD products over Trishuli AOI.
- **Job Status:** `JobStatus.AWAITING_AUTHENTICATION` (30% progress).
- **Diagnostics:**
  ```text
  Authentication required: CDSE credentials (CDSE_USERNAME / CDSE_PASSWORD) not configured in environment.
  Binary Sentinel-1 product download halted at authentication boundary.
  To process satellite rasters, configure .env with Copernicus credentials or supply pre-downloaded scene paths.
  ```
- **Scientific Integrity Verification:**
  - The pipeline cleanly halted at the authentication boundary without fabricating binary data.
  - No synthetic imagery was used or represented as observed flood damage.
  - Job status was honestly reported as `AWAITING_AUTHENTICATION` and never `COMPLETED`.

---

## 9. Software & Environment Versions

- OS: macOS (Darwin 24.6.0, arm64)
- Python: 3.14.7
- `rasterio`: 1.5.2
- `geopandas`: 1.2.0
- `shapely`: 2.2.0
- `pyproj`: 3.8.0
- `networkx`: 3.7
- `scipy`: 1.18.1
- `fastapi`: 0.143.0
- `pytest`: 9.1.1
- ESA SNAP `gpt`: Not installed (Python-native XML calibration active)
