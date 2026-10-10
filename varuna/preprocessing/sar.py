"""SAR Preprocessing: Radiometric Calibration, Speckle Filtering & Quality Masking.

Implements standard SAR procedures:
- DN to Sigma Nought (dB) calibration
- Spatial Lee filter for speckle reduction
- Border/nodata mask generation
- Terrain artifact & shadow hazard flagging
"""

from __future__ import annotations
import numpy as np
from scipy.ndimage import uniform_filter
from typing import Tuple, Optional, Dict, Any


def calibrate_to_sigma0_db(
    raw_dn: np.ndarray,
    calibration_constant: Optional[float] = None,
    min_db: float = -35.0,
    max_db: float = 10.0,
) -> np.ndarray:
    """Calibrate raw SAR Digital Numbers (DN) to Sigma0 backscatter in decibels (dB).

    Formula:
      Sigma0_linear = (DN^2) / (A^2)  [if calibration constant A provided]
      Sigma0_dB = 10 * log10(Sigma0_linear)
    """
    arr = raw_dn.astype(np.float32)
    # Mask non-positive or invalid DN
    invalid_mask = (arr <= 0) | np.isnan(arr) | np.isinf(arr)

    if calibration_constant is not None and calibration_constant > 0:
        linear_sigma0 = (arr ** 2) / (calibration_constant ** 2)
    else:
        # Default assumption: input is already linear power or uncalibrated amplitude
        linear_sigma0 = np.maximum(arr, 1e-7)

    # Avoid log of zero
    safe_linear = np.where(linear_sigma0 > 1e-7, linear_sigma0, 1e-7)
    db_array = 10.0 * np.log10(safe_linear)

    # Clip to physical radar backscatter bounds for C-band SAR
    db_array = np.clip(db_array, min_db, max_db)
    db_array[invalid_mask] = np.nan
    return db_array


def lee_speckle_filter(
    image: np.ndarray,
    window_size: int = 5,
    num_looks: float = 4.0,
) -> np.ndarray:
    """Adaptive Lee filter for SAR speckle noise reduction.

    Calculates local statistics to smooth homogeneous areas while preserving
    strong point targets and sharp water/land edges.

    Parameters:
      image: 2D float array (in linear power or dB)
      window_size: Odd integer (e.g. 5, 7)
      num_looks: Equivalent number of looks (ENL) for Sentinel-1 GRD (~4.4 for IW GRDH)
    """
    if window_size % 2 == 0:
        raise ValueError(f"window_size must be an odd integer, got {window_size}")

    nan_mask = np.isnan(image)
    filled_img = np.where(nan_mask, 0.0, image)

    # Local mean
    mean = uniform_filter(filled_img, size=window_size)
    # Local mean of square
    mean_sq = uniform_filter(filled_img ** 2, size=window_size)
    # Local variance
    variance = np.maximum(0.0, mean_sq - (mean ** 2))

    # Speckle noise relative variance
    noise_var = 1.0 / max(num_looks, 1.0)

    # Weighting factor W: 0 in flat/homogeneous areas, 1 near edges/targets
    denom = variance + 1e-8
    weights = np.maximum(0.0, (variance - (mean ** 2) * noise_var) / denom)
    weights = np.clip(weights, 0.0, 1.0)

    filtered = mean + weights * (filled_img - mean)
    filtered[nan_mask] = np.nan
    return filtered


def create_valid_mask(
    raster: np.ndarray,
    nodata_value: Optional[float] = None,
    min_physical_val: float = -35.0,
    max_physical_val: float = 15.0,
) -> np.ndarray:
    """Generate boolean mask of valid physical SAR pixels. True = Valid, False = Invalid/Nodata."""
    valid = ~np.isnan(raster) & ~np.isinf(raster)
    if nodata_value is not None:
        valid &= (raster != nodata_value)
    
    # Boundary check for physical plausibility
    valid &= (raster >= min_physical_val) & (raster <= max_physical_val)
    return valid


def flag_terrain_artifacts(
    slope_degrees: np.ndarray,
    steep_slope_threshold: float = 25.0,
) -> np.ndarray:
    """Identify steep mountain slope pixels where radar layover and shadow mimic water.

    True indicates high risk of terrain-induced radar false positive.
    """
    return slope_degrees >= steep_slope_threshold
