# VARUNA — Live Experiment Log

**Sprint:** Phase 1.5 Scientific Integrity Repair  
**Experiment ID:** `EXP-2026-08-TRISHULI-01`  
**Target Event:** August 26, 2026 Trishuli Flood, Nepal  
**Case Study Geography:** Trishuli River Valley & Gorge (Rasuwa & Nuwakot Districts, Central Nepal)  
**Execution Timestamp:** 2026-10-11T04:20:55Z  

---

## 1. Study Area Geography & Case Study Boundaries

- **Geographic Extent:**
  - Latitude: $27.90^\circ\text{N}$ to $28.20^\circ\text{N}$
  - Longitude: $85.10^\circ\text{E}$ to $85.35^\circ\text{E}$
- **Coverage Description:**
  - Encompasses the Trishuli River drainage from the confluence with Tadi Khola at Bidur/Battar ($27.91^\circ\text{N}, 85.16^\circ\text{E}$), north through Trishuli Bazar, Betrawati, Mailung, Dhunche ($28.11^\circ\text{N}, 85.30^\circ\text{E}$), and Syaphrubesi ($28.16^\circ\text{N}, 85.33^\circ\text{E}$).
- **Topographic Context:**
  - Steep, high-relief Himalayan gorge prone to torrential flash floods, debris flows, and co-seismic/rainfall-triggered landslides.
  - Critical radar challenges: Mountain slopes cause radar layover and shadow on steep flanks, requiring topographic masking.

---

## 2. Authentic Sentinel-1 Satellite Acquisitions

Queried against the live production European Space Agency / Copernicus Data Space Ecosystem (CDSE) catalogue:

| Observation | Product Identifier | Acquisition Timestamp (UTC) | Relative Orbit | Orbit Direction | Mode | Polarization | AOI Coverage |
|---|---|---|---|---|---|---|---|
| **Pre-Event** | `S1D_IW_GRDH_1SDV_20260824T001844_20260824T001909_004260_007D5D_45FC_COG.SAFE` | **2026-08-24 00:18:44 UTC** | **19** | **DESCENDING** | IW | VV & VH | **100.0%** |
| **Post-Event** | `S1D_IW_GRDH_1SDV_20260905T001844_20260905T001909_004435_00837B_60FD_COG.SAFE` | **2026-09-05 00:18:44 UTC** | **19** | **DESCENDING** | IW | VV & VH | **100.0%** |

### Geometric Comparability Analysis:
- **Repeat Pass Orbit:** Both scenes share Relative Orbit 19 with identical track timing (00:18:44 UTC), providing identical radar incidence angles and look geometry.
- **Temporal Baseline:** Exactly **12.0 days** (one complete orbital cycle of Sentinel-1), minimizing false positives from seasonal vegetation growth.
- **Timing Relation:** Pre-event observation occurred 2 days before the event; post-event observation occurred 10 days post-event.
- **Alternative Ascending Orbit Pair Discovered:**
  - Orbit 85 ASCENDING: Pre-event `2026-08-16 12:21:41 UTC` and Post-event `2026-08-28 12:21:41 UTC` (2 days post-event, 12-day temporal baseline).

---

## 3. Processing Parameters & Scientific Workflow

1. **Radiometric Calibration:**
   - Raw DN calibrated via Sentinel-1 calibration LUT vector: $\sigma^0_{\text{linear}} = |DN|^2 / A_{\sigma}^2$.
   - Converted to decibels: $\sigma^0_{\text{dB}} = 10 \log_{10}(\sigma^0_{\text{linear}})$.
   - Valid data mask applied (non-physical and border zeros masked).
2. **Speckle Filtering:**
   - Spatial adaptive Lee filter ($5 \times 5$ window, Equivalent Number of Looks $= 4.4$).
   - Executed strictly in the **linear intensity domain** to prevent logarithmic transformation bias.
3. **Common Analysis Grid (CAG):**
   - Reprojection to EPSG:4326 with standard 10m spatial resolution.
   - Bilinear resampling with boundary nodata preservation.
4. **Change Classification Thresholds:**
   - Candidate Water Inundation: $\Delta \sigma^0_{\text{dB}} \le -3.5\text{ dB}$ (specular backscatter drop).
   - Candidate Debris / Roughening: $\Delta \sigma^0_{\text{dB}} \ge +3.5\text{ dB}$ (surface coarsening/gravel).
   - Permanent Water Mask: Both Pre and Post $\le -16.0\text{ dB}$.
   - Steep Slope Shadow Flag: Mountain terrain slopes $\ge 25^\circ$.
5. **OpenStreetMap Road Network:**
   - Pre-event snapshot date: `2026-08-15T00:00:00Z` (11 days prior to event).
   - Noding: Junction segmentation with layer separation (`layer=1` bridges vs `layer=0` roads).
   - Distance Metrics: WGS84 Geodesic distance via `pyproj.Geod` (no planar degree approximations).

---

## 4. External Dependencies & Execution Blockers

1. **Copernicus Data Space Ecosystem (CDSE) Raw Binary Transfer:**
   - **Status:** Catalogue discovery and metadata verification **100% operational** and validated against live ESA servers.
   - **Blocker:** Downloading multi-gigabyte raw `.SAFE.zip` archives requires authenticated user registration via Keycloak OAuth2 (`CDSE_USERNAME` and `CDSE_PASSWORD`).
   - **Behavior:** The system cleanly halts at the authenticated download boundary, records the exact missing credential, and generates reproducible job records without fabricating binary data.

2. **OpenStreetMap Overpass API:**
   - **Status:** Query builder enforces point-in-time snapshot constraint `[date:"2026-08-15T00:00:00Z"]`.
   - **Network Rate Limit:** Public Overpass endpoints subject to community rate limiting; local cached pre-event OSM extracts recommended for offline judge demonstrations.

---

## 5. Software & Environment Versions

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
