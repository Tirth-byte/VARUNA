# VARUNA — Scientific Experiment Log

**Sprint:** Phase 1.6 Authentic Satellite Data & Scientific Integrity  
**Experiment ID:** `EXP-2026-08-TRISHULI-AUTHENTIC-01`  
**Target Event:** August 26, 2026 Trishuli Flood, Central Nepal  
**Case Study Geography:** Trishuli River Valley & Gorge (Rasuwa & Nuwakot Districts, Central Nepal)  
**Execution Timestamp:** 2026-10-11T13:14:02Z  
**Core Scientific Principle:** *"If we cannot verify it, we do not present it as fact."*

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
     - Pre-event: `S1D_IW_GRDH_1SDV_20260816T122141_20260816T122206_004151_007980_B091_COG.SAFE` (and `.SAFE`)
     - Post-event: `S1D_IW_GRDH_1SDV_20260828T122141_20260828T122206_004326_007FA4_01B4.SAFE` (and `_COG.SAFE`)

2. **Alternate Baseline Pair: Relative Orbit 19 (DESCENDING)**
   - Pre-event acquisition on August 24, 2026 (only 2 days prior to event).
   - Post-event acquisition on September 5, 2026 (10 days post-event; substantial water recession expected).
   - **Authentic CDSE Product Identifiers:**
     - Pre-event: `S1D_IW_GRDH_1SDV_20260824T001844_20260824T001909_004260_007D5D_45FC_COG.SAFE` (and `.SAFE`)
     - Post-event: `S1D_IW_GRDH_1SDV_20260905T001844_20260905T001909_004435_00837B_60FD_COG.SAFE` (and `.SAFE`)

---

## 3. Rigorous Sentinel-1 Preprocessing Specifications

1. **Radiometric Calibration:**
   - Raw Sentinel-1 Level-1 GRD Digital Numbers ($DN$) calibrated to linear $\sigma^0$ intensity:
     $$\sigma^0_i = \frac{|DN_i|^2 - \text{noise}_i^2}{A_{\sigma, i}^2}$$
     where $A_{\sigma}$ is the calibration vector extracted from `annotation/calibration/calibration-s1*-iw-grd-<pol>-*.xml` and interpolated in 2D across line and pixel coordinates.
   - Converted to physical decibels: $\sigma^0_{\text{dB}} = 10 \log_{10}(\sigma^0_{\text{linear}})$.
   - **Prohibited:** Pixel-value-based unit guessing and arbitrary scalar calibration constants (e.g. 100.0) are completely eliminated.

2. **Thermal & Border Noise Removal:**
   - Noise floor subtraction using calibration XML vectors.
   - Border noise removal masking zero/low boundary samples characteristic of Sentinel-1 GRD azimuth/range edges.

3. **Speckle Filtering:**
   - Multiplicative spatial adaptive Lee filter ($5 \times 5$ window, Equivalent Number of Looks $= 4.4$ for IW GRDH).
   - Executed strictly in the **linear intensity domain** to prevent logarithmic transformation bias, then converted back to decibels.

4. **Common Analysis Grid (CAG) & Alignment:**
   - Reprojection to EPSG:4326 with standard 10m spatial resolution.
   - Joint valid overlap mask ensuring only co-observed terrain is evaluated.

5. **Scientific Flood Detection Definitions:**
   - **Candidate Water Inundation:** $\Delta \sigma^0_{\text{dB}} \le -3.5\text{ dB}$ (specular backscatter drop).
   - **Candidate Surface Roughening:** $\Delta \sigma^0_{\text{dB}} \ge +3.5\text{ dB}$ (surface coarsening/gravel).
   - **Caveat:** Candidate water drop does not equate to confirmed structural damage. Backscatter increase does not equate to confirmed debris. Heuristic uncertainty is an uncalibrated margin index, not a calibrated posterior probability.

---

## 4. Execution Evidence & Blocker Status

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

## 5. Software Test Evidence (Synthetic Fixture Disclaimers)

> [!WARNING]
> **SYNTHETIC TEST OUTPUTS — NOT OBSERVED NEPAL FLOOD DAMAGE**
> 
> Historical software runs executing against synthetic NumPy test fixtures produced:
> - Water candidate area: 20.17 km²
> - Roughening area: 2.61 km²
> 
> **These numbers are synthetic software test fixture outputs generated for pipeline unit testing.**
> They do **NOT** represent real observations of Nepal and must **NEVER** be cited as research findings or flood intelligence.
> In accordance with Phase 1.6 standards, synthetic fixtures have been isolated to `tests/fixtures/synthetic_fixtures.py` and are strictly rejected from research-grade pipeline executions.

---

## 6. Software & Environment Versions

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
