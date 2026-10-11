"""Regression tests proving pipeline integrity: no unverified or unauthenticated scenario returns COMPLETED."""

import unittest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path
import tempfile
import json
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Polygon

from varuna.jobs.pipeline import (
    JobStatus,
    JobPipelineManager,
    ArtifactVerificationError,
    verify_analysis_artifacts,
)
from varuna.acquisition.cdse import DiscoveredRadarScene, ScenePairRecommendation


class TestPipelineIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.manager = JobPipelineManager(base_data_dir=self.base_dir)

        self.aoi = {
            "type": "Polygon",
            "coordinates": [[[85.1, 27.9], [85.3, 27.9], [85.3, 28.1], [85.1, 28.1], [85.1, 27.9]]]
        }
        self.event_date = datetime(2026, 8, 26)

        # Mock discovery recommendation
        self.dummy_pre = DiscoveredRadarScene(
            scene_id="S1D_IW_GRDH_PRE",
            acquired_at=datetime(2026, 8, 24, 0, 18, 44),
            relative_orbit=19,
            pass_direction="DESCENDING",
            polarization="VV&VH",
            source_url="https://example.org/pre",
            product_type="GRD",
            sensor_mode="IW",
            coverage_ratio=1.0,
            cdse_id="uuid-pre",
        )
        self.dummy_post = DiscoveredRadarScene(
            scene_id="S1D_IW_GRDH_POST",
            acquired_at=datetime(2026, 9, 5, 0, 18, 44),
            relative_orbit=19,
            pass_direction="DESCENDING",
            polarization="VV&VH",
            source_url="https://example.org/post",
            product_type="GRD",
            sensor_mode="IW",
            coverage_ratio=1.0,
            cdse_id="uuid-post",
        )
        self.mock_rec = ScenePairRecommendation(
            before_scene=self.dummy_pre,
            after_scene=self.dummy_post,
            event_date=self.event_date,
            orbit_direction="DESCENDING",
            relative_orbit=19,
            temporal_baseline_days=12.0,
            scientific_rationale="Matching Orbit 19 DESCENDING",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_credentials_halts_in_awaiting_authentication_not_completed(self):
        """CRITICAL: Without credentials or local rasters, job MUST halt in AWAITING_AUTHENTICATION, NEVER COMPLETED."""
        job = self.manager.create_job(
            aoi_geojson=self.aoi,
            event_date=self.event_date,
        )

        with patch("varuna.jobs.pipeline.CDSEDiscoveryService.discover_compatible_pair", return_value=self.mock_rec):
            with patch("varuna.acquisition.download.CDSEDownloader.has_credentials", return_value=False):
                executed_job = self.manager.execute_job(job.job_id)

                # MUST NOT BE COMPLETED
                self.assertNotEqual(executed_job.status, JobStatus.COMPLETED)
                self.assertEqual(executed_job.status, JobStatus.AWAITING_AUTHENTICATION)
                self.assertIn("Authentication required", executed_job.error_message)
                self.assertNotIn("geotiff_change_mask", executed_job.artifacts)

    def test_missing_raster_files_fails_pipeline(self):
        """When specified raster paths do not exist, job must FAIL closed."""
        job = self.manager.create_job(
            aoi_geojson=self.aoi,
            event_date=self.event_date,
            pre_raster_path=self.base_dir / "non_existent_pre.tif",
            post_raster_path=self.base_dir / "non_existent_post.tif",
        )

        with patch("varuna.jobs.pipeline.CDSEDiscoveryService.discover_compatible_pair", return_value=self.mock_rec):
            with patch("varuna.acquisition.download.CDSEDownloader.has_credentials", return_value=False):
                executed_job = self.manager.execute_job(job.job_id)
                self.assertNotEqual(executed_job.status, JobStatus.COMPLETED)
                self.assertEqual(executed_job.status, JobStatus.AWAITING_AUTHENTICATION)

    def test_failed_processing_scenario_halts_in_failed_not_completed(self):
        """When processing encounters an error (e.g. corrupt raster file), job status must be FAILED, never COMPLETED."""
        corrupt_pre = self.base_dir / "corrupt_pre.tif"
        corrupt_pre.write_text("not a valid geotiff")
        corrupt_post = self.base_dir / "corrupt_post.tif"
        corrupt_post.write_text("not a valid geotiff")

        job = self.manager.create_job(
            aoi_geojson=self.aoi,
            event_date=self.event_date,
            pre_raster_path=corrupt_pre,
            post_raster_path=corrupt_post,
        )

        with patch("varuna.jobs.pipeline.CDSEDiscoveryService.discover_compatible_pair", return_value=self.mock_rec):
            with self.assertRaises(Exception):
                self.manager.execute_job(job.job_id)

            failed_job = self.manager.get_job(job.job_id)
            self.assertNotEqual(failed_job.status, JobStatus.COMPLETED)
            self.assertEqual(failed_job.status, JobStatus.FAILED)
            self.assertIsNotNone(failed_job.error_message)

    def test_empty_or_corrupt_artifacts_fail_verification(self):
        """Artifact verification must reject missing, empty, or corrupt GeoTIFF files."""
        empty_tif = self.base_dir / "empty.tif"
        empty_tif.touch()

        fake_geojson = self.base_dir / "test.geojson"
        with open(fake_geojson, "w") as f:
            json.dump({"type": "FeatureCollection", "features": []}, f)

        prov = self.base_dir / "prov.json"
        with open(prov, "w") as f:
            json.dump({"test": True}, f)

        artifacts = {
            "geotiff_change_mask": str(empty_tif),
            "geojson_candidates": str(fake_geojson),
            "provenance": str(prov),
        }
        with self.assertRaises(ArtifactVerificationError):
            verify_analysis_artifacts(artifacts)

    def test_pipeline_executes_to_completed_with_valid_rasters_and_verifies_artifacts(self):
        """When valid georeferenced rasters exist, pipeline completes and produces readable artifacts."""
        # Create genuine georeferenced GeoTIFFs in temp directory
        transform = from_origin(85.1, 28.1, 0.001, 0.001)
        profile = {
            "driver": "GTiff",
            "height": 50,
            "width": 50,
            "count": 1,
            "dtype": rasterio.float32,
            "crs": "EPSG:4326",
            "transform": transform,
            "nodata": -9999.0,
        }

        pre_path = self.base_dir / "real_pre.tif"
        post_path = self.base_dir / "real_post.tif"

        # Pre: -10 dB background
        arr_pre = np.full((50, 50), -10.0, dtype=np.float32)
        # Post: -16 dB flood drop in top-left quadrant (-6 dB change)
        arr_post = np.full((50, 50), -10.0, dtype=np.float32)
        arr_post[0:15, 0:15] = -16.0

        with rasterio.open(pre_path, "w", **profile) as dst:
            dst.write(arr_pre, 1)
            dst.update_tags(SAR_UNIT="DECIBELS_DB")
        with rasterio.open(post_path, "w", **profile) as dst:
            dst.write(arr_post, 1)
            dst.update_tags(SAR_UNIT="DECIBELS_DB")

        job = self.manager.create_job(
            aoi_geojson=self.aoi,
            event_date=self.event_date,
            pre_raster_path=pre_path,
            post_raster_path=post_path,
        )

        with patch("varuna.jobs.pipeline.CDSEDiscoveryService.discover_compatible_pair", return_value=self.mock_rec):
            completed_job = self.manager.execute_job(job.job_id)

            # ONLY with valid rasters and verified artifacts may it be COMPLETED
            self.assertEqual(completed_job.status, JobStatus.COMPLETED)
            self.assertEqual(completed_job.progress_percent, 100)
            self.assertIn("geotiff_change_mask", completed_job.artifacts)
            self.assertIn("geotiff_valid_mask", completed_job.artifacts)
            self.assertIn("geojson_candidates", completed_job.artifacts)
            self.assertIn("provenance", completed_job.artifacts)

            # Verify exported GeoTIFF physically
            gt_path = Path(completed_job.artifacts["geotiff_change_mask"])
            self.assertTrue(gt_path.exists())
            self.assertGreater(gt_path.stat().st_size, 0)
            with rasterio.open(gt_path) as src:
                self.assertEqual(src.count, 3)
                self.assertEqual(src.crs.to_string(), "EPSG:4326")
                self.assertEqual(src.width, 50)
                self.assertEqual(src.height, 50)
                # Read band 2 (Classification mask)
                mask = src.read(2)
                # Top left quadrant should be Candidate Water (class 2)
                self.assertEqual(mask[5, 5], 2)

            # Verify exported Valid Data Mask GeoTIFF physically
            vm_path = Path(completed_job.artifacts["geotiff_valid_mask"])
            self.assertTrue(vm_path.exists())
            self.assertGreater(vm_path.stat().st_size, 0)
            with rasterio.open(vm_path) as src:
                self.assertEqual(src.count, 1)
                self.assertEqual(src.crs.to_string(), "EPSG:4326")
                self.assertEqual(src.width, 50)
                self.assertEqual(src.height, 50)
                vmask = src.read(1)
                self.assertEqual(vmask[5, 5], 1)

            # Verify exported GeoJSON physically
            gj_path = Path(completed_job.artifacts["geojson_candidates"])
            self.assertTrue(gj_path.exists())
            with open(gj_path) as f:
                gj_data = json.load(f)
                self.assertGreater(len(gj_data["features"]), 0)

            # Verify provenance file physically
            prov_path = Path(completed_job.artifacts["provenance"])
            self.assertTrue(prov_path.exists())
            with open(prov_path) as f:
                p_data = json.load(f)
                self.assertEqual(p_data["job_id"], completed_job.job_id)
                self.assertIn("summary_statistics", p_data)


if __name__ == "__main__":
    unittest.main()
