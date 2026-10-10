"""SAR Preprocessing: Rigorous Radiometric Calibration, Speckle Filtering & Quality Masking.

Conforms to standard ESA Sentinel-1 Level-1 GRD product calibration workflows:
- Explicit input unit specification (RAW_DN, AMPLITUDE, LINEAR_POWER, DECIBELS_DB)
- Rejection of missing calibration metadata (never silently treats DN as calibrated sigma0)
- Multiplicative Lee speckle filtering executed strictly in the linear intensity domain
- Nodata-aware local statistics preventing border artifact propagation
- Unclipped backscatter representation preserving physical radar response
"""

from __future__ import annotations
from enum import Enum
from typing import Tuple, Optional, Dict, Any, Union
import numpy as np
from scipy.ndimage import uniform_filter


class SARUnit(str, Enum):
    """Explicit measurement units for SAR raster data."""
    RAW_DN = "RAW_DN"                      # Raw Digital Numbers from Level-1 GRD/SLC
    AMPLITUDE = "AMPLITUDE"                # Linear radar amplitude |DN|
    LINEAR_POWER = "LINEAR_POWER"          # Calibrated linear Sigma Nought (sigma0)
    DECIBELS_DB = "DECIBELS_DB"            # Calibrated backscatter in decibels: 10*log10(sigma0)


class MissingCalibrationError(ValueError):
    """Raised when raw SAR measurements lack required radiometric calibration metadata."""
    pass


class InvalidSARUnitError(ValueError):
    """Raised when SAR data has an unrecognized or unsupported measurement unit."""
    pass


