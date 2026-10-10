"""Geospatial Alignment, Reprojection & Raster Comparability Checks.

Ensures that before and after radar scenes share identical CRS, pixel resolution,
bounding box, and affine transform prior to mathematical change detection.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import Affine


@dataclass
class RasterMetadata:
    """Core geospatial metadata for a raster file."""
    crs: str
    width: int
    height: int
    bounds: Tuple[float, float, float, float]  # (minx, miny, maxx, maxy)
    transform: Affine
    nodata: Optional[float]
    resolution: Tuple[float, float]  # (dx, dy)


def inspect_raster(path: str | Path) -> RasterMetadata:
    """Read geospatial metadata from a raster file without loading full pixel array into memory."""
    with rasterio.open(path) as src:
        crs_str = src.crs.to_string() if src.crs else "UNKNOWN"
        bounds = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
        res_x, res_y = abs(src.res[0]), abs(src.res[1])
        return RasterMetadata(
            crs=crs_str,
            width=src.width,
            height=src.height,
            bounds=bounds,
            transform=src.transform,
            nodata=src.nodata,
            resolution=(res_x, res_y),
        )


def check_spatial_comparability(
    meta_before: RasterMetadata,
    meta_after: RasterMetadata,
    tolerance: float = 1e-4,
) -> bool:
    """Verify if two rasters are geometrically identical (same CRS, shape, transform)."""
    if meta_before.crs != meta_after.crs:
        raise ValueError(
            f"CRS Mismatch: Before raster is {meta_before.crs}, but after raster is {meta_after.crs}. "
            "Rasters must be reprojected to a common CRS before change detection."
        )

    if meta_before.width != meta_after.width or meta_before.height != meta_after.height:
        return False

    # Check bounds compatibility
    for b_before, b_after in zip(meta_before.bounds, meta_after.bounds):
        if abs(b_before - b_after) > tolerance:
            return False

    return True


def align_raster_to_reference(
    source_path: str | Path,
    reference_path: str | Path,
    output_path: str | Path,
    resampling_method: Resampling = Resampling.bilinear,
) -> RasterMetadata:
    """Reproject and resample source raster to match exactly the reference raster grid."""
    with rasterio.open(reference_path) as ref_src:
        ref_crs = ref_src.crs
        ref_transform = ref_src.transform
        ref_width = ref_src.width
        ref_height = ref_src.height
        ref_profile = ref_src.profile.copy()

    with rasterio.open(source_path) as src:
        destination = np.full((ref_height, ref_width), fill_value=src.nodata or np.nan, dtype=np.float32)

        reproject(
            source=rasterio.band(src, 1),
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            resampling=resampling_method,
            src_nodata=src.nodata,
            dst_nodata=src.nodata or -9999.0,
        )

    ref_profile.update(dtype=rasterio.float32, count=1, nodata=src.nodata or -9999.0)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(output_path, "w", **ref_profile) as dst:
        dst.write(destination, 1)

    return inspect_raster(output_path)
