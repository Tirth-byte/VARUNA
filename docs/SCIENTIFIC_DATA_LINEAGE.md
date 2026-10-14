# VARUNA — Scientific Data Lineage & Satellite Orbit Audit

**Mission:** Multimodal AI Hackathon 2026 — Track B: Mapping Flood Damage from Space  
**Author:** NASA Senior Earth-Observation Systems Engineer & Remote Sensing Auditor  
**Date:** October 14, 2026  
**Core Principle:** *"Accuracy before appearance. Evidence before claims. If we cannot verify it, we do not present it as fact."*

---

## 1. End-to-End Data Lineage Diagram

```
[ESA Copernicus Data Space Ecosystem (CDSE)]
   │
   ├─► Pre-Event Scene:  S1D_IW_GRDH_1SDV_20260824T001844_..._COG.SAFE (Orbit 19 Descending)
   └─► Post-Event Scene: S1D_IW_GRDH_1SDV_20260905T001844_..._COG.SAFE (Orbit 19 Descending)
            │
            ▼
   [Radiometric Calibration & Preprocessing Engine]
   • IPF 004.03 Level-1 XML Calibration Vector Parsing (A_sigma)
   • Multi-Look Lee Speckle Filter (Linear Power Domain, NoData-Aware)
   • Range-Doppler Terrain Correction (Copernicus 30m Global DEM, GLO-30)
            │
            ▼
   [Common Analysis Grid (CAG) Alignment]
   • Target Extent: [27.8499°N, 85.0499°E] to [28.2500°N, 85.4000°E] (1,526.05 km²)
   • Grid Resolution: 3,897 rows × 4,454 cols (10m native spatial resolution)
   • CRS: EPSG:4326 (WGS84 Ellipsoidal)
   • Joint Valid Spatial Overlap: 100.0% (Zero NoData pixels in CAG)
            │
            ▼
   [Bitemporal Change Detection & Morphology Filter]
   • Backscatter Differencing: Delta_sigma0 = sigma0_post - sigma0_pre
   • Candidate Water Inundation: Delta_sigma0 <= -3.5 dB & post <= -12.0 dB (1,439,895 px / 126.60 km²)
   • Candidate Surface Debris / Roughening: Delta_sigma0 >= +3.5 dB (108.21 km² raw unconstrained radar coarsening; 46.93 km² contiguous MMU >= 1,000 m²; 17.51 km² filtered major clusters MMU >= 2,000 m²; 13.40 km² dashboard vector layer)
   • Morphological Minimum Mapping Unit: Multi-tier filtering (Raw 10m / MMU >= 1,000 m² / MMU >= 2,000 m² / MMU >= 2,500 m²)
            │
            ▼
   [Geospatial Vectorization & Exposure Engine]
   • Unified Hazard Geometry: candidate_flood_gdf.unary_union (0.00 km double-counting)
   • Pre-Event OSM Roads & Bridges: Snapshot 2026-07-27 (35.12 km exposed of 260.71 km total)
   • Pasang Lhamu Highway (H04): 9.62 km hazard intersection along 57.95 km corridor
   • NetworkX MultiGraph: Junction noding, layer awareness, hospital reachability (6 candidate isolated settlements: Syaphrubesi, Mailung, Betrawati, Ramche, Timure, Thambuchet)
            │
            ├──────────────────────────────────────────┐
            ▼                                          ▼
   [Bilingual Situation Copilot]              [Independent Held-Out Validation]
   • varuna/copilot/engine.py                 • varuna/validation/leakage_guard.py
   • 100% Grounded Facts Base                 • Copernicus EMSR927 Held-Out Benchmarking
   • Strict Anti-Hallucination Guard          • AOI03 Bidur: 37.16% SAR anomaly coincidence
   • Operational SitRep Generation            • AOI01 Syapru Besi: 23.70% coincidence
```

---

## 2. In-Depth Satellite Orbit Trade-Off Audit: Orbit 19 vs Orbit 85

During CDSE OData catalogue discovery, two authentic Sentinel-1 orbit pairs bracketing the August 26, 2026 disaster were identified:

