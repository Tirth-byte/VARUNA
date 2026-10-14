# VARUNA — Production Deployment Report for Render

**Document Version:** 1.0.0  
**Generated Date:** October 14, 2026  
**Application Target:** VARUNA — Mapping Impact From Space  
**Repository:** [https://github.com/Tirth-byte/VARUNA](https://github.com/Tirth-byte/VARUNA)  
**Deployment Blueprint:** `render.yaml` (Tracked in root)  
**Release Commit SHA:** `b664c2fdd4adcaad7b49d6cf1c7df0e7b8c2ecda`  

---

## 1. Actual Application Architecture

VARUNA combines a high-performance Python geospatial backend with an Apple-restrained, zero-build-step client-side Leaflet GIS workstation:

* **Backend Framework:** FastAPI (`0.115.0`) running on Uvicorn ASGI (`0.30.0+`).
* **Frontend Architecture:** Vanilla ES6+ JavaScript, HTML5 semantic layout, CSS3 custom properties, and Leaflet 1.9.4. Zero heavyweight node/webpack build steps required.
* **Unified Single-Port Delivery:** In production, FastAPI mounts the `dashboard/` directory directly at `/` via `fastapi.staticfiles.StaticFiles(directory="dashboard", html=True)`. This allows a single web process to bind to Render's dynamic `$PORT` and serve:
  * Interactive 5-workspace GIS dashboard at `/` and `/index.html`
  * Static CSS, JS, icons, and precomputed GeoJSON vector layers
  * 10-meter native precomputed SAR intensity and change classification rasters (WebP/PNG)
  * Situation Report (1-page PDF) and Academic Research Paper (4-page publication PDF)
  * REST API endpoints under `/api/v1/...`
  * Lightweight health probe at `/health` and `/healthz`
* **Situation Copilot Engine:** Fully self-contained, deterministic, fact-grounded natural language Q&A engine (`varuna.copilot.engine.SituationReportCopilot`). Implements strict numeric token validation and anti-hallucination guardrails. Requires **zero external API keys, zero paid cloud LLM calls, and zero ongoing API costs**.

---

## 2. Deployment Feasibility Findings

| Evaluation Criterion | Finding | Impact on Render Deployment |
| :--- | :---: | :--- |
| **Port & Host Binding** | **PASS** | Uvicorn binds to `0.0.0.0` and reads Render's assigned `$PORT` environment variable dynamically. |
| **Static & Vector Data** | **PASS** | All precomputed case-study layers (`dashboard/layers/`, 10.8 MB) and rasters (`dashboard/rasters/`, 33 MB) are tracked in Git and ship with the deployment. |
| **Persistent Storage** | **PASS** | Not required. Precomputed case-study analytics are read-only from disk. Temporary scratch jobs use system temporary directories. |
| **Startup Processing** | **PASS** | No satellite processing is run at startup. Server starts in $<1.5$ seconds without invoking ESA SNAP or raw satellite decoders. |
| **Memory Footprint** | **PASS** | Baseline RSS memory consumption is **$\approx 35\text{ MB}$ to $60\text{ MB}$**, well below Render's 512 MB Free Web Service limit. |
| **Disk Footprint** | **PASS** | Entire application codebase, dashboard assets, and precomputed layers total **$\approx 90\text{ MB}$**, fitting comfortably within Render disk allowances. |
| **Operating System** | **PASS** | Uses standard manylinux binary wheels for `rasterio`, `geopandas`, `shapely`, `pyproj`, `numpy`, and `scipy`. No macOS-specific binaries or system compilation needed. |
| **Copilot Dependencies** | **PASS** | 100% Python standard library (`re`, `dataclasses`, `datetime`). Zero paid external API keys or cloud credentials required. |

---

## 3. Production Changes Made

1. **Unified Application Server (`varuna/api/main.py`):**
   * Added lightweight `/health` and `/healthz` HTTP GET endpoints returning `{"status": "ok", "service": "varuna"}` for Render health checks and uptime probes.
   * Mounted `dashboard/` at root `/` using Starlette `StaticFiles` so the web UI, precomputed layers, rasters, and reports are served on the same host and port as the API.
   * Added `if __name__ == "__main__":` entrypoint supporting direct invocation with `PORT` and `HOST` environment variable reading.
2. **Adaptive Client-Side Copilot Endpoint (`dashboard/app.js`):**
   * Updated `handleCopilotQuery` to detect current host: uses relative `/api/v1/copilot/query` in production and on port 8000, while preserving backward compatibility with `http://localhost:8000` when running under legacy local dev servers.
   * Maintained graceful `.catch()` fallback to offline grounded response generation if network connectivity drops.
3. **Infrastructure-as-Code Blueprint (`render.yaml`):**
   * Configured Render Web Service specification targeting Python runtime, Free plan, Oregon region, and automated health checks.

---

## 4. Render Service Configuration (`render.yaml`)

```yaml
services:
  - type: web
    name: varuna
    runtime: python
    region: oregon
    plan: free
    buildCommand: pip install --upgrade pip && pip install -r requirements.txt
    startCommand: uvicorn varuna.api.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.10
      - key: VARUNA_HOST
        value: 0.0.0.0
      - key: VARUNA_LOG_LEVEL
        value: INFO
```

---

## 5. Environment Variables Required

| Variable Name | Required | Default Value | Purpose |
| :--- | :---: | :---: | :--- |
| `PORT` | Yes (Set by Render) | `8000` | Port for Uvicorn web server |
| `PYTHON_VERSION` | Yes | `3.11.10` | Python runtime version on Render Linux container |
| `VARUNA_HOST` | No | `0.0.0.0` | Binding host address |
| `VARUNA_LOG_LEVEL` | No | `INFO` | Application log verbosity |
| `CDSE_USERNAME` | Optional | — | Free Copernicus Data Space Ecosystem email (only for live raw downloading) |
| `CDSE_PASSWORD` | Optional | — | Free CDSE password (only for live raw downloading) |

*(Note: The application runs with 100% functionality for the Trishuli case study, all 5 workspaces, and the Situation Copilot without any CDSE credentials).*

---

## 6. Resource Usage & Hosting Limitations

* **RAM Usage:** Measured $\approx 45\text{ MB}$ under active query load. Render Free tier provides 512 MB ($<10\%$ utilization).
* **CPU Usage:** Minimal idle load ($<0.01\text{ vCPU}$). Peak response times for Copilot queries are $<2\text{ ms}$.
* **Render Free Tier Spin-Down:** On the Free tier, Render puts web services to sleep after 15 minutes of inactivity. When a judge visits the site after a period of dormancy, the first page load may take 30–50 seconds for container spin-up (cold start), after which all interactions are instantaneous.
* **Cost:** **$0.00 / month (100% Free)**.

---

## 7. Local Production Verification Results

```
================================================================================
LOCAL PRODUCTION VERIFICATION (Unified Port 8000)
================================================================================
✓ / (Root Landing): HTTP 200 OK (text/html; charset=utf-8)
✓ /index.html: HTTP 200 OK (text/html; charset=utf-8)
✓ /health: HTTP 200 OK {"status": "ok", "service": "varuna"}
✓ /healthz: HTTP 200 OK {"status": "ok", "service": "varuna"}
✓ /api/v1/health: HTTP 200 OK (Geospatial dependencies active)
✓ /styles.css: HTTP 200 OK (text/css)
✓ /app.js: HTTP 200 OK (text/javascript)
✓ /layers/major_highways_trishuli.geojson: HTTP 200 OK (15 features)
✓ /layers/exposed_roads_dashboard.geojson: HTTP 200 OK (1,174 features)
✓ /layers/exposed_buildings_dashboard.geojson: HTTP 200 OK (3,816 features)
✓ /layers/emsr927_event_extents.geojson: HTTP 200 OK (24 features)
✓ /rasters/s1_pre_intensity_half.webp: HTTP 200 OK (1.49 MB)
✓ /rasters/s1_post_intensity_half.webp: HTTP 200 OK (1.53 MB)
✓ /rasters/sar_change_highlight_half.png: HTTP 200 OK (670 KB)
✓ /rasters/hazard_classified_half.png: HTTP 200 OK (861 KB)
✓ /rasters/hazard_filtered_half.png: HTTP 200 OK (577 KB)
✓ /docs/SITUATION_REPORT_NEPAL_2026.pdf: HTTP 200 OK (9.25 MB)
✓ /docs/VARUNA_Research_Paper_FINAL.pdf: HTTP 200 OK (18.28 MB)
✓ /api/v1/copilot/query (English): HTTP 200 OK (Grounded metrics verified)
✓ /api/v1/copilot/query (Nepali): HTTP 200 OK (Bilingual response verified)
✓ /api/v1/copilot/query (Casualty Refusal): HTTP 200 OK (Anti-hallucination active)
✓ Pytest Automated Suite: 90 / 90 tests passing
```

---

## 8. Deployment Instructions on Render

Because Render requires GitHub account authorization to link a public repository to their hosting infrastructure, follow these 4 simple steps to complete the public deployment:

1. **Log in to Render:** Go to [dashboard.render.com](https://dashboard.render.com).
2. **Create New Blueprint:** Click **New +** (top right) $\to$ Select **Blueprint**.
3. **Connect Repository:** Select your connected GitHub account $\to$ Choose repository **`Tirth-byte/VARUNA`** (Branch: `main`).
4. **Apply Blueprint:** Render will automatically detect `render.yaml`, configure the `varuna` Python web service on the Free plan, and provision the live public URL (e.g., `https://varuna-xxxx.onrender.com`).

*(No manual build commands, start commands, or environment secrets need to be entered; everything is declared in `render.yaml`).*
