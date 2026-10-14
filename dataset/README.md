# VARUNA — Master Dataset Catalog & Data Directory

This directory aggregates all input, reference, and derived Earth observation datasets utilized across the **VARUNA Satellite-Powered Flood Intelligence System** for the August 26, 2026 Trishuli River GLOF and Flash Flood case study in Central Nepal.

---

## Directory Architecture

```
dataset/
├── sentinel1_sar_rasters/              # Authentic Sentinel-1 C-SAR level-1 GRD calibrated & aligned rasters
│   ├── trishuli_pre_20260824.tif       # Pre-event primary scene (Orbit 19 Descending, 2026-08-24)
│   ├── trishuli_post_20260905.tif      # Post-event primary scene (Orbit 19 Descending, 2026-09-05)
│   ├── pre_calibrated.tif              # Radiometrically calibrated decibel backscatter (pre-event)
│   ├── post_calibrated.tif             # Radiometrically calibrated decibel backscatter (post-event)
│   ├── aligned_pre.tif                 # Common Analysis Grid (CAG) resampled pre-event raster
│   └── aligned_post.tif                # Common Analysis Grid (CAG) resampled post-event raster
│
├── reference_emsr927_ground_truth/     # Copernicus Emergency Management Service EMSR927 Held-Out Truth
│   ├── AOI01/                          # Syapru Besi Gorge: Observed events, roads, buildings, facilities
│   ├── AOI02/                          # Dhunche: Built-up, transportation, observed event polygons
│   ├── AOI03/                          # Bidur / Trishuli Confluence: Validation AOI vectors & products
│   ├── AOI05/                          # Mailung / Lower Gorge: Transportation, not analysed, observed event
│   ├── AOI01_vectors.zip               # Complete vector shapefile package (AOI01)
│   ├── AOI02_vectors.zip               # Complete vector shapefile package (AOI02)
│   ├── AOI03_vectors.zip               # Complete vector shapefile package (AOI03)
│   ├── AOI05_vectors.zip               # Complete vector shapefile package (AOI05)
│   └── emsr927_event_extents.geojson   # Unified GeoJSON polygon extents for held-out cross-validation
│
├── infrastructure_osm_roads/           # Transportation & Infrastructure Baselines
│   ├── major_roads/                    # Pre-event road network shapefiles & GeoJSON (HOT-OSM Snapshot)
│   ├── npl_majrdsl_gist.zip            # National major road network GIS shapefile archive
│   ├── major_highways_trishuli.geojson # Pasang Lhamu National Highway (H04) study corridor centerline
│   └── exposed_roads_dashboard.geojson # Dissolved unique road segments intersecting flood / debris hazards
│
├── hazard_classification_products/     # Computed Change Detection & Exposure Products
│   ├── flood_change_classification.tif # 3-band GeoTIFF (Band 1: Δσ°, Band 2: Class, Band 3: Mask)
│   ├── candidate_hazard_polygons.geojson # Full raw polygon archive (466 MB, 782,612 features)
│   ├── valid_data_mask.tif             # Joint valid spatial overlap mask (100% valid, 0 NoData)
│   ├── independent_validation_emsr927.json # Machine-readable accuracy & spatial coincidence metrics
│   ├── infrastructure_exposure_analysis.json # Evidence-grounded road & building exposure statistics
│   ├── provenance.json                 # Processing lineage, SNAP version, IPF lookup tables, and parameters
│   ├── candidate_water_dashboard.geojson # Filtered floodwater inundation polygons (Δσ° ≤ -3.5 dB)
│   ├── candidate_debris_dashboard.geojson # Filtered surface debris coarsening polygons (Δσ° ≥ +3.5 dB)
│   └── exposed_buildings_dashboard.geojson # Surveyed buildings with potential hazard exposure
│
└── web_map_rasters/                    # Optimized Multi-Layer WebGL / Leaflet Map Tiles
    ├── raster_metadata.json            # Georeferenced bounding box coordinates & display bounds
    ├── s1_pre_intensity.webp           # Pre-event Sentinel-1 decibel grayscale imagery
    ├── s1_post_intensity.webp          # Post-event Sentinel-1 decibel grayscale imagery
    ├── s1_diff_continuous_half.webp    # Continuous backscatter change gradient map (Δσ°)
    ├── hazard_classified_half.webp     # Multi-class hazard overlay (Water = Blue, Debris = Orange)
    ├── hazard_water_half.png           # Transparent floodwater overlay
    ├── hazard_debris_half.png          # Transparent debris flow overlay
    └── hazard_filtered_half.png        # Filtered hazard clusters overlay (MMU ≥ 2,000 m²)
```

---

## Dataset Summary & Specifications

| Dataset Category | Source Agency | Primary Files / Formats | Spatial Resolution | CRS | Role in VARUNA |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Sentinel-1 SAR Level-1 GRD** | European Space Agency (ESA) Copernicus Data Space Ecosystem | GeoTIFF (Float32 decibel $\sigma^0$) | 10 m native | EPSG:4326 | Primary bitemporal backscatter differencing |
| **Copernicus EMSR927 Reference Truth** | Copernicus Emergency Management Service (EMS) Rapid Mapping | ESRI Shapefile, GeoJSON | Metric survey | EPSG:32645 / EPSG:4326 | **Strictly held-out independent validation** (Leakage Guard protected) |
| **OpenStreetMap Infrastructure** | Humanitarian OpenStreetMap Team (HOT) & Survey Dept Nepal | Shapefile, GeoJSON | Vector lines & points | EPSG:4326 | Exposure analysis, hospital reachability, and network graph topology |
| **Classified Hazard Models** | VARUNA Baseline Change Detection Engine | 3-band GeoTIFF, GeoJSON, FlatGeobuf | 10 m (3,897 × 4,454) | EPSG:4326 | Candidate flood inundation ($126.60\text{ km}^2$) and debris ($108.21\text{ km}^2$) |
| **Web Tile Stack** | VARUNA GeoConverter / PIL | WebP / PNG with Alpha transparency | Scaled 50% | EPSG:4326 | Interactive swipe comparison & dashboard layer toggling |

---

## Strict Scientific Integrity & Non-Leakage Rule

As enforced by `varuna/validation/leakage_guard.py`:
1. Datasets in `reference_emsr927_ground_truth/` are assigned `DatasetRole.INDEPENDENT_VALIDATION`.
2. They are never ingested into the feature extraction, threshold calibration, or baseline change detection modules.
3. Passing reference validation layers as `PREDICTION_INPUT` raises an immediate `DataLeakageError` exception.
