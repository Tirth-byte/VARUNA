# VARUNA — Phase 1.5 Scientific Integrity Audit & Repair Report

**Date:** 2026-10-11  
**Sprint:** Phase 1.5: Scientific Integrity Repair  
**Target Event:** August 26, 2026 Trishuli Flood, Nepal  
**Core Principle:** *"If we cannot verify it, we do not present it as fact."*

---

## Defect Matrix & Resolution Evidence

| Defect ID | Severity | File | Original Defect | Scientific Repair Implemented | Verification Evidence |
|---|---|---|---|---|---|
| **A.1** | **CRITICAL** | `varuna/preprocessing/sar.py` | `calibrate_to_sigma0_db` assumed uncalibrated DN was linear power when calibration scalar was omitted. | Enforced mandatory calibration verification: requires calibration LUT ($A_{\sigma}$) or scalar. Explicitly raises `MissingCalibrationError`. | `tests/test_sar_preprocessing.py::test_missing_calibration_fails_closed` passed. |
| **A.2** | **CRITICAL** | `varuna/preprocessing/sar.py` | Input units were implicit and unknown units were not validated. | Created `SARUnit` enum (`RAW_DN`, `AMPLITUDE`, `LINEAR_POWER`, `DECIBELS_DB`). Rejects unknown units with `InvalidSARUnitError`. | `tests/test_sar_preprocessing.py::test_invalid_unit_rejected` passed. |
| **A.3** | **CRITICAL** | `varuna/preprocessing/sar.py` | Artificial clipping (`min_db=-35`, `max_db=10`) was concealing legitimate high backscatter and extreme values. | Removed artificial clipping. Backscatter values are unclipped to preserve true physical radar response. | `tests/test_sar_preprocessing.py::test_calibrate_with_scalar_constant` passed. |
| **A.4** | **CRITICAL** | `varuna/preprocessing/sar.py` | Lee speckle filter allowed execution in logarithmic decibels (dB), skewing speckle distribution and biasing mean. | Multiplicative Lee filter strictly enforced in linear intensity domain (`LINEAR_POWER`). Decibel inputs are converted to linear, filtered, and converted back. Added nodata-aware convolution. | `tests/test_sar_preprocessing.py::test_lee_speckle_filter_reduces_variance_in_linear_domain` passed. |
| **B.1** | **HIGH** | `varuna/preprocessing/alignment.py` | Rasters with identical dimensions and CRS were assumed aligned without checking affine origins or resolutions. | Comprehensive `check_spatial_comparability` verifies CRS, all 6 Affine transform coefficients, grid dimensions, and bounding box overlap within numerical tolerance. | `tests/test_sar_preprocessing.py::test_spatial_alignment_and_overlap_rejection` passed. |
| **B.2** | **HIGH** | `varuna/preprocessing/alignment.py` | No standardized grid structure or rejection of non-overlapping scenes. | Implemented `CommonAnalysisGrid` and `NonOverlappingRasterError` for deterministic reprojection and joint valid overlap masking. | `tests/test_sar_preprocessing.py::test_spatial_alignment_and_overlap_rejection` passed. |
| **C.1** | **HIGH** | `varuna/acquisition/cdse.py` | Metadata attributes (relative orbit, orbit direction, polarization, operational mode) had silent defaults. | Strict parsing requiring all mandatory radar attributes. Rejects missing attributes with `ValueError`. | `tests/test_cdse_discovery.py::test_missing_metadata_raises_error` passed. |
| **C.2** | **HIGH** | `varuna/acquisition/cdse.py` | Previous agent used August 2024 instead of the actual August 2026 Trishuli case study corridor. | Re-executed query against live CDSE for August 2026 Trishuli Valley. Discovered authentic pre-event (`2026-08-24T00:18:44Z`) and post-event (`2026-09-05T00:18:44Z`) Orbit 19 pair with 100% AOI coverage. | Documented in `docs/EXPERIMENT_LOG.md`. |
| **D.1** | **CRITICAL** | `varuna/osm/network.py` | Road graph builder only used first and last coordinates of LineStrings, missing interior T-junctions and crossings. | Segmented road LineStrings at real intersection vertices. Split lines at shared coordinates into atomic topological edges. | `tests/test_osm_connectivity.py::test_t_junction_properly_noded` passed. |
| **D.2** | **CRITICAL** | `varuna/osm/network.py` | Used `nx.Graph` which destroyed distinct parallel roads between identical junctions. | Migrated network to `nx.MultiGraph`, preserving parallel road segments. | `tests/test_osm_connectivity.py::test_parallel_roads_preserved` passed. |
| **D.3** | **CRITICAL** | `varuna/osm/network.py` | Elevated bridges crossed underpass roads at identical nodes without checking elevation layers. | Added layer-aware noding. Overpass bridges at `layer=1` do not connect to surface highways at `layer=0`. | `tests/test_osm_connectivity.py::test_overpass_bridge_does_not_falsely_connect_underpass` passed. |
| **D.4** | **CRITICAL** | `varuna/osm/network.py` | Settlements were snapped to the nearest road regardless of distance. | Implemented `max_snap_distance_meters` constraint (default 1000m). Tracks `unattached_settlements` instead of false connections. | `tests/test_osm_connectivity.py::test_unattached_distant_settlement_recorded` passed. |
| **E.1** | **HIGH** | `varuna/osm/network.py`, `varuna/detection/baseline.py` | Used planar degree approximation `geom.length * 111320.0` which causes ~15% measurement errors at Nepal latitudes. | Integrated `pyproj.Geod(ellps="WGS84")` for exact geodesic ellipsoidal distance and area computations. | `tests/test_osm_connectivity.py::test_geodesic_distance_precision` passed. |
| **F.1** | **CRITICAL** | `varuna/osm/network.py` | Remote sensing hazard exposure was conflated with confirmed road destruction. | Implemented distinct `InfrastructureState` categories: `OBSERVED_HAZARD`, `POTENTIAL_INFRASTRUCTURE_EXPOSURE`, `HYPOTHETICAL_ROAD_CLOSURE`, `SCENARIO_ISOLATED_SETTLEMENT`, and `INDEPENDENT_VERIFIED_DAMAGE`. Added mandatory disclaimers. | Verified in API and network responses. |
| **G.1** | **HIGH** | `varuna/detection/baseline.py` | Threshold-distance scores were presented without explicitly labeling them as heuristic. | Explicitly labeled as `HEURISTIC_MARGIN_INDEX` (uncalibrated distance to threshold). Nodata pixels preserved as `NaN`. | `varuna/detection/baseline.py` verified. |
| **H.1** | **NEW** | `varuna/jobs/pipeline.py` | Missing end-to-end job orchestration workflow. | Built traceable job pipeline (`AnalysisJob`, `JobPipelineManager`) with state persistence and provenance logging. | `tests/test_api.py::test_jobs_endpoint_creation_and_status` passed. |
| **I.1** | **NEW** | `varuna/osm/fetcher.py` | Missing historical OpenStreetMap retrieval engine. | Built `HistoricalOSMFetcher` querying Overpass API with `[date:"..."]` point-in-time constraints. | `varuna/osm/fetcher.py` verified. |
| **J.1** | **NEW** | `varuna/validation/benchmark.py` | Missing independent validation engine for EMSR927 comparison. | Built `IndependentValidationBenchmark` computing IoU, Precision, Recall, F1, confusion matrix, and spatial agreement maps. | `tests/test_validation_benchmark.py` passed (3/3 tests). |

---

## Automated Test Suite Summary

- Total Automated Tests: **39 passing** (0 failures, 0 errors)
- Test Runtime: **0.56 seconds**
- Test Coverage:
  - Unit Tests: Calibration, units, unclipped dB, speckle filter, geodesic metrics, topology, layers, overlap.
  - Integration Tests: FastAPI endpoints, jobs pipeline, validation benchmark, CDSE live and mock discovery.
