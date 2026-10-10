"""Integration tests for VARUNA FastAPI endpoints including job pipeline and benchmarks."""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from shapely.geometry import Polygon

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
        self.assertIn("SCIENTIFIC ASSUMPTION & LIMITATION", data["disclaimer"])

    def test_validation_benchmark_endpoint(self):
        payload = {
            "predicted_binary_mask": [[1, 0], [0, 1]],
            "reference_binary_mask": [[1, 0], [1, 1]],
            "reference_dataset_name": "Copernicus EMS EMSR927 Rapid Mapping",
            "event_date": "2026-08-26T00:00:00",
            "pixel_area_m2": 100.0
        }
        resp = self.client.post("/api/v1/validation/benchmark", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["reference_activation_code"], "EMSR927")
        self.assertAlmostEqual(data["precision_score"], 1.0)
        self.assertAlmostEqual(data["recall_score"], 2.0 / 3.0)
        self.assertAlmostEqual(data["iou_score"], 2.0 / 3.0)

    def test_jobs_endpoint_creation_and_status(self):
        payload = {
            "aoi": {
                "type": "Polygon",
                "coordinates": [[[85.1, 27.8], [85.3, 27.8], [85.3, 28.0], [85.1, 28.0], [85.1, 27.8]]]
            },
            "event_date": "2026-08-26T00:00:00",
            "pre_window_days": 30,
            "post_window_days": 15
        }
        # Mock CDSE to test deterministic job pipeline
        dummy_pre = DiscoveredRadarScene(
            scene_id="S1D_IW_GRDH_PRE",
            acquired_at=datetime(2026, 8, 16, 12, 21, 41),
            relative_orbit=85,
            pass_direction="ASCENDING",
            polarization="VV&VH",
            source_url="https://example.org/pre",
            product_type="GRD",
            sensor_mode="IW",
            coverage_ratio=0.85,
            cdse_id="uuid-pre",
        )
        dummy_post = DiscoveredRadarScene(
            scene_id="S1D_IW_GRDH_POST",
            acquired_at=datetime(2026, 8, 28, 12, 21, 41),
            relative_orbit=85,
            pass_direction="ASCENDING",
            polarization="VV&VH",
            source_url="https://example.org/post",
            product_type="GRD",
            sensor_mode="IW",
            coverage_ratio=0.85,
            cdse_id="uuid-post",
        )
        dummy_rec = ScenePairRecommendation(
            before_scene=dummy_pre,
            after_scene=dummy_post,
            event_date=datetime(2026, 8, 26),
            orbit_direction="ASCENDING",
            relative_orbit=85,
            temporal_baseline_days=12.0,
            scientific_rationale="Matching Orbit 85 ASCENDING",
        )

        with patch("varuna.jobs.pipeline.CDSEDiscoveryService.discover_compatible_pair", return_value=dummy_rec):
            resp = self.client.post("/api/v1/jobs", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            job_id = data["job_id"]
            self.assertIn("job_id", data)
            self.assertEqual(data["status"], "COMPLETED")
            self.assertIn("pre_scene_id", data["selected_scenes"])
            self.assertEqual(data["selected_scenes"]["relative_orbit"], 85)

            # Check status endpoint
            resp_status = self.client.get(f"/api/v1/jobs/{job_id}")
            self.assertEqual(resp_status.status_code, 200)
            status_data = resp_status.json()
            self.assertEqual(status_data["job_id"], job_id)


if __name__ == "__main__":
    unittest.main()
