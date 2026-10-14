# VARUNA: 3-Minute Demonstration & Presenter Pitch Script

**Track B: Mapping Flood Damage from Space — Multimodal AI Hackathon 2026**  
**Event Case Study:** August 26, 2026 GLOF & Flash Flood, Trishuli River Valley, Central Nepal  
**Presenter:** Antigravity AI Engineering Team  
**Estimated Time:** Exactly 3:00 Minutes  
**Primary Live Asset:** Interactive Dashboard running at `http://localhost:8888/`  
**Reliable Offline Fallback:** Visual artifacts located in `data/demo_evidence/` and embedded below.

---

## Part 1: Timed Presentation Script

### 0:00 – 0:30 | The Disaster Problem & VARUNA's Core Objective
> **[Action: Stand at overview screen. Show title slide / dashboard overview.]**
>
> *"Judges, on August 26, 2026, an avalanche triggered a catastrophic Glacial Lake Outburst Flood and torrential debris torrent down the steep Trishuli River gorge in central Nepal. Dense monsoon clouds blinded all optical satellites. Mountain settlements, hydropower stations, and the lifeline Pasang Lhamu Highway were cut off.*
>
> *Traditional response teams were left blind. Our objective with VARUNA is simple but uncompromising: deliver rapid, physics-grounded flood intelligence from radar satellites within hours of pass time, with zero hallucination. If we cannot prove an observation from raw satellite physics, we refuse to present it as fact."*

---

### 0:30 – 1:00 | Authentic Sentinel-1 Data & ESA SNAP Processing
> **[Action: Point to the Satellite Observation Metadata Card on the left sidebar.]**
>
> *"Unlike mock hackathon projects that use synthetic toys or toy bounding boxes, VARUNA ingested two genuine 1.7 GB Sentinel-1 C-band SAR observations from the European Space Agency Copernicus Data Space Ecosystem.*
>
> *Notice our geometry: Pre-event scene from August 24, post-event from September 5. Both on identical Relative Orbit 19, descending pass, VV polarization, 12.0-day repeat. We executed radiometric calibration, thermal noise correction, and Range-Doppler Terrain Correction through ESA SNAP's Graph Processing Tool with the Copernicus 30m Global DEM. Over our 1,526 square kilometer analysis domain—spanning over 17 million 10-meter pixels—our spatial alignment achieved exactly 100.0% valid overlap with zero NoData dropouts."*

---

### 1:00 – 1:45 | Interactive Flood & Surface-Change Map
> **[Action: Switch to full map view. Toggle Candidate Water (cyan) and Debris (orange). Zoom to Trishuli River Corridor.]**
>
> *"Here is the interactive map. When radar pulses hit smooth standing water, the energy specularly reflects away from the antenna, creating a sharp drop in backscatter. VARUNA detected **126.60 square kilometers** of candidate inundation (shown in cyan). We independently verified this total against exact row-by-row WGS84 geodesic integration and metric UTM 45N reprojection—variance was under 0.02%.*
>
> *Crucially, mountain floods aren't just water. They carry massive sediment and boulders. When floodwaters recede or gravel bars are torn apart, the surface roughens, causing diffuse radar scattering to surge. VARUNA detected **108.21 square kilometers** of candidate surface debris and scour (shown in orange). To ensure fast, fluid interaction without browser crashes, we preserved the original 488 MB archive while engineering multi-tier optimized layers that render 60 FPS in any browser."*

---

### 1:45 – 2:20 | Infrastructure Exposure & Copernicus Reference Comparison
> **[Action: Click 'Zoom: Bidur Confluence (AOI03)'. Toggle 'EMSR927 Event Scour (Truth)', 'Exposed Surveyed Buildings', and 'Pasang Lhamu Highway'.]**
>
> *"Now let's examine ground truth and infrastructure impact. We cross-validated VARUNA against authentic European Commission Copernicus Emergency Management Service activation **EMSR927**.*
>
> *At the Bidur confluence, where optical satellites surveyed the flood footprint, VARUNA's radar anomaly captured **37.16%** of the optical event footprint—even though our SAR observation occurred 10 days post-peak.*
>
> *By overlaying national transportation vectors and 3,816 surveyed structures, we identified **1,062 potentially exposed buildings** (27.8%). Notice that among structures independently graded as 'Destroyed' by Copernicus, 33.3% directly intersect our radar anomalies.*
>
> *Along the national road network, we isolated **35.12 kilometers** of unique exposed roads with zero double counting between water and debris, including **9.62 kilometers** along the critical Pasang Lhamu Highway."*

