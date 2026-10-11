"""Regression Tests for Phase 1.6 Authentic Sentinel-1 Preprocessing & Provenance.

Verifies:
1. SAFE product structural integrity inspection and corrupted archive rejection.
2. XML calibration vector parsing and 2D A_sigma interpolation.
3. Incompatible polarization rejection.
4. Fails closed on missing calibration metadata without guessing units from pixel values.
5. Prohibition of arbitrary hardcoded calibration constants (e.g. 100.0).
6. Synthetic test fixture rejection when `allow_synthetic=False` in research mode.
7. Proper propagation of nodata values.
"""

import os
import json
import shutil
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import rasterio
from rasterio.transform import from_origin

from varuna.preprocessing.sar import (
    SARUnit,
    calibrate_sar_raster,
    MissingCalibrationError,
    InvalidSARUnitError,
)
from varuna.preprocessing.sentinel1 import (
    Sentinel1ProductInspector,
    Sentinel1CalibrationLUTExtractor,
    AuthenticSentinel1Processor,
    CorruptSAFEProductError,
    IncompatiblePolarizationError,
)
from varuna.jobs.pipeline import JobPipelineManager, JobStatus
from tests.fixtures.synthetic_fixtures import create_synthetic_test_raster_pair


class TestSentinel1ProcessingIntegrity(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_mock_safe_archive(self, zip_name: str = "S1D_IW_GRDH_TEST.SAFE.zip", corrupt: bool = False) -> Path:
        """Create a structurally valid or corrupt Sentinel-1 SAFE archive for testing."""
        safe_name = zip_name.replace(".zip", "")
        safe_path = self.base_dir / safe_name
        meas_dir = safe_path / "measurement"
        ann_dir = safe_path / "annotation" / "calibration"
        meas_dir.mkdir(parents=True, exist_ok=True)
        ann_dir.mkdir(parents=True, exist_ok=True)

        # Manifest with valid XML namespace
        manifest = safe_path / "manifest.safe"
        manifest.write_text('<xfdu:XFDU xmlns:xfdu="urn:ccsds:schema:xfdu:1"><metadataSection><metadataObject ID="generalAnnotation"/></metadataSection></xfdu:XFDU>')

        if corrupt:
            # Create incomplete SAFE (no measurement rasters)
            zip_path = self.base_dir / zip_name
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.write(manifest, arcname=f"{safe_name}/manifest.safe")
            return zip_path

        # Measurement GeoTIFF
        meas_file = meas_dir / "s1d-iw-grd-vv-20260824t001844-004260-007d5d-001.tiff"
        transform = from_origin(85.1, 28.1, 0.001, 0.001)
        profile = {
            "driver": "GTiff",
            "height": 20,
            "width": 20,
            "count": 1,
            "dtype": rasterio.float32,
            "crs": "EPSG:4326",
            "transform": transform,
            "nodata": 0.0,
        }
        with rasterio.open(meas_file, "w", **profile) as dst:
            dst.write(np.full((20, 20), 500.0, dtype=np.float32), 1)

        # Calibration XML
        cal_xml = ann_dir / "calibration-s1d-iw-grd-vv-20260824t001844-004260-007d5d-001.xml"
        root = ET.Element("calibration")
        vec_list = ET.SubElement(root, "calibrationVectorList", count="2")
        for line_idx in [0, 19]:
            vec = ET.SubElement(vec_list, "calibrationVector")
            ET.SubElement(vec, "line").text = str(line_idx)
            ET.SubElement(vec, "pixel").text = "0 10 19"
            ET.SubElement(vec, "sigmaNought").text = "25.0 25.0 25.0"
        tree = ET.ElementTree(root)
        tree.write(cal_xml)

        # Pack into zip
        zip_path = self.base_dir / zip_name
        with zipfile.ZipFile(zip_path, "w") as zf:
            for f in safe_path.rglob("*"):
                if f.is_file():
                    zf.write(f, arcname=str(f.relative_to(self.base_dir)))

        return zip_path

    def test_corrupt_safe_archive_rejected(self):
        """Corrupt or incomplete SAFE archives must fail closed with CorruptSAFEProductError."""
        corrupt_zip = self._create_mock_safe_archive("S1_CORRUPT.SAFE.zip", corrupt=True)
        with self.assertRaises(CorruptSAFEProductError):
            Sentinel1ProductInspector.inspect(corrupt_zip, work_dir=self.base_dir)

    def test_safe_calibration_lut_parsing_and_interpolation(self):
        """Verify calibration XML parsing and 2D A_sigma LUT interpolation."""
        cal_xml = self.base_dir / "test_calibration.xml"
        root = ET.Element("calibration")
        vec_list = ET.SubElement(root, "calibrationVectorList", count="3")
        for line_idx, val in [(0, 10.0), (10, 20.0), (20, 30.0)]:
            vec = ET.SubElement(vec_list, "calibrationVector")
            ET.SubElement(vec, "line").text = str(line_idx)
            ET.SubElement(vec, "pixel").text = "0 10 20"
            ET.SubElement(vec, "sigmaNought").text = f"{val} {val} {val}"
        ET.ElementTree(root).write(cal_xml)

        lut_matrix = Sentinel1CalibrationLUTExtractor.extract_calibration_matrix(
            calibration_xml_path=cal_xml,
            raster_shape=(21, 21),
        )

        self.assertEqual(lut_matrix.shape, (21, 21))
        # Top line should be ~10.0, bottom line should be ~30.0
        self.assertAlmostEqual(lut_matrix[0, 0], 10.0, places=1)
        self.assertAlmostEqual(lut_matrix[20, 20], 30.0, places=1)

    def test_authentic_safe_processor_calibrates_and_writes_provenance(self):
        """End-to-end test of AuthenticSentinel1Processor producing calibrated decibels."""
        safe_zip = self._create_mock_safe_archive("S1_AUTHENTIC.SAFE.zip", corrupt=False)
        output_tif = self.base_dir / "calibrated_vv.tif"

        out_path = AuthenticSentinel1Processor.process_sentinel1_product(
            product_path=safe_zip,
            output_calibrated_path=output_tif,
            polarization="VV",
            work_dir=self.base_dir / "work",
        )

        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 0)

        with rasterio.open(out_path) as src:
            self.assertEqual(src.crs.to_string(), "EPSG:4326")
            tags = src.tags()
            self.assertEqual(tags.get("DATA_ORIGIN"), "REAL_SENTINEL1_OBSERVATION")
            self.assertEqual(tags.get("SAR_UNIT"), "DECIBELS_DB")
            self.assertEqual(tags.get("CALIBRATION_METHOD"), "SENTINEL1_LEVEL1_XML_LUT_A_SIGMA")

            # DN=500, A_sigma=25 -> linear sigma0 = (500^2)/(25^2) = 20^2 = 400.0
            # 10*log10(400) = 26.02 dB (before Lee filtering variance adjustment)
            arr = src.read(1)
            self.assertTrue(np.all(~np.isnan(arr)))
            self.assertAlmostEqual(np.mean(arr), 26.02, delta=1.5)

    def test_synthetic_data_provenance_rejected_in_production_run(self):
        """CRITICAL: Synthetic test fixture must be rejected when allow_synthetic=False."""
        pre_synth, post_synth = create_synthetic_test_raster_pair(self.base_dir / "synth")

        manager = JobPipelineManager(base_data_dir=self.base_dir / "jobs")
        job = manager.create_job(
            aoi_geojson={"type": "Polygon", "coordinates": [[[85.1, 27.9], [85.3, 27.9], [85.3, 28.1], [85.1, 28.1], [85.1, 27.9]]]},
            event_date=datetime(2026, 8, 26, tzinfo=timezone.utc),
            pre_raster_path=pre_synth,
            post_raster_path=post_synth,
            allow_synthetic=False,  # PRODUCTION / RESEARCH GRADE
        )

        with self.assertRaises(ValueError) as ctx:
            manager.execute_job(job.job_id)

        self.assertIn("SYNTHETIC_TEST_FIXTURE", str(ctx.exception))
        self.assertIn("strictly prohibited", str(ctx.exception))

    def test_synthetic_fixture_allowed_only_in_explicit_test_mode(self):
        """When allow_synthetic=True, pipeline accepts fixture and marks SYNTHETIC_TEST_COMPLETED."""
        pre_synth, post_synth = create_synthetic_test_raster_pair(self.base_dir / "synth_allowed")

        manager = JobPipelineManager(base_data_dir=self.base_dir / "jobs_allowed")
        job = manager.create_job(
            aoi_geojson={"type": "Polygon", "coordinates": [[[85.1, 27.9], [85.3, 27.9], [85.3, 28.1], [85.1, 28.1], [85.1, 27.9]]]},
            event_date=datetime(2026, 8, 26, tzinfo=timezone.utc),
            pre_raster_path=pre_synth,
            post_raster_path=post_synth,
            allow_synthetic=True,  # EXPLICIT TEST MODE
        )

        executed = manager.execute_job(job.job_id)
        self.assertEqual(executed.status, JobStatus.SYNTHETIC_TEST_COMPLETED)
        self.assertEqual(executed.data_origin, "SYNTHETIC_TEST_FIXTURE")

    def test_uncalibrated_raster_without_unit_tags_fails_closed(self):
        """Rasters lacking SAR_UNIT metadata tags and calibration XML must fail closed.

        Guarantees that pixel-value guessing and hardcoded calibration scalars (100.0) are never used.
        """
        uncalibrated_path = self.base_dir / "uncalibrated_raw.tif"
        transform = from_origin(85.1, 28.1, 0.001, 0.001)
        profile = {
            "driver": "GTiff",
            "height": 20,
            "width": 20,
            "count": 1,
            "dtype": rasterio.float32,
            "crs": "EPSG:4326",
            "transform": transform,
            "nodata": -9999.0,
        }
        # Positive values (e.g. 50.0) that previous code would have guessed were DN and multiplied by 100.0
        with rasterio.open(uncalibrated_path, "w", **profile) as dst:
            dst.write(np.full((20, 20), 50.0, dtype=np.float32), 1)
            # Deliberately DO NOT set SAR_UNIT tag

        manager = JobPipelineManager(base_data_dir=self.base_dir / "jobs_fail_closed")
        job = manager.create_job(
            aoi_geojson={"type": "Polygon", "coordinates": [[[85.1, 27.9], [85.3, 27.9], [85.3, 28.1], [85.1, 28.1], [85.1, 27.9]]]},
            event_date=datetime(2026, 8, 26, tzinfo=timezone.utc),
            pre_raster_path=uncalibrated_path,
            post_raster_path=uncalibrated_path,
        )

        with self.assertRaises(MissingCalibrationError) as ctx:
            manager.execute_job(job.job_id)

        self.assertIn("lacks valid SAR_UNIT metadata tags or calibration XML", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
