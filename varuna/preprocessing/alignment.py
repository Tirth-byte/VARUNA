"""Geospatial Alignment, Common Analysis Grid & Raster Comparability Engine.

Ensures that multi-temporal radar scenes share identical CRS, affine transform,
pixel coordinates, and bounding box prior to mathematical change detection.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any, Union
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import Affine, from_bounds


class NonOverlappingRasterError(ValueError):
    """Raised when two rasters share no common geographic area."""
    pass


class IncompatibleCRSError(ValueError):
    """Raised when two rasters have incompatible or unprojectable coordinate reference systems."""
    pass


@dataclass(frozen=True)
class RasterMetadata:
    """Core geospatial metadata for a raster file."""
    crs: str
    width: int
    height: int
    bounds: Tuple[float, float, float, float]  # (minx, miny, maxx, maxy)
    transform: Affine
    nodata: Optional[float]
    resolution: Tuple[float, float]  # (dx, dy)


@dataclass(frozen=True)
class CommonAnalysisGrid:
    """Defines a deterministic, standardized analysis grid for reproducible comparisons."""
    crs: str
    bounds: Tuple[float, float, float, float]  # (minx, miny, maxx, maxy)
    resolution: Tuple[float, float]           # (dx, dy) in CRS units
    width: int
    height: int
    transform: Affine
    nodata: float = -9999.0

    @classmethod
    def from_bounds_and_resolution(
        cls,
        bounds: Tuple[float, float, float, float],
        resolution: Tuple[float, float],
        crs: str = "EPSG:4326",
        nodata: float = -9999.0,
    ) -> CommonAnalysisGrid:
        minx, miny, maxx, maxy = bounds
        dx, dy = abs(resolution[0]), abs(resolution[1])
        if minx >= maxx or miny >= maxy:
            raise ValueError(f"Invalid bounding box: {bounds}")
        width = max(1, int(np.round((maxx - minx) / dx)))
        height = max(1, int(np.round((maxy - miny) / dy)))
        # Ensure snapped bounds
        snapped_maxx = minx + width * dx
        snapped_miny = maxy - height * dy
        transform = from_bounds(minx, snapped_miny, snapped_maxx, maxy, width, height)
        return cls(
            crs=crs,
            bounds=(minx, snapped_miny, snapped_maxx, maxy),
            resolution=(dx, dy),
            width=width,
            height=height,
            transform=transform,
            nodata=nodata,
        )


def inspect_raster(path: str | Path) -> RasterMetadata:
    """Read geospatial metadata from a raster file without loading full pixel array."""
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


def compute_raster_overlap(
    meta_a: RasterMetadata,
    meta_b: RasterMetadata,
) -> Optional[Tuple[float, float, float, float]]:
    """Compute geographic intersection bounds of two rasters.

    Requires identical CRS or raises IncompatibleCRSError.
    Returns (minx, miny, maxx, maxy) or None if disjoint.
    """
    crs_a = CRS.from_string(meta_a.crs)
    crs_b = CRS.from_string(meta_b.crs)
    if crs_a != crs_b:
        raise IncompatibleCRSError(f"Cannot compute overlap directly between different CRS: {meta_a.crs} vs {meta_b.crs}")

    minx = max(meta_a.bounds[0], meta_b.bounds[0])
    miny = max(meta_a.bounds[1], meta_b.bounds[1])
    maxx = min(meta_a.bounds[2], meta_b.bounds[2])
    maxy = min(meta_a.bounds[3], meta_b.bounds[3])

    if minx >= maxx or miny >= maxy:
        return None
    return (minx, miny, maxx, maxy)


def check_spatial_comparability(
    meta_before: RasterMetadata,
    meta_after: RasterMetadata,
    tolerance: float = 1e-4,
) -> bool:
    """Verify if two rasters are geometrically identical on the pixel grid.

    Checks:
    - Equivalent CRS
    - Matching dimensions (width, height)
    - Matching Affine transform (origin, pixel size, rotation)
    - Non-empty geographic overlap
    """
    try:
        crs_before = CRS.from_string(meta_before.crs)
        crs_after = CRS.from_string(meta_after.crs)
        if crs_before != crs_after:
            raise IncompatibleCRSError(
                f"CRS Mismatch: Before raster is {meta_before.crs}, but after raster is {meta_after.crs}."
            )
    except Exception as e:
        if isinstance(e, IncompatibleCRSError):
            raise
        raise IncompatibleCRSError(f"Invalid CRS encountered: {e}")

    # Check non-overlapping bounds
    overlap = compute_raster_overlap(meta_before, meta_after)
    if overlap is None:
        raise NonOverlappingRasterError(
            f"Rasters do not overlap geographically. Bounds A: {meta_before.bounds}, Bounds B: {meta_after.bounds}"
        )

    if meta_before.width != meta_after.width or meta_before.height != meta_after.height:
        return False

    # Check affine transform elements: [a, b, c, d, e, f]
    t1 = meta_before.transform
    t2 = meta_after.transform
    for val1, val2 in zip([t1.a, t1.b, t1.c, t1.d, t1.e, t1.f], [t2.a, t2.b, t2.c, t2.d, t2.e, t2.f]):
        if abs(val1 - val2) > tolerance:
            return False

    return True


def reproject_to_grid(
    source_path: str | Path,
    target_grid: CommonAnalysisGrid,
    output_path: str | Path,
    resampling_method: Resampling = Resampling.bilinear,
) -> RasterMetadata:
    """Reproject and resample a source raster onto the exact CommonAnalysisGrid."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(source_path) as src:
        dst_crs = CRS.from_string(target_grid.crs)
        destination = np.full((target_grid.height, target_grid.width), fill_value=target_grid.nodata, dtype=np.float32)

        reproject(
            source=rasterio.band(src, 1),
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=target_grid.transform,
            dst_crs=dst_crs,
            resampling=resampling_method,
            src_nodata=src.nodata,
            dst_nodata=target_grid.nodata,
        )

        profile = {
            "driver": "GTiff",
            "height": target_grid.height,
            "width": target_grid.width,
            "count": 1,
            "dtype": rasterio.float32,
            "crs": dst_crs,
            "transform": target_grid.transform,
            "nodata": target_grid.nodata,
            "compress": "lzw",
        }

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(destination, 1)

    return inspect_raster(output_path)


