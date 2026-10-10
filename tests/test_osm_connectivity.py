"""Adversarial tests for road network topology, junction noding, layers, and geodesic metrics."""

import unittest
from datetime import datetime
import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon

from varuna.osm.network import (
    RoadNetworkConnectivityAnalyzer,
    InfrastructureState,
    WGS84_GEOD,
)


class TestOSMTopologyAndConnectivity(unittest.TestCase):
    def setUp(self):
        self.event_date = datetime(2026, 8, 26)
        self.pre_event_snapshot = datetime(2026, 8, 15)

    def test_t_junction_properly_noded(self):
        """Road B terminates along the interior of Road A (T-Junction).

        Both must connect at the shared vertex node.
        """
        analyzer = RoadNetworkConnectivityAnalyzer(self.pre_event_snapshot, self.event_date)

        # Road A: (85.0, 28.0) -> (85.1, 28.0) -> (85.2, 28.0)
        # Road B: (85.1, 28.0) -> (85.1, 28.1) meets Road A at the middle coordinate (85.1, 28.0)
        roads_gdf = gpd.GeoDataFrame([
            {"osm_id": 1, "highway": "primary", "geometry": LineString([(85.0, 28.0), (85.1, 28.0), (85.2, 28.0)])},
            {"osm_id": 2, "highway": "secondary", "geometry": LineString([(85.1, 28.0), (85.1, 28.1)])},
        ], crs="EPSG:4326")

        analyzer.build_graph_from_geodataframe(roads_gdf)
        graph = analyzer.graph

        # Road A must be split into two subsegments around the T-junction (85.1, 28.0)
        # Total edges in MultiGraph should be 3 (2 for Road A + 1 for Road B)
        self.assertEqual(len(graph.edges), 3)

        # Check path from Road B tip (85.1, 28.1) to Road A end (85.2, 28.0)
        node_b_tip = analyzer._node_key(85.1, 28.1)
        node_a_end = analyzer._node_key(85.2, 28.0)
        import networkx as nx
        self.assertTrue(nx.has_path(graph, node_b_tip, node_a_end))

    def test_overpass_bridge_does_not_falsely_connect_underpass(self):
        """A bridge at layer=1 passing over a highway at layer=0 must NOT form a false junction."""
        analyzer = RoadNetworkConnectivityAnalyzer(self.pre_event_snapshot, self.event_date)

        # Surface road (layer=0): West-East (85.0, 28.0) to (85.2, 28.0) with vertex at (85.1, 28.0)
        # Bridge overpass (layer=1): South-North (85.1, 27.9) to (85.1, 28.1) with vertex at (85.1, 28.0)
        roads_gdf = gpd.GeoDataFrame([
            {"osm_id": 1, "highway": "trunk", "layer": 0, "geometry": LineString([(85.0, 28.0), (85.1, 28.0), (85.2, 28.0)])},
            {"osm_id": 2, "highway": "primary", "layer": 1, "bridge": True, "geometry": LineString([(85.1, 27.9), (85.1, 28.0), (85.1, 28.1)])},
        ], crs="EPSG:4326")

        analyzer.build_graph_from_geodataframe(roads_gdf)
        graph = analyzer.graph

        node_surface = analyzer._node_key(85.0, 28.0, layer=0)
        node_bridge = analyzer._node_key(85.1, 28.1, layer=1)

        import networkx as nx
        # Cars on the surface road cannot jump onto the overpass bridge!
        self.assertFalse(nx.has_path(graph, node_surface, node_bridge))

    def test_parallel_roads_preserved(self):
        """Two parallel roads between identical junction endpoints must both exist in MultiGraph."""
        analyzer = RoadNetworkConnectivityAnalyzer(self.pre_event_snapshot, self.event_date)

        # Road 1: North bypass
        # Road 2: South bypass
        roads_gdf = gpd.GeoDataFrame([
            {"osm_id": 10, "highway": "primary", "geometry": LineString([(85.0, 28.0), (85.05, 28.05), (85.1, 28.0)])},
            {"osm_id": 20, "highway": "secondary", "geometry": LineString([(85.0, 28.0), (85.05, 27.95), (85.1, 28.0)])},
        ], crs="EPSG:4326")

        analyzer.build_graph_from_geodataframe(roads_gdf)
        graph = analyzer.graph

        u = analyzer._node_key(85.0, 28.0)
        v = analyzer._node_key(85.1, 28.0)

        # Must have exactly 2 edges between u and v
        self.assertEqual(graph.number_of_edges(u, v), 2)

    def test_unattached_distant_settlement_recorded(self):
        """Settlements beyond max_snap_distance_meters must NOT snap falsely to distant roads."""
        analyzer = RoadNetworkConnectivityAnalyzer(
            self.pre_event_snapshot, self.event_date, max_snap_distance_meters=500.0
        )

        roads_gdf = gpd.GeoDataFrame([
            {"osm_id": 1, "highway": "primary", "geometry": LineString([(85.0, 28.0), (85.01, 28.0)])}
        ], crs="EPSG:4326")

        # Remote village 10 km away in the mountains
        settlements_gdf = gpd.GeoDataFrame([
            {"name": "Remote High Himalayan Village", "geometry": Point(85.1, 28.1)}
        ], crs="EPSG:4326")

        analyzer.build_graph_from_geodataframe(roads_gdf, settlements_gdf)

        self.assertEqual(len(analyzer.unattached_settlements), 1)
        self.assertEqual(analyzer.unattached_settlements[0].name, "Remote High Himalayan Village")
        self.assertGreater(analyzer.unattached_settlements[0].distance_meters, 500.0)

    def test_geodesic_distance_precision(self):
        """Geodesic distances must be in exact meters on WGS84 ellipsoid."""
        geom = LineString([(85.0, 28.0), (85.0, 28.01)])  # 0.01 deg latitude
        dist_m = float(WGS84_GEOD.geometry_length(geom))
        # 1 degree lat is ~110.8 km at 28 deg N, 0.01 deg is ~1,108 m
        self.assertTrue(1100.0 <= dist_m <= 1120.0)


if __name__ == "__main__":
    unittest.main()