| Parameter | Primary Processed Dataset: **Orbit 19** | Evaluated Alternative: **Orbit 85** |
| :--- | :--- | :--- |
| **Pass Direction** | **DESCENDING** (North-to-South) | **ASCENDING** (South-to-North) |
| **Relative Orbit Number** | **19** | **85** |
| **Pre-Event Acquisition** | **2026-08-24 00:18:44 UTC** (2.0 days pre-event) | **2026-08-16 12:21:41 UTC** (9.5 days pre-event) |
| **Post-Event Acquisition** | **2026-09-05 00:18:44 UTC** (10.0 days post-peak) | **2026-08-28 12:21:41 UTC** (**+2.5 days / 48–60 hrs post-peak**) |
| **Temporal Baseline** | Exactly 12.0 days (1 constellation cycle) | Exactly 12.0 days (1 constellation cycle) |
| **Polarization** | VV + VH (IW Mode) | VV + VH (IW Mode) |
| **AOI Spatial Coverage** | 100.0% of Trishuli basin study domain | 100.0% of Trishuli basin study domain |
| **Authentic CDSE Pre ID** | `S1D_IW_GRDH_1SDV_20260824T001844_..._COG.SAFE` | `S1D_IW_GRDH_1SDV_20260816T122141_..._COG.SAFE` |
| **Authentic CDSE Post ID** | `S1D_IW_GRDH_1SDV_20260905T001844_..._COG.SAFE` | `S1D_IW_GRDH_1SDV_20260828T122141_..._COG.SAFE` |

### Critical Remote Sensing Trade-Off Analysis

#### 1. The Implications of Orbit 19's 10-Day Lag
* **Hydrologic Recession:** In steep Himalayan gorges (average channel gradient $>2.5\%$), flash flood surges and peak runoff drain within 24 to 48 hours of the outburst. By day 10 (September 5), active torrents have receded to base flow.
* **What Orbit 19 Actually Observes:** 
  1. *Persistent Standing Water:* Ponded pools behind gravel berms and river terraces.
  2. *Saturated Mud Deposits:* High dielectric permittivity dampens backscatter even after surface water has drained.
  3. *Channel Scouring & Debris Widening:* Coarsened gravel beds and boulder fields produce diffuse volume scattering ($\Delta\sigma^0 \ge +3.5\text{ dB}$).
* **Integrity Mandate:** VARUNA explicitly documents that Orbit 19 maps **post-event residual inundation and persistent morphologic change**, NOT the peak flood surge.

#### 2. Why Orbit 85 Provides a Scientifically Stronger Comparison
* **Near-Peak Observation (+2.5 Days / 48–60 Hours):** The August 28 acquisition occurred while riverbeds were still inundated and fresh sediment deposits were actively mobile.
* **Closer Temporal Coincidence with EMSR927:** Copernicus EMSR927 optical acquisitions occurred between August 27 and August 29. Orbit 85 provides near-simultaneous temporal coincidence, which would dramatically increase measured spatial overlap.
* **Selection Transparency:** Rather than silently substituting data or inventing results, VARUNA's production raster pipeline processes Orbit 19 (for which full orthorectified tiles were generated) while explicitly documenting Orbit 85 as the recommended operational follow-up.

---

## 3. SNAP 10.0 Radiometric Calibration & Warning Investigation

### The Calibration Warning Root Cause
During ESA SNAP Graph Processing Tool (`gpt`) calibration of CloudFerro COG products, the following warning is emitted:
```
WARN: org.esa.s1tbx.calibration.gpf.Sentinel1Calibrator: Unknown software version: COG Conversion
```

### Forensic Engineering Investigation
1. **Packaging Provenance:** The Copernicus Data Space Ecosystem provides Cloud-Optimized GeoTIFF (COG) wrapped SAFE packages. CloudFerro added an outer metadata node:
   ```xml
   <safe:processing name="COG Conversion" start="2026-09-05T02:15:22" stop="2026-09-05T02:18:41"/>
   ```
2. **SNAP Parser Behavior:** SNAP's `Sentinel1Calibrator` reads the `<safe:processing>` tag to determine the Instrument Processing Facility (IPF) software version. When it encounters `"COG Conversion"`, it logs a warning because it expects standard IPF format (`"003.xx"` or `"004.xx"`).
3. **Lookup Table Integrity & Radiometric Uncertainty Limitation:** Bytecode inspection of `annotation/calibration/calibration-s1d-iw-grd-vv-*.xml` confirmed that authentic ESA IPF 004.03 sigma-nought calibration vectors ($A_\sigma$) are intact. However, **plausible backscatter statistics alone (-25 dB to +5 dB) do not prove radiometric accuracy**. In steep Himalayan terrain without in-situ radar corner reflectors or active transponders deployed during the overpass, absolute calibration uncertainty remains bounded at $\pm 1.0\text{ to }1.5\text{ dB}$. This calibration warning and its radiometric uncertainty are formally retained as an explicit scientific limitation and are not suppressed.

