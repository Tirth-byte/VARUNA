"""Unit and integration tests for Sentinel-1 CDSE discovery and orbit validation."""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import httpx
from shapely.geometry import Polygon

from varuna.acquisition.cdse import (
    CDSEDiscoveryService,
    DiscoveredRadarScene,
    IncompatibleScenePairError,
)
from varuna.acquisition.download import (
    CDSEDownloader,
    AuthenticationRequiredError,
)
from varuna.contracts import validate_pair, validate_osm_snapshot


class TestCDSEDiscovery(unittest.TestCase):
    def setUp(self):
        # Trishuli Nepal approximate bounding box
        self.trishuli_aoi = Polygon([
            [85.10, 27.80],
            [85.35, 27.80],
            [85.35, 28.05],
            [85.10, 28.05],
            [85.10, 27.80],
        ])
        self.event_date = datetime(2026, 8, 26, 12, 0, 0)

    def _create_mock_odata_item(self, name, start_iso, rel_orbit, direction="ASCENDING", pol="VV&VH"):
        return {
            "Id": f"uuid-{name}",
            "Name": name,
            "ContentDate": {"Start": start_iso, "End": start_iso},
            "GeoFootprint": {
                "type": "Polygon",
                "coordinates": [[[84.5, 27.5], [86.0, 27.5], [86.0, 28.5], [84.5, 28.5], [84.5, 27.5]]]
            },
            "Attributes": [
                {"Name": "relativeOrbitNumber", "Value": rel_orbit},
                {"Name": "orbitDirection", "Value": direction},
                {"Name": "polarisationChannels", "Value": pol},
                {"Name": "sensorOperationalMode", "Value": "IW"},
                {"Name": "productType", "Value": "GRD"},
            ]
        }

    def test_discover_compatible_pair_success(self):
        service = CDSEDiscoveryService()
        mock_pre = self._create_mock_odata_item("S1A_IW_GRDH_PRE", "2026-08-20T00:15:00Z", 42, "ASCENDING")
        mock_post = self._create_mock_odata_item("S1A_IW_GRDH_POST", "2026-09-01T00:15:00Z", 42, "ASCENDING")

        with patch.object(service, "query_scenes") as mock_query:
            pre_scene = DiscoveredRadarScene.from_odata_item(mock_pre, self.trishuli_aoi)
            post_scene = DiscoveredRadarScene.from_odata_item(mock_post, self.trishuli_aoi)
            mock_query.return_value = [pre_scene, post_scene]

            rec = service.discover_compatible_pair(self.trishuli_aoi, self.event_date)
            self.assertEqual(rec.relative_orbit, 42)
            self.assertEqual(rec.orbit_direction, "ASCENDING")
            self.assertEqual(rec.before_scene.scene_id, "S1A_IW_GRDH_PRE")
            self.assertEqual(rec.after_scene.scene_id, "S1A_IW_GRDH_POST")
            self.assertGreater(rec.before_scene.coverage_ratio, 0.9)

    def test_incompatible_relative_orbits_rejected(self):
        service = CDSEDiscoveryService()
        # Orbit 42 vs Orbit 115
        mock_pre = self._create_mock_odata_item("S1A_PRE_42", "2026-08-20T00:00:00Z", 42, "ASCENDING")
        mock_post = self._create_mock_odata_item("S1A_POST_115", "2026-08-28T00:00:00Z", 115, "ASCENDING")

        with patch.object(service, "query_scenes") as mock_query:
            mock_query.return_value = [
                DiscoveredRadarScene.from_odata_item(mock_pre, self.trishuli_aoi),
                DiscoveredRadarScene.from_odata_item(mock_post, self.trishuli_aoi),
            ]

            with self.assertRaises(IncompatibleScenePairError) as ctx:
                service.discover_compatible_pair(self.trishuli_aoi, self.event_date)
            self.assertIn("Incompatible radar geometry", str(ctx.exception))
            self.assertIn("relative orbit", str(ctx.exception))

    def test_incompatible_pass_directions_rejected(self):
        service = CDSEDiscoveryService()
        mock_pre = self._create_mock_odata_item("S1A_PRE_ASC", "2026-08-20T00:00:00Z", 42, "ASCENDING")
        mock_post = self._create_mock_odata_item("S1A_POST_DESC", "2026-08-28T00:00:00Z", 42, "DESCENDING")

        with patch.object(service, "query_scenes") as mock_query:
            mock_query.return_value = [
                DiscoveredRadarScene.from_odata_item(mock_pre, self.trishuli_aoi),
                DiscoveredRadarScene.from_odata_item(mock_post, self.trishuli_aoi),
            ]

            with self.assertRaises(IncompatibleScenePairError):
                service.discover_compatible_pair(self.trishuli_aoi, self.event_date)

    def test_downloader_requires_credentials(self):
        downloader = CDSEDownloader(username=None, password=None, client_id=None, client_secret=None)
        self.assertFalse(downloader.has_credentials())
        with self.assertRaises(AuthenticationRequiredError):
            downloader.acquire_token()

    def test_missing_metadata_raises_error(self):
        bad_item = {
            "Id": "uuid-bad",
            "Name": "S1A_BAD",
            "ContentDate": {"Start": "2026-08-20T00:00:00Z"},
            "Attributes": [
                # Missing relativeOrbitNumber and orbitDirection!
                {"Name": "sensorOperationalMode", "Value": "IW"},
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            DiscoveredRadarScene.from_odata_item(bad_item)
        self.assertIn("Missing required attribute", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
