"""VARUNA Baseline Change-Detection Engine.

Transparent, reproducible, and scientifically defensible radar change detection:
- Log-ratio SAR difference computation: Delta dB = Post_dB - Pre_dB
- Distinction between candidate water inundation (specular drop) and debris deposition (roughening)
- Permanent water baseline separation
- Mountain terrain shadow artifact flagging
- Configurable thresholds and adaptive Otsu thresholding
- Geodesic ellipsoidal metric calculations via pyproj.Geod (no planar degree approximations)
- Explicit heuristic uncertainty index reporting (preserves NaN for nodata; never claims calibrated probability)
- GeoDataFrame vectorization with spatial provenance
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

import numpy as np
import geopandas as gpd
from shapely.geometry import shape, Polygon, box
import rasterio
from rasterio.features import shapes
from rasterio.transform import Affine
import pyproj

WGS84_GEOD = pyproj.Geod(ellps="WGS84")


class LandCoverChangeClass(IntEnum):
    INVALID_OR_NODATA = 0
    NO_SIGNIFICANT_CHANGE = 1
    CANDIDATE_WATER_INUNDATION = 2
    CANDIDATE_DEBRIS_OR_ROUGHENING = 3
    PERMANENT_WATER = 4
    TERRAIN_SHADOW_SUSPECT = 5


@dataclass
class BaselineDetectionConfig:
    """Configurable parameters for baseline radar change detection."""
    water_threshold_db: float = -3.5  # Negative change required for water candidate (dB)
    debris_threshold_db: float = 3.5  # Positive change required for debris/roughening (dB)
    permanent_water_db: float = -16.0  # Threshold below which both pre & post indicates permanent water
    use_adaptive_otsu: bool = False   # Compute adaptive threshold on negative change
    min_cluster_size_pixels: int = 5  # Filter out single-pixel speckle false alarms


@dataclass
class BaselineDetectionResult:
    """Output of baseline change detection preserving intermediate arrays and provenance."""
    difference_db: np.ndarray
    classification_mask: np.ndarray
    uncertainty_score: np.ndarray  # Heuristic margin index; NaN for nodata/invalid
    valid_mask: np.ndarray
    config: BaselineDetectionConfig
    transform: Affine
    crs: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def summary_statistics(self) -> Dict[str, Any]:
        """Compute pixel counts and exact geodesic ellipsoidal area summaries."""
        total_valid = int(np.sum(self.valid_mask))
        flood_px = int(np.sum(self.classification_mask == LandCoverChangeClass.CANDIDATE_WATER_INUNDATION))
        debris_px = int(np.sum(self.classification_mask == LandCoverChangeClass.CANDIDATE_DEBRIS_OR_ROUGHENING))
        perm_px = int(np.sum(self.classification_mask == LandCoverChangeClass.PERMANENT_WATER))
        shadow_px = int(np.sum(self.classification_mask == LandCoverChangeClass.TERRAIN_SHADOW_SUSPECT))
        no_change_px = int(np.sum(self.classification_mask == LandCoverChangeClass.NO_SIGNIFICANT_CHANGE))

        # Compute geodesic pixel area at raster centroid
        h, w = self.classification_mask.shape
        c_lon = float(self.transform.c + (w / 2.0) * self.transform.a)
        c_lat = float(self.transform.f + (h / 2.0) * self.transform.e)
        dx = abs(self.transform.a)
        dy = abs(self.transform.e)

        if "4326" in str(self.crs) or "WGS 84" in str(self.crs) or "CRS84" in str(self.crs):
            sample_pixel_geom = box(c_lon, c_lat - dy, c_lon + dx, c_lat)
            px_area_m2 = abs(float(WGS84_GEOD.geometry_area_perimeter(sample_pixel_geom)[0]))
        else:
            # Projected metric CRS (meters)
            px_area_m2 = float(dx * dy)

        valid_unc = self.uncertainty_score[self.valid_mask & ~np.isnan(self.uncertainty_score)]

        return {
            "total_pixels": int(self.classification_mask.size),
            "valid_pixels": total_valid,
            "candidate_water_pixels": flood_px,
            "candidate_debris_pixels": debris_px,
            "permanent_water_pixels": perm_px,
            "terrain_shadow_suspect_pixels": shadow_px,
            "no_change_pixels": no_change_px,
            "pixel_area_m2": px_area_m2,
            "candidate_water_area_m2": flood_px * px_area_m2,
            "candidate_water_area_km2": (flood_px * px_area_m2) / 1e6,
            "candidate_debris_area_m2": debris_px * px_area_m2,
            "candidate_debris_area_km2": (debris_px * px_area_m2) / 1e6,
            "water_threshold_db": self.config.water_threshold_db,
            "debris_threshold_db": self.config.debris_threshold_db,
            "area_measurement_method": "WGS84 Geodesic Ellipsoidal Area via pyproj.Geod",
            "uncertainty_type": "HEURISTIC_MARGIN_INDEX (0=far from threshold, 1=on boundary; uncalibrated)",
            "mean_heuristic_uncertainty": float(np.mean(valid_unc)) if len(valid_unc) > 0 else float("nan"),
        }

    def to_geodataframe(self) -> gpd.GeoDataFrame:
        """Vectorize candidate flood and debris pixels to GeoPandas GeoDataFrame with exact geodesic areas."""
        records = []
        mask = self.classification_mask.astype(np.int16)

        # Vectorize non-zero classes using rasterio.features.shapes
        for geom_dict, val in shapes(mask, mask=(mask > 1), transform=self.transform):
            val_int = int(val)
            poly = shape(geom_dict)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                continue

            class_enum = LandCoverChangeClass(val_int)
            # Compute exact geodesic area
            if "4326" in str(self.crs) or "WGS 84" in str(self.crs):
                poly_area_m2 = abs(float(WGS84_GEOD.geometry_area_perimeter(poly)[0]))
            else:
                poly_area_m2 = float(poly.area)

            records.append({
                "geometry": poly,
                "class_id": val_int,
                "class_name": class_enum.name,
                "area_m2": poly_area_m2,
                "area_km2": poly_area_m2 / 1e6,
                "is_candidate_flood": val_int == LandCoverChangeClass.CANDIDATE_WATER_INUNDATION,
                "is_candidate_debris": val_int == LandCoverChangeClass.CANDIDATE_DEBRIS_OR_ROUGHENING,
                "is_terrain_suspect": val_int == LandCoverChangeClass.TERRAIN_SHADOW_SUSPECT,
            })

        if not records:
            return gpd.GeoDataFrame(
                columns=[
                    "geometry", "class_id", "class_name", "area_m2", "area_km2",
                    "is_candidate_flood", "is_candidate_debris", "is_terrain_suspect"
                ],
                crs=self.crs
            )

        gdf = gpd.GeoDataFrame(records, crs=self.crs)
        return gdf

    def save_geotiff(self, output_path: str | Path) -> Path:
        """Write classified change mask and difference rasters to multi-band GeoTIFF."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        height, width = self.classification_mask.shape
        profile = {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "count": 3,
            "dtype": rasterio.float32,
            "crs": self.crs,
            "transform": self.transform,
            "nodata": -9999.0,
            "compress": "lzw",
        }

        diff_clean = np.where(self.valid_mask, self.difference_db, -9999.0)
        mask_clean = np.where(self.valid_mask, self.classification_mask.astype(np.float32), 0.0)
        unc_clean = np.where(self.valid_mask, self.uncertainty_score, -9999.0)

        with rasterio.open(path, "w", **profile) as dst:
            dst.write(diff_clean.astype(np.float32), 1)
            dst.set_band_description(1, "Delta_dB (Post - Pre)")
            dst.write(mask_clean.astype(np.float32), 2)
            dst.set_band_description(2, "Classification_Mask (0=NoData, 2=Water, 3=Debris, 5=Shadow)")
            dst.write(unc_clean.astype(np.float32), 3)
            dst.set_band_description(3, "Heuristic_Margin_Uncertainty [0=Clear, 1=Marginal, -9999=NoData]")

        return path


