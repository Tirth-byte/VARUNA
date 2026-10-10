"""Unit tests for baseline change detection, threshold sensitivity, and vectorization."""

import unittest
import numpy as np
from rasterio.transform import from_origin

from varuna.detection.baseline import (
    LandCoverChangeClass,
    BaselineDetectionConfig,
    run_baseline_detection,
    compute_otsu_threshold,
)


class TestBaselineChangeDetection(unittest.TestCase):
    def setUp(self):
        self.transform = from_origin(85.1, 28.1, 0.001, 0.001)
        self.crs = "EPSG:4326"

    def test_detection_classification_logic(self):
        # 4x4 synthetic test grid
        # Pixel (0,0): No change (-10 dB pre, -10 dB post -> Delta = 0 dB)
        # Pixel (0,1): Water candidate (-8 dB pre, -14 dB post -> Delta = -6 dB <= -3.5 dB)
        # Pixel (1,0): Debris candidate (-12 dB pre, -7 dB post -> Delta = +5 dB >= +3.5 dB)
        # Pixel (1,1): Permanent water (-18 dB pre, -19 dB post)
        pre = np.array([
            [-10.0, -8.0],
            [-12.0, -18.0]
        ], dtype=np.float32)

        post = np.array([
            [-10.0, -14.0],
            [-7.0, -19.0]
        ], dtype=np.float32)

        res = run_baseline_detection(pre, post, self.transform, self.crs)
        mask = res.classification_mask

        self.assertEqual(mask[0, 0], LandCoverChangeClass.NO_SIGNIFICANT_CHANGE)
        self.assertEqual(mask[0, 1], LandCoverChangeClass.CANDIDATE_WATER_INUNDATION)
        self.assertEqual(mask[1, 0], LandCoverChangeClass.CANDIDATE_DEBRIS_OR_ROUGHENING)
        self.assertEqual(mask[1, 1], LandCoverChangeClass.PERMANENT_WATER)

    def test_terrain_shadow_flagging(self):
        pre = np.array([[-8.0]], dtype=np.float32)
        post = np.array([[-14.0]], dtype=np.float32)  # -6 dB drop
        steep_slopes = np.array([[32.0]], dtype=np.float32)  # 32 degree slope

        res = run_baseline_detection(
            pre, post, self.transform, self.crs,
            terrain_slope_degrees=steep_slopes,
            steep_slope_threshold=25.0
        )
        self.assertEqual(res.classification_mask[0, 0], LandCoverChangeClass.TERRAIN_SHADOW_SUSPECT)

    def test_adaptive_otsu_computation(self):
        # Bimodal distribution of negative drops: background (-1 dB) and water flood (-5 dB)
        np.random.seed(42)
        background = np.random.normal(-1.0, 0.4, 500)
        flood = np.random.normal(-5.0, 0.5, 200)
        drops = np.concatenate([background, flood])

        otsu_thresh = compute_otsu_threshold(drops)
        # Expected threshold separating -1.0 and -5.0 is around -3.0 dB
        self.assertTrue(-4.0 <= otsu_thresh <= -2.0)

    def test_vectorization_to_geodataframe(self):
        pre = np.full((10, 10), -8.0, dtype=np.float32)
        post = np.full((10, 10), -8.0, dtype=np.float32)
        # Put 4 flood pixels in corner
        post[0:2, 0:2] = -15.0

        res = run_baseline_detection(pre, post, self.transform, self.crs)
        gdf = res.to_geodataframe()

        self.assertFalse(gdf.empty)
        self.assertIn("geometry", gdf.columns)
        self.assertIn("class_name", gdf.columns)
        self.assertEqual(gdf.crs.to_string(), "EPSG:4326")

        stats = res.summary_statistics
        self.assertEqual(stats["candidate_water_pixels"], 4)
        self.assertGreater(stats["candidate_water_area_km2"], 0)


if __name__ == "__main__":
    unittest.main()
