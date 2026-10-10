"""Unit tests for SAR preprocessing, calibration, speckle filtering, and raster alignment."""

import unittest
import numpy as np
import rasterio
from rasterio.transform import from_origin

from varuna.preprocessing.sar import (
    calibrate_to_sigma0_db,
    lee_speckle_filter,
    create_valid_mask,
    flag_terrain_artifacts,
)
from varuna.preprocessing.alignment import (
    RasterMetadata,
    check_spatial_comparability,
)


class TestSARPreprocessing(unittest.TestCase):
    def test_calibrate_to_sigma0_db(self):
        # Synthetic Digital Numbers (DN)
        raw_dn = np.array([
            [100.0, 50.0],
            [0.0, -10.0],  # Invalid / border pixels
        ])
        calibrated = calibrate_to_sigma0_db(raw_dn, calibration_constant=10.0)
        # For DN=100, constant=10: linear = 100^2 / 10^2 = 100. dB = 10 * log10(100) = 20 dB, clipped to max_db=10
        self.assertAlmostEqual(calibrated[0, 0], 10.0)
        # Invalid DN should be NaN
        self.assertTrue(np.isnan(calibrated[1, 0]))
        self.assertTrue(np.isnan(calibrated[1, 1]))

    def test_lee_speckle_filter_reduces_variance(self):
        # Generate synthetic homogeneous field with multiplicative speckle noise
        np.random.seed(42)
        true_val = 10.0
        noisy = true_val + np.random.normal(0, 3.0, size=(50, 50))
        var_before = float(np.var(noisy))

        filtered = lee_speckle_filter(noisy, window_size=5, num_looks=4.0)
        var_after = float(np.var(filtered))

        # Filtered homogeneous area must have significantly lower variance
        self.assertLess(var_after, var_before * 0.6)

    def test_create_valid_mask(self):
        data = np.array([
            [-20.0, -15.0],
            [-9999.0, np.nan],
        ])
        mask = create_valid_mask(data, nodata_value=-9999.0)
        self.assertTrue(mask[0, 0])
        self.assertTrue(mask[0, 1])
        self.assertFalse(mask[1, 0])
        self.assertFalse(mask[1, 1])

    def test_flag_terrain_artifacts(self):
        slopes = np.array([
            [10.0, 26.0],
            [35.0, 5.0],
        ])
        shadow_risk = flag_terrain_artifacts(slopes, steep_slope_threshold=25.0)
        self.assertFalse(shadow_risk[0, 0])
        self.assertTrue(shadow_risk[0, 1])
        self.assertTrue(shadow_risk[1, 0])
        self.assertFalse(shadow_risk[1, 1])

    def test_spatial_comparability_check(self):
        transform = from_origin(85.0, 28.0, 0.0001, 0.0001)
        meta1 = RasterMetadata(
            crs="EPSG:4326",
            width=100,
            height=100,
            bounds=(85.0, 27.99, 85.01, 28.0),
            transform=transform,
            nodata=-9999.0,
            resolution=(0.0001, 0.0001),
        )
        meta2 = RasterMetadata(
            crs="EPSG:4326",
            width=100,
            height=100,
            bounds=(85.0, 27.99, 85.01, 28.0),
            transform=transform,
            nodata=-9999.0,
            resolution=(0.0001, 0.0001),
        )
        self.assertTrue(check_spatial_comparability(meta1, meta2))

        # CRS mismatch raises ValueError
        meta_utm = RasterMetadata(
            crs="EPSG:32645",
            width=100,
            height=100,
            bounds=(85.0, 27.99, 85.01, 28.0),
            transform=transform,
            nodata=-9999.0,
            resolution=(10.0, 10.0),
        )
        with self.assertRaises(ValueError):
            check_spatial_comparability(meta1, meta_utm)


if __name__ == "__main__":
    unittest.main()
