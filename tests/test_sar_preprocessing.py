"""Unit tests for SAR preprocessing, calibration verification, units, and raster alignment."""

import unittest
import numpy as np
import rasterio
from rasterio.transform import from_origin

from varuna.preprocessing.sar import (
    SARUnit,
    MissingCalibrationError,
    InvalidSARUnitError,
    calibrate_raw_dn_to_linear_sigma0,
    amplitude_to_linear_sigma0,
    linear_to_db,
    db_to_linear,
    calibrate_sar_raster,
    calibrate_to_sigma0_db,
    lee_speckle_filter,
    create_valid_mask,
    flag_terrain_artifacts,
)
from varuna.preprocessing.alignment import (
    RasterMetadata,
    CommonAnalysisGrid,
    NonOverlappingRasterError,
    IncompatibleCRSError,
    check_spatial_comparability,
    compute_raster_overlap,
)


class TestSARPreprocessing(unittest.TestCase):
    def test_missing_calibration_fails_closed(self):
        # Digital Numbers provided without calibration LUT or constant must raise MissingCalibrationError
        raw_dn = np.array([[100.0, 200.0], [150.0, 300.0]], dtype=np.float32)
        with self.assertRaises(MissingCalibrationError):
            calibrate_raw_dn_to_linear_sigma0(raw_dn, calibration_constant=None, calibration_lut=None)

        with self.assertRaises(MissingCalibrationError):
            calibrate_to_sigma0_db(raw_dn)

    def test_invalid_unit_rejected(self):
        data = np.array([[1.0, 2.0]], dtype=np.float32)
        with self.assertRaises(InvalidSARUnitError):
            calibrate_sar_raster(data, input_unit="UNKNOWN_OPTICAL_REFLECTANCE")

    def test_calibrate_with_scalar_constant(self):
        # DN = 100, constant = 10 -> sigma0_linear = 100^2 / 10^2 = 100
        # 10 * log10(100) = 20 dB
        raw_dn = np.array([[100.0]], dtype=np.float32)
        linear = calibrate_raw_dn_to_linear_sigma0(raw_dn, calibration_constant=10.0)
        self.assertAlmostEqual(linear[0, 0], 100.0)

        db = linear_to_db(linear)
        self.assertAlmostEqual(db[0, 0], 20.0)

        # Unclipped backscatter preserved (does not artificially clamp at 10 dB)
        self.assertEqual(db[0, 0], 20.0)

    def test_calibrate_with_lut_matrix(self):
        raw_dn = np.array([[100.0, 50.0]], dtype=np.float32)
        lut = np.array([[10.0, 5.0]], dtype=np.float32)
        linear = calibrate_raw_dn_to_linear_sigma0(raw_dn, calibration_lut=lut)
        # 100^2 / 10^2 = 100; 50^2 / 5^2 = 100
        self.assertAlmostEqual(linear[0, 0], 100.0)
        self.assertAlmostEqual(linear[0, 1], 100.0)

    def test_linear_db_roundtrip_precision(self):
        original_linear = np.array([[0.001, 0.05], [0.2, 5.0]], dtype=np.float32)
        db = linear_to_db(original_linear)
        recovered = db_to_linear(db)
        np.testing.assert_allclose(original_linear, recovered, rtol=1e-5)

    def test_lee_speckle_filter_reduces_variance_in_linear_domain(self):
        np.random.seed(42)
        true_linear_power = 0.05
        # Multiplicative noise with mean 1.0
        speckle = np.random.gamma(shape=4.4, scale=1.0 / 4.4, size=(60, 60))
        noisy_linear = (true_linear_power * speckle).astype(np.float32)
        var_before = float(np.var(noisy_linear))

        filtered = lee_speckle_filter(noisy_linear, window_size=5, num_looks=4.4, input_unit=SARUnit.LINEAR_POWER)
        var_after = float(np.var(filtered))

        # Speckle filter in linear domain significantly dampens speckle variance
        self.assertLess(var_after, var_before * 0.45)

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

    def test_spatial_alignment_and_overlap_rejection(self):
        transform1 = from_origin(85.0, 28.0, 0.001, 0.001)
        meta1 = RasterMetadata(
            crs="EPSG:4326", width=100, height=100,
            bounds=(85.0, 27.9, 85.1, 28.0),
            transform=transform1, nodata=-9999.0, resolution=(0.001, 0.001),
        )

        # Identical
        meta2 = RasterMetadata(
            crs="EPSG:4326", width=100, height=100,
            bounds=(85.0, 27.9, 85.1, 28.0),
            transform=transform1, nodata=-9999.0, resolution=(0.001, 0.001),
        )
        self.assertTrue(check_spatial_comparability(meta1, meta2))

        # Disjoint non-overlapping raster
        transform_disjoint = from_origin(87.0, 28.0, 0.001, 0.001)
        meta_disjoint = RasterMetadata(
            crs="EPSG:4326", width=100, height=100,
            bounds=(87.0, 27.9, 87.1, 28.0),
            transform=transform_disjoint, nodata=-9999.0, resolution=(0.001, 0.001),
        )
        with self.assertRaises(NonOverlappingRasterError):
            check_spatial_comparability(meta1, meta_disjoint)

        # CRS mismatch raises IncompatibleCRSError
        meta_utm = RasterMetadata(
            crs="EPSG:32645", width=100, height=100,
            bounds=(85.0, 27.9, 85.1, 28.0),
            transform=transform1, nodata=-9999.0, resolution=(10.0, 10.0),
        )
        with self.assertRaises(IncompatibleCRSError):
            check_spatial_comparability(meta1, meta_utm)


if __name__ == "__main__":
    unittest.main()