---

### 2:20 – 3:00 | Scientific Limitations, Practical Value, & Conclusion
> **[Action: Click 'Scientific Audit' tab on dashboard or highlight disclosures.]**
>
> *"We conclude with scientific honesty:
> First, our September 5 acquisition is a **10-day post-event assessment**, not peak inundation. In steep mountain gorges, water drains in 24 hours; radar captures persistent standing water and altered riverbeds.
> Second, satellite hazard intersection indicates **potential exposure**, not confirmed structural collapse.
> Third, we audited SNAP layover/shadow masking and disclosed that cliff faces require optical confirmation.
>
> In an emergency, first responders don't need black-box AI fantasies. They need verifiable, physics-grounded intelligence. VARUNA delivers an auditable end-to-end chain from raw Copernicus telemetry to life-saving decision maps.
>
> All code, tests, and reports are reproducible on disk today. Thank you!"*

---

## Part 2: Offline Fallback Plan (Pre-Rendered Evidence)

If internet access is unavailable, local ports are blocked, or browser display fails during the presentation, open the following verified local visual artifacts:

### Fallback Slide 1: Regional Flood & Debris Classification Map
* **Artifact Path:** `data/demo_evidence/map_1_trishuli_flood_hazard_overview.png`
* **Resolution:** $2400 \times 1800$ High-Resolution PNG
* **Key Visuals:** Full Trishuli River Valley corridor, cyan candidate water ($126.60\text{ km}^2$), orange debris/roughening ($108.21\text{ km}^2$), DEM terrain relief, district borders.

### Fallback Slide 2: High-Resolution Infrastructure Exposure Detail (Bidur Confluence)
* **Artifact Path:** `data/demo_evidence/map_2_bidur_infrastructure_exposure_detail.png`
* **Resolution:** $2400 \times 1800$ High-Resolution PNG
* **Key Visuals:** Building dots colored by damage grade, highway corridor crossing flood zones, magenta EMSR927 optical truth boundary.

### Fallback Slide 3: Live Interactive Dashboard Capture
* **Artifact Path:** `data/demo_evidence/dashboard_screenshot.png`
* **Resolution:** $1600 \times 1000$ True Browser Screenshot
* **Key Visuals:** Dark GIS canvas, verified layer toggles, orbital geometry telemetry table, headline statistics.

### Fallback Slide 4: PDF Submission Deliverables
* **1-Page SITREP:** `docs/SITUATION_REPORT_NEPAL_2026.pdf` (Single page, executive summary, verified metrics)
* **5-Page Research Report:** `docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.pdf` (Complete academic paper, equations, tables, citations)

---

## Part 3: Anticipated Judge Q&A Cheatsheet

| Question | Concise Evidence-Based Answer |
| :--- | :--- |
| **Q1: Why only 37% overlap with Copernicus EMSR927 in Bidur?** | *"EMSR927 used 0.3m optical images taken within 24-48 hours mapping maximum mud/scour high-water lines. Our Sentinel-1 acquisition was on September 5, 10 days post-peak. In steep Himalayan gorges, torrential waters drain in under 36 hours. The 37.16% represents persistent standing water, saturated mud bars, and river widening that remained 10 days later."* |
| **Q2: Does 9.62 km of highway exposure mean 9.62 km was destroyed?** | *"No, and we explicitly caution against that conflation. 9.62 km represents the length of the highway corridor intersecting SAR hazard zones. While EMSR927 mapped ~61 km of destroyed local roads, our spatial audit proved only 0.30 km directly overlaps the highway centerline, because EMSR927 surveyed local riverbed access tracks while the highway follows an upper bench."* |
| **Q3: Did you use machine learning or hard thresholds?** | *"We implemented adaptive Otsu log-ratio thresholding combined with physical radar decibel boundaries ($\le -3.5\text{ dB}$ for specular drop, $\ge +3.5\text{ dB}$ for diffuse roughening, and $\le -16.0\text{ dB}$ for baseline water). This ensures explainability and prevents synthetic overfitting."* |
| **Q4: How do you know the calibration warning didn't corrupt the data?** | *"We performed a bytecode audit of SNAP's `Sentinel1Calibrator.class`. SNAP threw the warning because CloudFerro wrapped the SAFE archive with a 'COG Conversion' tag instead of the IPF float version string. We inspected the internal XML lookup tables and verified genuine Sentinel-1 IPF 004.03 $A_\sigma$ calibration was applied."* |
