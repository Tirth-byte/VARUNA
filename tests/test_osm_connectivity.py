"""Unit tests for OpenStreetMap road network connectivity and settlement isolation analysis."""

import unittest
from datetime import datetime
import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon

from varuna.osm.network import (
    RoadNetworkConnectivityAnalyzer,
    InfrastructureExposureSummary,
)


class TestOSMConnectivity(unittest.TestCase):
    def setUp(self):
        self.event_date = datetime(2026, 8, 26)
        self.pre_event_snapshot = datetime(2026, 8, 15)
        self.post_event_snapshot = datetime(2026, 8, 27)

    def test_post_event_osm_snapshot_rejected(self):
        # Strict temporal guard
        with self.assertRaises(ValueError) as ctx:
            RoadNetworkConnectivityAnalyzer(self.post_event_snapshot, self.event_date)
        self.assertIn("not strictly pre-event", str(ctx.exception))

    def test_network_isolation_simulation(self):
        analyzer = RoadNetworkConnectivityAnalyzer(self.pre_event_snapshot, self.event_date)

        # Build a synthetic road network:
        # Town (Node A: 85.0, 28.0) ---- Road 1 (Bridge) ---- Settlement (Node B: 85.1, 28.0)
        # Node B is a remote settlement with no other access road.
        # Town has a hospital.
        roads_gdf = gpd.GeoDataFrame([
            {
                "osm_id": 1,
                "highway": "primary",
                "bridge": True,
                "length_m": 1000.0,
                "geometry": LineString([(85.0, 28.0), (85.1, 28.0)]),
            }
        ], crs="EPSG:4326")

        settlements_gdf = gpd.GeoDataFrame([
            {
                "name": "District Hospital Town",
                "amenity": "hospital",
                "is_hospital": True,
                "geometry": Point(85.0, 28.0),
            },
            {
                "name": "Remote Mountain Village",
                "amenity": None,
                "is_hospital": False,
                "geometry": Point(85.1, 28.0),
            }
        ], crs="EPSG:4326")

        analyzer.build_graph_from_geodataframe(roads_gdf, settlements_gdf)

        # Flood polygon covering the bridge along the road: (85.04 to 85.06)
        flood_poly = Polygon([
            [85.04, 27.99],
            [85.06, 27.99],
            [85.06, 28.01],
            [85.04, 28.01],
            [85.04, 27.99],
        ])
        flood_gdf = gpd.GeoDataFrame([{"geometry": flood_poly}], crs="EPSG:4326")

        summary, exposed_roads = analyzer.analyze_flood_impact(flood_gdf)

        # Assertions
        self.assertEqual(summary.exposed_bridges_count, 1)
        self.assertEqual(summary.candidate_isolated_settlements_count, 1)
        self.assertIn("Remote Mountain Village", summary.candidate_isolated_settlements)
        self.assertIn("IMPORTANT SCIENTIFIC LIMITATION", summary.disclaimer)
        self.assertFalse(exposed_roads.empty)

    def test_alternative_unflooded_route_prevents_isolation(self):
        analyzer = RoadNetworkConnectivityAnalyzer(self.pre_event_snapshot, self.event_date)

        # Triangle network:
        # Town (A: 0,0) - Road 1 - Village (B: 1,0)
        # Town (A: 0,0) - Road 2 - Junction (C: 0,1) - Road 3 - Village (B: 1,0)
        roads_gdf = gpd.GeoDataFrame([
            {
                "osm_id": 1,
                "highway": "primary",
                "length_m": 1000.0,
                "geometry": LineString([(0.0, 0.0), (1.0, 0.0)]),
            },
            {
                "osm_id": 2,
                "highway": "secondary",
                "length_m": 1000.0,
                "geometry": LineString([(0.0, 0.0), (0.0, 1.0)]),
            },
            {
                "osm_id": 3,
                "highway": "secondary",
                "length_m": 1400.0,
                "geometry": LineString([(0.0, 1.0), (1.0, 0.0)]),
            },
        ], crs="EPSG:4326")

        settlements_gdf = gpd.GeoDataFrame([
            {"name": "Main Hospital", "is_hospital": True, "geometry": Point(0.0, 0.0)},
            {"name": "Redundant Access Village", "is_hospital": False, "geometry": Point(1.0, 0.0)},
        ], crs="EPSG:4326")

        analyzer.build_graph_from_geodataframe(roads_gdf, settlements_gdf)

        # Flood polygon covers only Road 1
        flood_poly = Polygon([
            [0.4, -0.1],
            [0.6, -0.1],
            [0.6, 0.1],
            [0.4, 0.1],
            [0.4, -0.1],
        ])
        flood_gdf = gpd.GeoDataFrame([{"geometry": flood_poly}], crs="EPSG:4326")

        summary, exposed_roads = analyzer.analyze_flood_impact(flood_gdf)

        # Road 1 is exposed, but Village is NOT isolated because path via Junction C remains intact
        self.assertEqual(len(exposed_roads), 1)
        self.assertEqual(summary.candidate_isolated_settlements_count, 0)


if __name__ == "__main__":
    unittest.main()
