# VARUNA — Implementation Status

**Phase 1 Completed:** Scientific Engineering & Project Foundation  
**System Objective:** Multimodal AI Hackathon 2026 — Track B: Mapping Flood Damage from Space  
**Primary Case Study:** August 26, 2026 Trishuli Flood, Nepal  
**Core Principle:** *"If we cannot verify it, we do not present it as fact."*

---

## 1. Initial State vs. Completed Phase 1 Work

### Initial State (Prior to Phase 1)
- Minimal static contracts file (`varuna/contracts.py`) containing basic `RadarScene` dataclass.
- 4 basic tests in `varuna/test_contracts.py`.
- Report template outline (`RESEARCH_REPORT_TEMPLATE.md`).
- Missing: Satellite discovery, CDSE API integration, SAR preprocessing, speckle filtering, change detection baseline, OpenStreetMap road network connectivity, data leakage controls, FastAPI REST service, test suite.

### Phase 1 Completed Capabilities
1. **Satellite Acquisition Engine (`varuna/acquisition/`):**
   - Implemented `CDSEDiscoveryService` querying the official Copernicus Data Space Ecosystem OData v1 catalogue (`https://catalogue.dataspace.copernicus.eu/odata/v1`).
   - Verified against live Copernicus production API, discovering authentic Sentinel-1 GRD IW acquisitions.
   - Enforced geometric comparability: identical relative orbit, identical pass direction (ASCENDING/DESCENDING), identical polarization, minimum AOI coverage threshold, and temporal bracketing.
   - Built `CDSEDownloader` with Keycloak OAuth2 authentication handling and fail-closed security preventing false download claims.

2. **Geospatial Preprocessing Foundation (`varuna/preprocessing/`):**
   - Radiometric calibration: raw Digital Numbers (DN) to Sigma0 backscatter in decibels ($\sigma^0_{\text{dB}}$).
   - Adaptive Lee speckle filter with Equivalent Number of Looks (ENL) parameterization.
   - Physical valid-data masking and boundary/nodata handling.
   - Mountain terrain artifact & radar shadow flagging using slope thresholds.
   - Raster inspection, CRS compatibility verification, and spatial grid alignment via `rasterio.warp.reproject`.

3. **Transparent Baseline Change Detection (`varuna/detection/`):**
   - Multi-class change detection engine:
     - `CANDIDATE_WATER_INUNDATION` ($\Delta \text{dB} \le \tau_{\text{water}}$)
     - `CANDIDATE_DEBRIS_OR_ROUGHENING` ($\Delta \text{dB} \ge \tau_{\text{debris}}$)
     - `PERMANENT_WATER` ($\text{Pre}_{\text{dB}} \le -16 \text{ dB} \land \text{Post}_{\text{dB}} \le -16 \text{ dB}$)
     - `TERRAIN_SHADOW_SUSPECT` (low backscatter on steep mountain slopes)
     - `NO_SIGNIFICANT_CHANGE`
   - Configurable manual thresholds and adaptive Otsu thresholding on negative change distribution.
   - Continuous pixel uncertainty quantification.
   - Vectorization to GeoPandas GeoDataFrame and multi-band GeoTIFF export.

4. **Road Network Accessibility & Settlement Isolation (`varuna/osm/network.py`):**
   - Strict temporal guard: requires pre-event OpenStreetMap snapshot; rejects post-event data to prevent leakage.
   - NetworkX graph construction from road LineStrings, bridges, and settlement nodes.
   - Road exposure intersection: marks segments as `POTENTIALLY_EXPOSED` (explicitly distinguishing remote-sensing exposure from confirmed physical destruction).
   - Graph reachability analysis: identifies settlements that lose all connectivity to critical hubs (hospitals, towns).

