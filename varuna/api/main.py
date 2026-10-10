"""VARUNA FastAPI Engine.

REST API endpoints for Sentinel-1 scene discovery, radar baseline change detection,
and OpenStreetMap road accessibility and isolation analysis.
"""

from __future__ import annotations
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

import numpy as np
import geopandas as gpd
from shapely.geometry import shape, Polygon
from rasterio.transform import from_bounds
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import rasterio
import shapely
import pyproj
import networkx
import scipy

from varuna.acquisition.cdse import (
    CDSEDiscoveryService,
    IncompatibleScenePairError,
    CDSEDiscoveryError,
)
from varuna.acquisition.download import CDSEDownloader
from varuna.detection.baseline import (
    BaselineDetectionConfig,
    run_baseline_detection,
)
from varuna.osm.network import (
    RoadNetworkConnectivityAnalyzer,
)
from varuna.api.schemas import (
    SceneDiscoveryRequest,
    SceneDiscoveryResponse,
    DiscoveredSceneInfo,
    BaselineDetectionRequest,
    BaselineDetectionResponse,
    RoadExposureRequest,
    RoadExposureResponse,
    HealthResponse,
)

app = FastAPI(
    title="VARUNA Flood Intelligence Engine",
    description="Satellite-powered flood intelligence API for Track B: Mapping Flood Damage from Space.",
    version="0.1.0",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return system health, library versions, and external API readiness."""
    downloader = CDSEDownloader()
    return HealthResponse(
        status="healthy",
        system="VARUNA Geospatial Processing Engine",
        version="0.1.0",
        library_versions={
            "python": sys.version.split()[0],
            "rasterio": rasterio.__version__,
            "geopandas": gpd.__version__,
            "shapely": shapely.__version__,
            "pyproj": pyproj.__version__,
            "networkx": networkx.__version__,
            "scipy": scipy.__version__,
            "numpy": np.__version__,
        },
        cdse_credentials_configured=downloader.has_credentials(),
        scientific_integrity_mode="ACTIVE (No fake data; reference validation strictly held out)",
    )


@app.post("/api/v1/scenes/discover", response_model=SceneDiscoveryResponse)
def discover_scenes(req: SceneDiscoveryRequest) -> SceneDiscoveryResponse:
    """Discover compatible Sentinel-1 scene pairs from CDSE bracketing the event date."""
    try:
        aoi_poly = shape(req.aoi.model_dump())
        if not aoi_poly.is_valid:
            aoi_poly = aoi_poly.buffer(0)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid AOI GeoJSON geometry: {e}"
        )

    service = CDSEDiscoveryService()
    try:
        rec = service.discover_compatible_pair(
            aoi_geom=aoi_poly,
            event_date=req.event_date,
            pre_event_window_days=req.pre_window_days,
            post_event_window_days=req.post_window_days,
            min_aoi_coverage=req.min_aoi_coverage,
        )
    except IncompatibleScenePairError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Radar geometry compatibility failure: {str(e)}"
        )
    except CDSEDiscoveryError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Copernicus catalogue communication error: {str(e)}"
        )

    before_info = DiscoveredSceneInfo(
        scene_id=rec.before_scene.scene_id,
        acquired_at=rec.before_scene.acquired_at,
        relative_orbit=rec.before_scene.relative_orbit,
        pass_direction=rec.before_scene.pass_direction,
        polarization=rec.before_scene.polarization,
        source_url=rec.before_scene.source_url,
        product_type=rec.before_scene.product_type,
        sensor_mode=rec.before_scene.sensor_mode,
        coverage_ratio=rec.before_scene.coverage_ratio,
        cdse_id=rec.before_scene.cdse_id,
    )
    after_info = DiscoveredSceneInfo(
        scene_id=rec.after_scene.scene_id,
        acquired_at=rec.after_scene.acquired_at,
        relative_orbit=rec.after_scene.relative_orbit,
        pass_direction=rec.after_scene.pass_direction,
        polarization=rec.after_scene.polarization,
        source_url=rec.after_scene.source_url,
        product_type=rec.after_scene.product_type,
        sensor_mode=rec.after_scene.sensor_mode,
        coverage_ratio=rec.after_scene.coverage_ratio,
        cdse_id=rec.after_scene.cdse_id,
    )

    return SceneDiscoveryResponse(
        event_date=rec.event_date,
        relative_orbit=rec.relative_orbit,
        pass_direction=rec.orbit_direction,
        temporal_baseline_days=rec.temporal_baseline_days,
        scientific_rationale=rec.scientific_rationale,
        before_scene=before_info,
        after_scene=after_info,
        provenance_metadata=rec.provenance_metadata,
    )


@app.post("/api/v1/detection/baseline", response_model=BaselineDetectionResponse)
def run_detection(req: BaselineDetectionRequest) -> BaselineDetectionResponse:
    """Execute baseline change detection on radar backscatter data."""
    if req.pre_db_values is not None and req.post_db_values is not None:
        pre_arr = np.array(req.pre_db_values, dtype=np.float32)
        post_arr = np.array(req.post_db_values, dtype=np.float32)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direct array values (pre_db_values, post_db_values) are required for baseline detection execution."
        )

    if pre_arr.shape != post_arr.shape:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Raster shape mismatch: pre is {pre_arr.shape}, post is {post_arr.shape}."
        )

    # Calculate transform from bounds or default
    if req.bounds and len(req.bounds) == 4:
        minx, miny, maxx, maxy = req.bounds
        transform = from_bounds(minx, miny, maxx, maxy, pre_arr.shape[1], pre_arr.shape[0])
    else:
        transform = from_bounds(85.1, 27.8, 85.3, 28.0, pre_arr.shape[1], pre_arr.shape[0])

    config = BaselineDetectionConfig(
        water_threshold_db=req.water_threshold_db,
        debris_threshold_db=req.debris_threshold_db,
        permanent_water_db=req.permanent_water_db,
        use_adaptive_otsu=req.use_adaptive_otsu,
    )

    try:
        result = run_baseline_detection(
            pre_db=pre_arr,
            post_db=post_arr,
            transform=transform,
            crs=req.crs,
            config=config,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change detection processing failed: {str(e)}"
        )

    gdf = result.to_geodataframe()
    geojson_features = json.loads(gdf.to_json()) if not gdf.empty else {"type": "FeatureCollection", "features": []}

    valid_unc = result.uncertainty_score[result.valid_mask]
    unc_summary = {
        "mean_uncertainty": float(np.mean(valid_unc)) if len(valid_unc) > 0 else 1.0,
        "max_uncertainty": float(np.max(valid_unc)) if len(valid_unc) > 0 else 1.0,
        "min_uncertainty": float(np.min(valid_unc)) if len(valid_unc) > 0 else 0.0,
    }

    return BaselineDetectionResponse(
        status="success",
        summary_statistics=result.summary_statistics,
        candidate_features_geojson=geojson_features,
        uncertainty_summary=unc_summary,
        provenance={
            "pre_scene_id": req.pre_scene_id,
            "post_scene_id": req.post_scene_id,
            "crs": req.crs,
            "processed_at": datetime.utcnow().isoformat(),
        },
    )


@app.post("/api/v1/analysis/exposure", response_model=RoadExposureResponse)
def analyze_exposure(req: RoadExposureRequest) -> RoadExposureResponse:
    """Assess potential road network exposure and settlement isolation."""
    try:
        analyzer = RoadNetworkConnectivityAnalyzer(req.snapshot_date, req.event_date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Temporal integrity violation: {str(e)}"
        )

    # Load candidate flood polygons
    try:
        flood_gdf = gpd.GeoDataFrame.from_features(req.candidate_flood_geojson.get("features", []), crs="EPSG:4326")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid candidate flood GeoJSON: {e}"
        )

    # Load roads GeoDataFrame
    if req.roads_geojson and "features" in req.roads_geojson:
        roads_gdf = gpd.GeoDataFrame.from_features(req.roads_geojson["features"], crs="EPSG:4326")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pre-event roads GeoJSON is required."
        )

    # Load settlements GeoDataFrame
    settlements_gdf = None
    if req.settlements_geojson and "features" in req.settlements_geojson:
        settlements_gdf = gpd.GeoDataFrame.from_features(req.settlements_geojson["features"], crs="EPSG:4326")

    analyzer.build_graph_from_geodataframe(roads_gdf, settlements_gdf)
    summary, exposed_roads = analyzer.analyze_flood_impact(flood_gdf)

    exposed_roads_json = json.loads(exposed_roads.to_json()) if not exposed_roads.empty else {"type": "FeatureCollection", "features": []}

    return RoadExposureResponse(
        total_roads_analyzed_km=summary.total_roads_analyzed_km,
        exposed_roads_km=summary.exposed_roads_km,
        exposed_road_percentage=summary.exposed_road_percentage,
        exposed_bridges_count=summary.exposed_bridges_count,
        candidate_isolated_settlements_count=summary.candidate_isolated_settlements_count,
        candidate_isolated_settlements=summary.candidate_isolated_settlements,
        disclaimer=summary.disclaimer,
        exposed_roads_geojson=exposed_roads_json,
    )
