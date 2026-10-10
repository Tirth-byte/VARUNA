"""Pydantic schemas for VARUNA FastAPI REST endpoints."""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GeoJSONGeometry(BaseModel):
    type: str = Field(..., example="Polygon")
    coordinates: List[Any] = Field(...)


class SceneDiscoveryRequest(BaseModel):
    aoi: GeoJSONGeometry = Field(
        ...,
        description="GeoJSON geometry (Polygon or MultiPolygon) representing the Area of Interest in EPSG:4326."
    )
    event_date: datetime = Field(
        ...,
        description="Estimated flood event date and time (ISO format)."
    )
    pre_window_days: int = Field(30, ge=1, le=120)
    post_window_days: int = Field(15, ge=1, le=60)
    min_aoi_coverage: float = Field(0.50, ge=0.05, le=1.0)


class DiscoveredSceneInfo(BaseModel):
    scene_id: str
    acquired_at: datetime
    relative_orbit: int
    pass_direction: str
    polarization: str
    source_url: str
    product_type: str
    sensor_mode: str
    coverage_ratio: float
    cdse_id: Optional[str] = None


class SceneDiscoveryResponse(BaseModel):
    event_date: datetime
    relative_orbit: int
    pass_direction: str
    temporal_baseline_days: float
    scientific_rationale: str
    before_scene: DiscoveredSceneInfo
    after_scene: DiscoveredSceneInfo
    provenance_metadata: Dict[str, Any]


class BaselineDetectionRequest(BaseModel):
    pre_scene_id: str
    post_scene_id: str
    crs: str = "EPSG:4326"
    water_threshold_db: float = Field(-3.5, description="Backscatter drop threshold for candidate water")
    debris_threshold_db: float = Field(3.5, description="Backscatter rise threshold for candidate debris")
    permanent_water_db: float = Field(-16.0, description="Threshold for permanent water")
    use_adaptive_otsu: bool = Field(False, description="Automatically calculate Otsu threshold")
    # For direct API testing with synthetic/in-memory matrices:
    pre_db_values: Optional[List[List[float]]] = None
    post_db_values: Optional[List[List[float]]] = None
    bounds: Optional[List[float]] = Field(None, description="[minx, miny, maxx, maxy]")


class BaselineDetectionResponse(BaseModel):
    status: str
    summary_statistics: Dict[str, Any]
    candidate_features_geojson: Dict[str, Any]
    uncertainty_summary: Dict[str, float]
    provenance: Dict[str, Any]


class RoadExposureRequest(BaseModel):
    event_date: datetime
    snapshot_date: datetime
    candidate_flood_geojson: Dict[str, Any] = Field(
        ...,
        description="GeoJSON FeatureCollection of candidate flood polygons."
    )
    roads_geojson: Optional[Dict[str, Any]] = None
    settlements_geojson: Optional[Dict[str, Any]] = None


class RoadExposureResponse(BaseModel):
    total_roads_analyzed_km: float
    exposed_roads_km: float
    exposed_road_percentage: float
    exposed_bridges_count: int
    candidate_isolated_settlements_count: int
    candidate_isolated_settlements: List[str]
    disclaimer: str
    exposed_roads_geojson: Dict[str, Any]


class CreateJobRequest(BaseModel):
    aoi: GeoJSONGeometry
    event_date: datetime
    pre_window_days: int = Field(30, ge=1, le=120)
    post_window_days: int = Field(15, ge=1, le=60)
    water_threshold_db: float = -3.5
    debris_threshold_db: float = 3.5


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress_percent: int
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    selected_scenes: Optional[Dict[str, Any]] = None
    artifacts: Dict[str, str] = Field(default_factory=dict)
    summary_results: Optional[Dict[str, Any]] = None
    logs: List[str] = Field(default_factory=list)


class ValidationBenchmarkRequest(BaseModel):
    predicted_binary_mask: List[List[int]]
    reference_binary_mask: List[List[int]]
    reference_dataset_name: str = "Copernicus EMS EMSR927"
    event_date: datetime
    pixel_area_m2: float = 100.0


class ValidationBenchmarkResponse(BaseModel):
    reference_dataset_name: str
    reference_activation_code: str
    valid_evaluated_area_km2: float
    iou_score: float
    precision_score: float
    recall_score: float
    f1_score: float
    accuracy_score: float
    confusion_matrix: Dict[str, int]
    methodological_notes: str
    limitations: Dict[str, str]


class HealthResponse(BaseModel):
    status: str
    system: str
    version: str
    library_versions: Dict[str, str]
    cdse_credentials_configured: bool
    scientific_integrity_mode: str
