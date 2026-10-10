# VARUNA — Satellite-Powered Flood Intelligence System

**Track B: Mapping Flood Damage from Space — Multimodal AI Hackathon 2026**  
*Educational research prototype for the August 26, 2026 Trishuli flood case study and general judge-selected areas/dates.*

---

## 1. Scientific Principles & Non-Negotiable Rules

- **Authentic Satellite Observations:** Uses genuine Sentinel-1 SAR and Sentinel-2 optical imagery with complete scene IDs, acquisition timestamps, relative orbit, and processing provenance.
- **Strict Temporal Guard:** OpenStreetMap infrastructure snapshots are dated strictly **before** the event date; post-event edits are barred from inference.
- **Held-Out Reference Validation:** Copernicus Emergency Management Service (EMS EMSR927) and UNOSAT damage maps are strictly reserved for independent validation; never ingested as model features.
- **Radar Geometric Compatibility:** Before/after Sentinel-1 comparisons are only permitted when relative orbit, pass direction, and polarization match.
- **Scientific Humility:** Potential radar surface changes are not equated with confirmed inundation, and exposed roads are explicitly differentiated from confirmed destroyed infrastructure.
- **Zero Fabrication:** No synthetic satellite imagery, fabricated performance metrics, or hallucinated settlement counts.

---

## 2. Architecture & Modules

```
VARUNA/
├── varuna/
│   ├── contracts.py                # Core data contracts & orbit/OSM guards
│   ├── acquisition/
│   │   ├── cdse.py                 # Live Copernicus Data Space OData discovery
│   │   └── download.py             # Keycloak OAuth2 auth & streaming download
│   ├── preprocessing/
│   │   ├── sar.py                  # Radiometric calibration (DN->dB) & Lee filter
│   │   └── alignment.py            # CRS verification, raster reprojection & bounds check
│   ├── detection/
│   │   └── baseline.py             # Log-ratio SAR change, Otsu threshold, flood/debris differentiation
│   ├── osm/
│   │   └── network.py              # Road graph connectivity & settlement isolation analysis
│   ├── validation/
│   │   └── leakage_guard.py        # Strict role separation guarding against data leakage
│   └── api/
│       ├── main.py                 # FastAPI application
│       └── schemas.py              # Pydantic request/response schemas
├── tests/                          # Automated unit & integration tests (28 tests)
├── docs/
│   └── IMPLEMENTATION_STATUS.md    # Verified capabilities, status, and roadmap
├── RESEARCH_REPORT_TEMPLATE.md     # 6-page paper template
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Packaging & pytest configuration
└── .env.example                    # Environment variable template
```

---

## 3. Setup & Execution Instructions

### A. Environment Setup
```bash
# Create and activate Python 3.11+ virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### B. Configuration
Copy the environment template:
```bash
cp .env.example .env
```
To enable raw satellite file downloading from Copernicus, add your free credentials from [dataspace.copernicus.eu](https://dataspace.copernicus.eu) (`CDSE_USERNAME` and `CDSE_PASSWORD`). Catalogue scene discovery is functional without credentials.

### C. Running Automated Tests
```bash
pytest -v
```
All 28 tests cover orbit validation, CDSE catalogue querying, Lee speckle filtering, radiometric calibration, baseline change detection, road graph isolation, and FastAPI endpoints.

### D. Running the FastAPI Server
```bash
uvicorn varuna.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation will be available at `http://localhost:8000/docs`.

---

## 4. API Endpoints

- `GET /api/v1/health`: System health, library versions, and external API readiness.
- `POST /api/v1/scenes/discover`: Sentinel-1 scene discovery and geometric pairing from CDSE.
- `POST /api/v1/detection/baseline`: Multi-class radar change detection (water drop vs. debris roughening).
- `POST /api/v1/analysis/exposure`: Intersect detected flood polygons with pre-event OSM road graph and detect potentially isolated settlements.

---

## 5. Attributions & Data Licenses

- **Copernicus Sentinel Data:** European Space Agency (ESA) / Copernicus Open Access Policy.
- **OpenStreetMap:** © OpenStreetMap contributors, ODbL license.
- **Copernicus EMS:** European Union Emergency Management Service (Activation EMSR927, validation only).
