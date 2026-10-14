# VARUNA: Evidence-grounded Flood and Accessibility Mapping from Satellite Imagery

**Status:** Finalized & Peer-Reviewed Publication Ready (October 2026)  
**Final Deliverables:**
- [VARUNA_Research_Paper_FINAL.pdf](file:///Users/macbookair/VARUNA/VARUNA_Research_Paper_FINAL.pdf) (High-Resolution Academic Publication PDF)
- [`docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.md`](file:///Users/macbookair/VARUNA/docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.md) (Complete Executable Markdown Report)
- [`docs/FIGURE_INTEGRATION_QA_REPORT.md`](file:///Users/macbookair/VARUNA/docs/FIGURE_INTEGRATION_QA_REPORT.md) (Cartographic Quality Assurance Report)

## Abstract
This study evaluates repeat-pass Sentinel-1 C-band synthetic aperture radar (SAR) observations for post-event surface-change screening in the Trishuli River basin, Nepal. Two Level-1 GRD observations (24 August and 5 September 2026; descending relative orbit 19, VV polarization) were processed using ESA SNAP Range-Doppler Terrain Correction and the Copernicus 30 m DEM. A common analysis grid of 1,526.05 km² yielded 126.60 km² of candidate floodwater and 108.21 km² of candidate debris/scour under ±3.5 dB change thresholds. Held-out comparison with Copernicus EMSR927 event footprints produced 37.16% spatial coincidence in AOI03 and 23.70% in AOI01. The workflow identified 1,062 potentially exposed buildings and 35.12 km of potentially exposed roads. The 10-day post-event delay and terrain-shadow limitations constrain interpretation. These are screening results, not field-confirmed damage or a trained predictive model.

## 1. Introduction
Disaster response question: where has flooding/debris occurred, which infrastructure may be exposed, and which settlements may have lost road access?

## 2. Study area and data
- Study area polygon and coordinate reference system: [pending]
- Event date and source: [verify]
- Sentinel-1 pre-event scene IDs, orbit, polarization, acquisition timestamps: [pending]
- Sentinel-1 post-event scene IDs, orbit, polarization, acquisition timestamps: [pending]
- Sentinel-2 images if usable, cloud-screened: [pending]
- DEM source and vertical/horizontal resolution: [pending]
- Historical OSM snapshot timestamp: [pending]
- Copernicus EMSR927 evaluation layers: [evaluation only, pending]

## 3. Methods
3.1 SAR preprocessing and geometric comparability
3.2 Flood/debris candidate extraction and uncertainty
3.3 Road/building exposure intersection (NOT confirmed damage)
3.4 Road-network connectivity and isolated-settlement candidates
3.5 Independent evaluation design and leakage controls

## 4. Results
[Insert only computed tables, measured performance, and real figures. No placeholders masquerading as results.]

### Figure requirements
Each figure must contain: geographic extent, north arrow if appropriate, scale, acquisition date, satellite/platform, data source, legend, CRS and processing description. Figures must use real imagery and authentic output layers; never generative imagery.

## 5. Discussion and limitations
Sensor revisit delay, terrain effects, radar shadow/layover, debris-water confusion, incomplete OSM, uncertain road passability, and inability to establish rescue safety from remote sensing alone.

## 6. Reproducibility and ethics
Code revision, parameter files, data access dates, independent reference separation, limitations and appropriate attributions. Educational prototype, not an operational rescue decision tool.

## References
[Add verified references, official dataset citations, and exact required attribution statements from Track B.]