5. **Scientific Anti-Leakage Separation (`varuna/validation/leakage_guard.py`):**
   - Structural boundary separating prediction inputs (Sentinel-1, pre-event OSM, DEM) from prohibited reference layers (Copernicus EMS EMSR927, UNOSAT).
   - Explicit `DatasetRole` enforcement preventing reference damage assessments from entering prediction models.

6. **FastAPI Engine (`varuna/api/`):**
   - `GET /api/v1/health`: System health, library versions, credential status.
   - `POST /api/v1/scenes/discover`: Live or offline CDSE Sentinel-1 discovery with orbit compatibility.
   - `POST /api/v1/detection/baseline`: Change detection execution returning GeoJSON and uncertainty metrics.
   - `POST /api/v1/analysis/exposure`: Infrastructure exposure and settlement isolation analysis.

---

## 2. Test Suite Execution & Results

**All 28 tests passing cleanly (100% pass rate in 0.51s):**

| Test Module | Tests | Status | Scope |
|---|---|---|---|
| `varuna/test_contracts.py` | 4 | **PASS** | Orbit matching, temporal bracketing, OSM temporal guard |
| `tests/test_cdse_discovery.py` | 4 | **PASS** | CDSE OData parsing, orbit mismatch rejection, auth requirement |
| `tests/test_sar_preprocessing.py` | 5 | **PASS** | DN-to-dB calibration, Lee speckle filter variance reduction, CRS comparability |
| `tests/test_baseline_change.py` | 4 | **PASS** | Water vs debris differentiation, terrain shadow flagging, Otsu, vectorization |
| `tests/test_osm_connectivity.py` | 3 | **PASS** | Post-event OSM rejection, bridge cut simulation, alternative path resilience |
| `tests/test_leakage_guard.py` | 4 | **PASS** | EMSR927 input rejection, temporal leakage protection, role enforcement |
| `tests/test_api.py` | 4 | **PASS** | Health endpoint, baseline change endpoint, OSM temporal validation, exposure endpoint |

**Total:** 28 passed, 0 failed.

---

## 3. External Dependencies & Live System Verification

1. **Copernicus Data Space Ecosystem (CDSE):**
   - Catalogue OData v1 API: **VERIFIED WORKING LIVE**. Tested against live query over Trishuli, Nepal ($85.1^\circ\text{E}$ to $85.35^\circ\text{E}$, $27.8^\circ\text{N}$ to $28.05^\circ\text{N}$). Returned real Sentinel-1 GRD IW acquisitions.
   - Download Endpoint: Requires `CDSE_USERNAME` and `CDSE_PASSWORD` (or `CDSE_CLIENT_ID` / `CDSE_CLIENT_SECRET`) in `.env`. Downloader correctly raises `AuthenticationRequiredError` when missing credentials rather than faking data.

2. **Installed Geospatial Environment:**
   - Python: 3.14.7
   - `rasterio`: 1.5.2
   - `geopandas`: 1.2.0
   - `shapely`: 2.2.0
   - `pyproj`: 3.8.0
   - `networkx`: 3.7
   - `scipy`: 1.18.1
   - `fastapi`: 0.143.0
   - `pydantic`: 2.14.0

---

## 4. Next Implementation Actions (Phase 2 Roadmap)

1. **Copernicus DEM & Topographic Corrections:**
   - Integrate Copernicus 30m Global DEM (GLO-30) for range Doppler terrain correction and shadow masking in Trishuli's high-relief valleys.
2. **Multi-temporal Optical Cross-Validation:**
   - Ingest cloud-screened Sentinel-2 pre/post imagery for visual validation where cloud cover permits.
3. **Copernicus EMS EMSR927 Validation Benchmark:**
   - Build independent quantitative evaluation suite comparing VARUNA candidate detections against held-out EMSR927 delineation layers (precision, recall, IoU, confusion matrix).
4. **Editorial Map Interface:**
   - Build Next.js / MapLibre GL frontend adhering strictly to the VARUNA design constitution (white/black editorial typography, restrained `#16B300` / `#087D48` accents, scientific hazard color schemes).