def align_raster_to_reference(
    source_path: str | Path,
    reference_path: str | Path,
    output_path: str | Path,
    resampling_method: Resampling = Resampling.bilinear,
) -> RasterMetadata:
    """Reproject source raster to match exactly the reference raster grid."""
    ref_meta = inspect_raster(reference_path)
    target_grid = CommonAnalysisGrid(
        crs=ref_meta.crs,
        bounds=ref_meta.bounds,
        resolution=ref_meta.resolution,
        width=ref_meta.width,
        height=ref_meta.height,
        transform=ref_meta.transform,
        nodata=ref_meta.nodata or -9999.0,
    )
    return reproject_to_grid(source_path, target_grid, output_path, resampling_method)


def align_pair_to_common_analysis_grid(
    pre_path: str | Path,
    post_path: str | Path,
    output_dir: str | Path,
    target_crs: Optional[str] = None,
    target_resolution: Optional[Tuple[float, float]] = None,
    resampling_method: Resampling = Resampling.bilinear,
) -> Tuple[Path, Path, np.ndarray, CommonAnalysisGrid]:
    """Reproject both pre- and post-event rasters onto a shared analysis grid.

    Returns:
      (aligned_pre_path, aligned_post_path, joint_valid_mask, common_grid)
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_pre = inspect_raster(pre_path)
    meta_post = inspect_raster(post_path)

    chosen_crs = target_crs or meta_pre.crs
    chosen_res = target_resolution or meta_pre.resolution

    overlap = compute_raster_overlap(meta_pre, meta_post)
    if overlap is None:
        raise NonOverlappingRasterError(
            f"Pre- and post-event rasters do not overlap. Bounds pre: {meta_pre.bounds}, Bounds post: {meta_post.bounds}"
        )

    grid = CommonAnalysisGrid.from_bounds_and_resolution(
        bounds=overlap,
        resolution=chosen_res,
        crs=chosen_crs,
        nodata=-9999.0,
    )

    aligned_pre = out_dir / "aligned_pre.tif"
    aligned_post = out_dir / "aligned_post.tif"

    reproject_to_grid(pre_path, grid, aligned_pre, resampling_method)
    reproject_to_grid(post_path, grid, aligned_post, resampling_method)

    # Compute joint valid mask
    with rasterio.open(aligned_pre) as src_pre, rasterio.open(aligned_post) as src_post:
        arr_pre = src_pre.read(1)
        arr_post = src_post.read(1)
        valid_pre = (arr_pre != grid.nodata) & ~np.isnan(arr_pre)
        valid_post = (arr_post != grid.nodata) & ~np.isnan(arr_post)
        joint_valid = valid_pre & valid_post

    return aligned_pre, aligned_post, joint_valid, grid
