"""Integration tests for VARUNA FastAPI endpoints."""

import unittest
from unittest.mock import patch
from datetime import datetime
from fastapi.testclient import TestClient

from varuna.api.main import app
from varuna.acquisition.cdse import DiscoveredRadarScene, ScenePairRecommendation


class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("rasterio", data["library_versions"])
        self.assertIn("networkx", data["library_versions"])

    def test_detection_baseline_endpoint(self):
        payload = {
            "pre_scene_id": "S1A_PRE",
            "post_scene_id": "S1A_POST",
            "crs": "EPSG:4326",
            "water_threshold_db": -3.5,
            "debris_threshold_db": 3.5,
            "pre_db_values": [
                [-10.0, -8.0],
                [-12.0, -18.0]
            ],
            "post_db_values": [
                [-10.0, -14.0],  # (0,1) drop by 6 dB -> candidate water
                [-7.0, -19.0]    # (1,0) rise by 5 dB -> candidate debris
            ],
            "bounds": [85.1, 27.8, 85.3, 28.0]
        }
        resp = self.client.post("/api/v1/detection/baseline", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        stats = data["summary_statistics"]
        self.assertEqual(stats["candidate_water_pixels"], 1)
        self.assertEqual(stats["candidate_debris_pixels"], 1)
        self.assertEqual(stats["permanent_water_pixels"], 1)

    def test_exposure_endpoint_rejects_post_event_osm(self):
        payload = {
            "event_date": "2026-08-26T00:00:00",
            "snapshot_date": "2026-08-28T00:00:00",  # Post event -> LEAKAGE
            "candidate_flood_geojson": {"type": "FeatureCollection", "features": []},
            "roads_geojson": {"type": "FeatureCollection", "features": []}
        }
        resp = self.client.post("/api/v1/analysis/exposure", json=payload)
        self.assertEqual(resp.status_code, 422)
        self.assertIn("not strictly pre-event", resp.json()["detail"])

    def test_exposure_endpoint_valid_run(self):
        payload = {
            "event_date": "2026-08-26T00:00:00",
            "snapshot_date": "2026-08-15T00:00:00",
            "candidate_flood_geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[85.04, 27.99], [85.06, 27.99], [85.06, 28.01], [85.04, 28.01], [85.04, 27.99]]]
                        },
                        "properties": {}
                    }
                ]
            },
            "roads_geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[85.0, 28.0], [85.1, 28.0]]
                        },
                        "properties": {
                            "osm_id": 101,
                            "highway": "primary",
                            "bridge": True,
                            "length_m": 1200.0
                        }
                    }
                ]
            },
            "settlements_geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [85.0, 28.0]},
                        "properties": {"name": "Central Hospital", "is_hospital": True}
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [85.1, 28.0]},
                        "properties": {"name": "Isolated Hamlet", "is_hospital": False}
                    }
                ]
            }
        }
        resp = self.client.post("/api/v1/analysis/exposure", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["exposed_bridges_count"], 1)
        self.assertEqual(data["candidate_isolated_settlements_count"], 1)
        self.assertIn("Isolated Hamlet", data["candidate_isolated_settlements"])
        self.assertIn("IMPORTANT SCIENTIFIC LIMITATION", data["disclaimer"])


if __name__ == "__main__":
    unittest.main()