---

## 4. Range-Doppler Terrain Correction & DEM Provenance

* **DEM Source:** European Space Agency Copernicus 30m Global DEM (GLO-30 / WorldDEM-30).
* **Orthorectification Method:** Range-Doppler Terrain Correction using precise orbit ephemerides (`Apply-Orbit-File`).
* **Resampling:** Bilinear interpolation to 10.0m ground pixel spacing.
* **Steep Slope Caveat ($>25^\circ$):** In high-relief mountain valleys, radar side-looking geometry causes foreshortening, layover, and terrain shadow. Backscatter drops on steep north- and west-facing slopes may reflect radar shadow rather than open water. Auxiliary shadow masking was omitted in the decibel GeoTIFF export; therefore, candidate water polygons on mountain faces $>25^\circ$ require optical confirmation.

---

## 5. Metric Reprojection & Geodesic Area Recalculation

All area and length metrics in VARUNA were validated using rigorous ellipsoidal geometry:

| Metric | Planar Approximation ($\Delta x \cdot \Delta y$) | WGS84 Geodesic Integration (`pyproj.Geod`) | UTM Zone 45N Equal-Area Reprojection | Verified Variance |
| :--- | :---: | :---: | :---: | :---: |
| **Common Analysis Grid** | $1,731.42\text{ km}^2$ | **$1,526.05\text{ km}^2$** | $1,525.92\text{ km}^2$ | $-0.009\%$ |
| **Candidate Flood Inundation** | $143.99\text{ km}^2$ | **$126.60\text{ km}^2$** | $126.58\text{ km}^2$ | $-0.010\%$ |
| **Candidate Surface Debris (Raw)** | $123.07\text{ km}^2$ | **$108.21\text{ km}^2$** | $108.19\text{ km}^2$ | $-0.011\%$ |
| **Exposed Road Length** | $39.88\text{ km}$ | **$35.12\text{ km}$** | $35.10\text{ km}$ | $-0.057\%$ |

*Note on Debris Extents:* The raw change detection produces **$108.21\text{ km}^2$** of unconstrained candidate debris/surface coarsening ($1,230,733$ pixels, $\Delta\sigma^0 \ge +3.5\text{ dB}$). Applying a contiguous cluster Minimum Mapping Unit (MMU) of $\ge 1,000\text{ m}^2$ suppresses steep-mountain single-pixel speckle to yield **$46.93\text{ km}^2$** ($533,819$ pixels). Restricting to major valley deposit fans ($\text{MMU} \ge 2,000\text{ m}^2$) yields **$17.51\text{ km}^2$** ($199,190$ pixels), and vectorization with $\text{MMU} \ge 2,500\text{ m}^2$ yields **$13.40\text{ km}^2$** ($3,086$ polygons).

---

## 6. Exposure vs Destruction Terminology Standards

To prevent false scientific claims and panic during disaster response, VARUNA enforces strict semantic separation in all code, APIs, and reports:

* **OBSERVED_HAZARD:** An anomalous physical change detected in radar backscatter ($\Delta\sigma^0 \le -3.5\text{ dB}$ or $\ge +3.5\text{ dB}$).
* **POTENTIAL_INFRASTRUCTURE_EXPOSURE:** A spatial intersection between a pre-event infrastructure LineString/Polygon and an observed hazard polygon ($35.12\text{ km}$ total roads, $9.62\text{ km}$ Pasang Lhamu Highway). Indicates potential disruption; does *not* prove physical structural collapse.
* **HYPOTHETICAL_ROAD_CLOSURE:** A network simulation assumption that an exposed road link is impassable, used to test network connectivity vulnerabilities.
* **SCENARIO_ISOLATED_SETTLEMENT:** A community that loses all road paths to towns or hospitals *under the hypothetical closure scenario*. Exactly 6 candidate isolated settlements are identified: **Syaphrubesi, Mailung, Betrawati, Ramche, Timure, and Thambuchet** (severed from vehicular route to Nuwakot District Hospital at Bidur).
* **INDEPENDENTLY_VERIFIED_DAMAGE:** Ground truth structural destruction confirmed by on-site civil engineers or high-resolution post-event aerial inspection (e.g. EMSR927 surveyed destroyed buildings). Satellite exposure is never presented as confirmed destruction.
