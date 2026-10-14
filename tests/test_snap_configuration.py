"""Unit and Regression Tests for ESA SNAP Configuration, DEM Provenance, and Secure Authentication.

Verifies:
1. Discovery and validation of local ESA SNAP GPT executable via SNAP_GPT_PATH.
2. Verification of required operators (Apply-Orbit-File, Calibration, Speckle-Filter,
   Terrain-Correction, Terrain-Mask, ThermalNoiseRemoval).
3. Range-Doppler Terrain Correction XML graph structure, including DEM provenance and
   terrain layover/shadow masking.
4. Mandatory Range-Doppler Terrain Correction enforcement for research-grade Sentinel-1 processing.
5. Secure credential verification preventing secret leakage.
"""

import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

import httpx

from varuna.acquisition.download import CDSEDownloader, AuthenticationRequiredError
from varuna.preprocessing.sentinel1 import (
    SNAPGraphProcessor,
    AuthenticSentinel1Processor,
    Sentinel1ProductInspector,
    TerrainCorrectionUnavailableError,
)


class TestSNAPConfiguration(unittest.TestCase):
    """Test suite for ESA SNAP GPT discovery, operators, DEM provenance, and security."""

    def test_snap_gpt_executable_discovery(self):
        """Verify discovery of local ESA SNAP GPT executable."""
        gpt_path = SNAPGraphProcessor.get_gpt_path()
        self.assertIsNotNone(gpt_path, "SNAP GPT executable should be discovered on this system")
        self.assertTrue(gpt_path.exists())
        self.assertTrue(os.access(gpt_path, os.X_OK))

    def test_required_operators_available(self):
        """Verify all 6 required radar operators are present in the local SNAP installation."""
        val = SNAPGraphProcessor.validate_installation()
        self.assertTrue(val["discovered"])
        self.assertTrue(val["valid"])
        self.assertEqual(val["missing_operators"], [])

        expected_operators = [
            "Apply-Orbit-File",
            "Calibration",
            "Speckle-Filter",
            "Terrain-Correction",
            "Terrain-Mask",
            "ThermalNoiseRemoval",
        ]
        for op in expected_operators:
            self.assertIn(op, val["available_operators"], f"Required operator '{op}' missing from SNAP")

    def test_snap_graph_xml_parameters_and_dem_provenance(self):
        """Verify generated SNAP graph XML includes DEM source and layover/shadow mask."""
        xml_str = SNAPGraphProcessor.build_graph_xml(
            safe_path=Path("/tmp/test.SAFE"),
            output_geotiff_path=Path("/tmp/out.tif"),
            polarization="VV",
            dem_source="Copernicus 30m Global DEM",
            pixel_spacing_m=10.0,
            enable_layover_shadow_mask=True,
        )

        self.assertIn("<operator>Terrain-Correction</operator>", xml_str)
        self.assertIn("<demName>Copernicus 30m Global DEM</demName>", xml_str)
        self.assertIn("<saveLayoverShadowMask>true</saveLayoverShadowMask>", xml_str)
        self.assertIn("<operator>Apply-Orbit-File</operator>", xml_str)
        self.assertIn("<operator>ThermalNoiseRemoval</operator>", xml_str)
        self.assertIn("<operator>Calibration</operator>", xml_str)

    def test_research_grade_terrain_correction_mandatory_by_default(self):
        """Verify AuthenticSentinel1Processor defaults to require_range_doppler=True."""
        import inspect
        sig = inspect.signature(AuthenticSentinel1Processor.process_sentinel1_product)
        self.assertIn("require_range_doppler", sig.parameters)
        self.assertTrue(sig.parameters["require_range_doppler"].default)

    def test_terrain_correction_fails_closed_when_snap_unavailable(self):
        """Verify fail-closed behavior when SNAP is unavailable in research-grade mode."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            mock_meta = MagicMock()
            mock_meta.polarizations = ["VV"]
            mock_meta.product_name = "MOCK_S1"

            with patch.object(Sentinel1ProductInspector, "inspect", return_value=(mock_meta, tmp_path / "mock.SAFE")):
                with patch.object(SNAPGraphProcessor, "is_snap_available", return_value=False):
                    with self.assertRaises(TerrainCorrectionUnavailableError):
                        AuthenticSentinel1Processor.process_sentinel1_product(
                            product_path=tmp_path / "mock.SAFE",
                            output_calibrated_path=tmp_path / "mock.tif",
                            polarization="VV",
                            require_range_doppler=True,
                        )

    def test_secure_credential_verification_masks_secrets(self):
        """Verify credential verification never leaks secrets or raw passwords."""
        downloader = CDSEDownloader(
            username="sensitive_user@domain.com",
            password="SuperSecretPassword123!",
        )

        # Mock 401 response from Keycloak
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("httpx.Client.post", side_effect=httpx.HTTPStatusError("401", request=MagicMock(), response=mock_resp)):
            result = downloader.verify_credentials_securely()

            self.assertTrue(result["configured"])
            self.assertFalse(result["authenticated"])
            self.assertEqual(result["status"], "UNAUTHORIZED")
            self.assertEqual(result["identity_masked"], "se***@domain.com")

            # Check that sensitive secret is not anywhere in the result
            result_str = str(result)
            self.assertNotIn("SuperSecretPassword123!", result_str)
            self.assertNotIn("sensitive_user", result_str)

    def test_unconfigured_credentials_reported_safely(self):
        """Verify unconfigured downloader reports cleanly."""
        with patch.dict(os.environ, {"CDSE_USERNAME": "", "CDSE_PASSWORD": "", "CDSE_CLIENT_SECRET": ""}, clear=True):
            downloader = CDSEDownloader(username=None, password=None, client_id="cdse-public", client_secret=None)
            result = downloader.verify_credentials_securely()

            self.assertFalse(result["configured"])
            self.assertFalse(result["authenticated"])
            self.assertEqual(result["status"], "NOT_CONFIGURED")


if __name__ == "__main__":
    unittest.main()