def calibrate_raw_dn_to_linear_sigma0(
    raw_dn: np.ndarray,
    calibration_constant: Optional[float] = None,
    calibration_lut: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Calibrate raw Sentinel-1 Level-1 GRD Digital Numbers (DN) to linear Sigma0 backscatter.

    Equation:
      sigma0_linear = (|DN|^2) / (A_sigma^2)
    where A_sigma is the calibration vector (LUT) from Sentinel-1 calibration XML.

    Fails closed if calibration vector or constant is not provided.
    """
    if calibration_constant is None and calibration_lut is None:
        raise MissingCalibrationError(
            "Missing calibration metadata. Raw Sentinel-1 DN cannot be transformed to backscatter "
            "without calibration LUT (A_sigma) or scalar calibration constant. "
            "Never treat raw uncalibrated DN as physical backscatter."
        )

    arr = np.asarray(raw_dn, dtype=np.float32)
    invalid_mask = np.isnan(arr) | np.isinf(arr) | (arr <= 0)

    if calibration_lut is not None:
        lut = np.asarray(calibration_lut, dtype=np.float32)
        if lut.shape != arr.shape:
            raise ValueError(f"Calibration LUT shape {lut.shape} does not match DN raster shape {arr.shape}")
        denom = np.square(lut)
        denom = np.where(denom <= 0, np.nan, denom)
        linear_sigma0 = np.square(arr) / denom
    else:
        if calibration_constant <= 0:
            raise ValueError(f"Calibration constant must be positive, got {calibration_constant}")
        linear_sigma0 = np.square(arr) / (calibration_constant ** 2)

    linear_sigma0[invalid_mask] = np.nan
    return linear_sigma0


def amplitude_to_linear_sigma0(
    amplitude: np.ndarray,
    calibration_constant: Optional[float] = None,
    calibration_lut: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Convert linear radar amplitude to calibrated linear Sigma Nought power."""
    # Amplitude is |DN|
    return calibrate_raw_dn_to_linear_sigma0(amplitude, calibration_constant, calibration_lut)


def linear_to_db(linear_sigma0: np.ndarray) -> np.ndarray:
    """Convert calibrated linear Sigma0 to decibels (dB): 10 * log10(sigma0).

    Does NOT artificially clip valid backscatter to conceal extremes.
    """
    arr = np.asarray(linear_sigma0, dtype=np.float32)
    invalid = np.isnan(arr) | np.isinf(arr) | (arr <= 0)

    # Calculate log10 only on positive values
    db = np.full_like(arr, np.nan)
    np.log10(arr, out=db, where=~invalid)
    db = 10.0 * db
    db[invalid] = np.nan
    return db


def db_to_linear(sigma0_db: np.ndarray) -> np.ndarray:
    """Convert calibrated backscatter in decibels (dB) back to linear Sigma0 power: 10^(dB / 10)."""
    arr = np.asarray(sigma0_db, dtype=np.float32)
    invalid = np.isnan(arr) | np.isinf(arr)
    linear = np.full_like(arr, np.nan)
    linear[~invalid] = np.power(10.0, arr[~invalid] / 10.0)
    return linear


def calibrate_sar_raster(
    data: np.ndarray,
    input_unit: Union[SARUnit, str],
    calibration_constant: Optional[float] = None,
    calibration_lut: Optional[np.ndarray] = None,
    output_unit: SARUnit = SARUnit.DECIBELS_DB,
) -> np.ndarray:
    """Standardized entrypoint to calibrate SAR raster to target unit."""
    try:
        unit = SARUnit(input_unit)
    except ValueError:
        raise InvalidSARUnitError(
            f"Unsupported input unit '{input_unit}'. Expected one of: "
            f"{[u.value for u in SARUnit]}"
        )

    # Step 1: Normalize to linear Sigma0 power
    if unit == SARUnit.RAW_DN:
        linear = calibrate_raw_dn_to_linear_sigma0(data, calibration_constant, calibration_lut)
    elif unit == SARUnit.AMPLITUDE:
        linear = amplitude_to_linear_sigma0(data, calibration_constant, calibration_lut)
    elif unit == SARUnit.LINEAR_POWER:
        linear = np.asarray(data, dtype=np.float32).copy()
    elif unit == SARUnit.DECIBELS_DB:
        linear = db_to_linear(data)
    else:
        raise InvalidSARUnitError(f"Unhandled unit {unit}")

    # Step 2: Convert to requested output unit
    if output_unit == SARUnit.LINEAR_POWER:
        return linear
    elif output_unit == SARUnit.DECIBELS_DB:
        return linear_to_db(linear)
    elif output_unit == SARUnit.AMPLITUDE:
        return np.sqrt(np.maximum(0.0, linear))
    else:
        raise ValueError(f"Unsupported output unit {output_unit}")


def calibrate_to_sigma0_db(
    raw_dn: np.ndarray,
    calibration_constant: Optional[float] = None,
    calibration_lut: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Backwards-compatible interface with mandatory calibration verification.

    Never assumes uncalibrated DN is linear power.
    """
    return calibrate_sar_raster(
        data=raw_dn,
        input_unit=SARUnit.RAW_DN,
        calibration_constant=calibration_constant,
        calibration_lut=calibration_lut,
        output_unit=SARUnit.DECIBELS_DB,
    )


def lee_speckle_filter(
    image: np.ndarray,
    window_size: int = 5,
    num_looks: float = 4.4,
    input_unit: SARUnit = SARUnit.LINEAR_POWER,
) -> np.ndarray:
    """Adaptive spatial Lee filter for SAR speckle noise reduction.

    CRITICAL SCIENTIFIC REQUIREMENT:
    Multiplicative speckle filtering must be executed in the LINEAR INTENSITY DOMAIN.
    Applying speckle filters directly to logarithmic decibels (dB) produces mathematically
    biased estimators because log transforms skew the speckle probability distribution.

    Parameters:
      image: 2D float array in linear power or specified unit
      window_size: Odd integer (e.g. 5, 7)
      num_looks: Equivalent number of looks (ENL) for Sentinel-1 GRD (~4.4 for IW GRDH)
      input_unit: Unit of input array (if DECIBELS_DB, converted to linear, filtered, converted back)
    """
    if window_size % 2 == 0 or window_size < 3:
        raise ValueError(f"window_size must be an odd integer >= 3, got {window_size}")

    # Enforce linear intensity domain for filtering
    was_db = False
    if input_unit == SARUnit.DECIBELS_DB:
        was_db = True
        linear_data = db_to_linear(image)
    elif input_unit in (SARUnit.LINEAR_POWER, SARUnit.RAW_DN, SARUnit.AMPLITUDE):
        linear_data = np.asarray(image, dtype=np.float32).copy()
    else:
        raise InvalidSARUnitError(f"Unsupported unit {input_unit} for speckle filtering")

    nan_mask = np.isnan(linear_data) | np.isinf(linear_data) | (linear_data <= 0)
    valid_mask = (~nan_mask).astype(np.float32)

    filled_img = np.where(nan_mask, 0.0, linear_data)

    # Nodata-aware local statistics
    valid_count = uniform_filter(valid_mask, size=window_size)
    min_valid_fraction = 0.3  # Require at least 30% valid pixels in window
    valid_window = valid_count >= min_valid_fraction

    # Local sum and local sum of squares
    local_sum = uniform_filter(filled_img, size=window_size)
    local_sq_sum = uniform_filter(filled_img ** 2, size=window_size)

    # Local mean and variance normalized by valid count
    safe_valid = np.maximum(valid_count, 1e-6)
    mean = local_sum / safe_valid
    mean_sq = local_sq_sum / safe_valid
    variance = np.maximum(0.0, mean_sq - (mean ** 2))

    # Speckle noise relative variance: sigma_v^2 = 1 / ENL
    noise_var = 1.0 / max(num_looks, 1.0)

    # Weight factor W
    denom = variance + 1e-10
    weights = np.maximum(0.0, (variance - (mean ** 2) * noise_var) / denom)
    weights = np.clip(weights, 0.0, 1.0)

    filtered = mean + weights * (filled_img - mean)
    # Mask out invalid pixels and windows with insufficient valid observations
    filtered[nan_mask | (~valid_window)] = np.nan

    if was_db:
        return linear_to_db(filtered)
    return filtered


def create_valid_mask(
    raster: np.ndarray,
    nodata_value: Optional[float] = None,
    min_physical_val: Optional[float] = None,
    max_physical_val: Optional[float] = None,
) -> np.ndarray:
    """Generate boolean mask of valid physical SAR pixels. True = Valid, False = Invalid/Nodata."""
    valid = ~np.isnan(raster) & ~np.isinf(raster)
    if nodata_value is not None:
        valid &= (raster != nodata_value)

    if min_physical_val is not None:
        valid &= (raster >= min_physical_val)
    if max_physical_val is not None:
        valid &= (raster <= max_physical_val)
    return valid


def flag_terrain_artifacts(
    slope_degrees: np.ndarray,
    steep_slope_threshold: float = 25.0,
) -> np.ndarray:
    """Identify steep mountain slope pixels where radar layover and shadow mimic water."""
    return slope_degrees >= steep_slope_threshold