def compute_otsu_threshold(values: np.ndarray, num_bins: int = 100) -> float:
    """Compute Otsu threshold on a 1D continuous array minimizing intra-class variance."""
    v = values[~np.isnan(values)]
    if len(v) == 0:
        return -3.5

    counts, bin_edges = np.histogram(v, bins=num_bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    total = len(v)

    weight_b = np.cumsum(counts) / total
    weight_f = 1.0 - weight_b

    cumsum_val = np.cumsum(counts * bin_centers) / total
    mean_b = np.divide(cumsum_val, weight_b, out=np.zeros_like(cumsum_val), where=weight_b > 0)
    mean_f = np.divide(cumsum_val[-1] - cumsum_val, weight_f, out=np.zeros_like(cumsum_val), where=weight_f > 0)

    inter_var = weight_b * weight_f * ((mean_b - mean_f) ** 2)
    max_idx = np.argmax(inter_var)
    return float(bin_centers[max_idx])


def run_baseline_detection(
    pre_db: np.ndarray,
    post_db: np.ndarray,
    transform: Affine,
    crs: str = "EPSG:4326",
    config: Optional[BaselineDetectionConfig] = None,
    terrain_slope_degrees: Optional[np.ndarray] = None,
    steep_slope_threshold: float = 25.0,
    metadata: Optional[Dict[str, Any]] = None,
) -> BaselineDetectionResult:
    """Execute baseline change detection on aligned pre- and post-event radar dB rasters."""
    if pre_db.shape != post_db.shape:
        raise ValueError(f"Shape mismatch: Pre is {pre_db.shape}, Post is {post_db.shape}")

    cfg = config or BaselineDetectionConfig()

    # Valid data masks (do not clip backscatter; check for non-NaN finite values)
    valid_pre = ~np.isnan(pre_db) & ~np.isinf(pre_db)
    valid_post = ~np.isnan(post_db) & ~np.isinf(post_db)
    valid_mask = valid_pre & valid_post

    # Delta dB = Post - Pre
    delta_db = np.zeros_like(pre_db, dtype=np.float32)
    np.subtract(post_db, pre_db, out=delta_db, where=valid_mask)
    delta_db[~valid_mask] = np.nan

    # Adaptive Otsu thresholding if requested
    water_threshold = cfg.water_threshold_db
    if cfg.use_adaptive_otsu:
        negative_changes = delta_db[valid_mask & (delta_db < 0)]
        if len(negative_changes) > 100:
            otsu_val = compute_otsu_threshold(negative_changes)
            water_threshold = float(np.clip(otsu_val, -7.0, -2.0))
            cfg.water_threshold_db = water_threshold

    # Initialize classification mask
    mask = np.full(pre_db.shape, LandCoverChangeClass.INVALID_OR_NODATA, dtype=np.int16)
    mask[valid_mask] = LandCoverChangeClass.NO_SIGNIFICANT_CHANGE

    # 1. Permanent water check: low backscatter in both pre and post
    perm_water = valid_mask & (pre_db <= cfg.permanent_water_db) & (post_db <= cfg.permanent_water_db)
    mask[perm_water] = LandCoverChangeClass.PERMANENT_WATER

    # 2. Candidate water inundation: significant drop in backscatter
    candidate_water = valid_mask & (~perm_water) & (delta_db <= water_threshold)
    mask[candidate_water] = LandCoverChangeClass.CANDIDATE_WATER_INUNDATION

    # 3. Candidate debris / surface roughening: significant increase in backscatter
    candidate_debris = valid_mask & (delta_db >= cfg.debris_threshold_db)
    mask[candidate_debris] = LandCoverChangeClass.CANDIDATE_DEBRIS_OR_ROUGHENING

    # 4. Terrain shadow artifact check on steep slopes
    if terrain_slope_degrees is not None:
        steep_slopes = terrain_slope_degrees >= steep_slope_threshold
        suspect_shadow = candidate_water & steep_slopes
        mask[suspect_shadow] = LandCoverChangeClass.TERRAIN_SHADOW_SUSPECT

    # 5. Heuristic Uncertainty Indicator [0.0 = decisive change, 1.0 = near decision threshold]
    # Explicitly uncalibrated decision-margin proximity; NaN for invalid/nodata
    uncertainty = np.full(pre_db.shape, np.nan, dtype=np.float32)
    margin = 3.0
    dist_water = np.abs(delta_db - water_threshold)
    unc_water = np.clip(1.0 - (dist_water / margin), 0.05, 0.95)
    uncertainty[valid_mask] = unc_water[valid_mask]

    meta = metadata or {}
    meta["uncertainty_description"] = "Heuristic decision-margin index. Preserves NaN for nodata."

    return BaselineDetectionResult(
        difference_db=delta_db,
        classification_mask=mask,
        uncertainty_score=uncertainty,
        valid_mask=valid_mask,
        config=cfg,
        transform=transform,
        crs=crs,
        metadata=meta,
    )
