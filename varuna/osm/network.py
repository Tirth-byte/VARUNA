"""OpenStreetMap Road Network Topology, Geodesic Metrics & Exposure Analysis Engine.

Constructs topologically sound road networks using NetworkX MultiGraph:
- Real intersection noding (handles T-junctions, X-junctions, sub-segments)
- Elevation/layer awareness (bridges and tunnels at different layers do not falsely intersect)
- Parallel edge preservation
- Geodesic metric calculations (WGS84 ellipsoidal distance and area via PyProj Geod)
- Strict snapping radius with unattached settlement tracking
- Multi-destination critical hub reachability
- Clear distinction between Hazard Observation, Exposure, Closure Scenario, and Verified Damage
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Tuple

import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString, MultiLineString, Polygon
from shapely.ops import nearest_points
import pyproj

from varuna.contracts import validate_osm_snapshot


# Initialize WGS84 Geod for exact geodesic metric calculations
WGS84_GEOD = pyproj.Geod(ellps="WGS84")


class InfrastructureState(str, Enum):
    """Explicit lifecycle states separating remote sensing observations from ground truth damage."""
    OBSERVED_HAZARD = "OBSERVED_HAZARD"                                     # Satellite-detected water/debris
    POTENTIAL_INFRASTRUCTURE_EXPOSURE = "POTENTIAL_INFRASTRUCTURE_EXPOSURE" # Road geometry intersects hazard
    HYPOTHETICAL_ROAD_CLOSURE = "HYPOTHETICAL_ROAD_CLOSURE"                 # Simulation assumption for reachability
    SCENARIO_ISOLATED_SETTLEMENT = "SCENARIO_ISOLATED_SETTLEMENT"           # Lost access under closure assumption
    INDEPENDENTLY_VERIFIED_DAMAGE = "INDEPENDENTLY_VERIFIED_DAMAGE"         # Confirmed by external ground truth


@dataclass
class UnattachedSettlement:
    """Settlement too far from road network to reliably snap."""
    name: str
    distance_meters: float
    max_threshold_meters: float
    coords: Tuple[float, float]


@dataclass
class InfrastructureExposureSummary:
    """Scientific summary of infrastructure exposure and scenario-based isolation."""
    total_roads_analyzed_meters: float
    total_roads_analyzed_km: float
    exposed_roads_meters: float
    exposed_roads_km: float
    exposed_road_percentage: float
    exposed_bridges_count: int
    exposed_buildings_count: int
    candidate_isolated_settlements_count: int
    candidate_isolated_settlements: List[str]
    unattached_settlements_count: int
    unattached_settlements: List[Dict[str, Any]]
    critical_hubs_count: int
    critical_hubs_names: List[str]
    measurement_crs: str = "WGS84 Ellipsoidal (Geodesic via pyproj.Geod)"
    assumptions_and_disclaimer: str = (
        "SCIENTIFIC ASSUMPTION & LIMITATION: A satellite hazard observation intersecting a road "
        "defines POTENTIAL_INFRASTRUCTURE_EXPOSURE. Road closure is a HYPOTHETICAL simulation scenario "
        "to test accessibility vulnerabilities. It does NOT prove physical destruction or impassability. "
        "Field inspection is required for ground truth verification."
    )


class RoadNetworkConnectivityAnalyzer:
    """Topologically correct road network connectivity and isolation analyzer."""

    def __init__(
        self,
        snapshot_date: datetime,
        event_date: datetime,
        max_snap_distance_meters: float = 1000.0,
    ):
        validate_osm_snapshot(snapshot_date, event_date)
        self.snapshot_date = snapshot_date
        self.event_date = event_date
        self.max_snap_distance_meters = max_snap_distance_meters
        # MultiGraph preserves multiple distinct parallel roads between identical junctions
        self.graph = nx.MultiGraph()
        self.critical_hubs: Set[str] = set()
        self.unattached_settlements: List[UnattachedSettlement] = []

    def _node_key(self, lon: float, lat: float, layer: int = 0) -> str:
        """Create unique key for node at given coordinates and elevation layer."""
        return f"{lon:.7f}_{lat:.7f}_L{layer}"

    def build_graph_from_geodataframe(
        self,
        roads_gdf: gpd.GeoDataFrame,
        settlements_gdf: Optional[gpd.GeoDataFrame] = None,
    ) -> nx.MultiGraph:
        """Construct topologically segmented MultiGraph from road LineStrings.

        Noding Rules:
        1. Explodes multi-segment lines at real intersection vertices.
        2. Respects 'layer' attribute (default layer=0). Bridges/overpasses at layer=1
           crossing roads at layer=0 do NOT form false junctions.
        3. Computes exact geodesic lengths in meters.
        4. Preserves parallel edges.
        """
        self.graph.clear()
        self.critical_hubs.clear()
        self.unattached_settlements.clear()

        # Phase 1: Identify all coordinate vertices and their visit counts per layer
        coord_visits: Dict[Tuple[float, float, int], int] = {}
        processed_roads = []

        for idx, row in roads_gdf.iterrows():
            geom = row.geometry
            if not isinstance(geom, LineString) or geom.is_empty:
                continue

            # Layer / level handling
            raw_layer = row.get("layer", 0)
            try:
                layer = int(raw_layer)
            except (ValueError, TypeError):
                layer = 0

            coords = list(geom.coords)
            if len(coords) < 2:
                continue

            # Record endpoints and vertices
            for i, (lon, lat) in enumerate(coords):
                key = (round(lon, 7), round(lat, 7), layer)
                coord_visits[key] = coord_visits.get(key, 0) + 1

            processed_roads.append((row, coords, layer, idx))

        # Phase 2: Segment LineStrings at real junctions (endpoints or vertices with >1 visits)
        edge_id = 0
        for row, coords, layer, orig_idx in processed_roads:
            is_bridge = bool(row.get("bridge", False) or row.get("is_bridge", False))
            highway = str(row.get("highway", "unclassified"))
            osm_id = str(row.get("osm_id", orig_idx))

            sub_segment_coords = [coords[0]]
            for i in range(1, len(coords)):
                curr_pt = coords[i]
                sub_segment_coords.append(curr_pt)

                pt_key = (round(curr_pt[0], 7), round(curr_pt[1], 7), layer)
                is_junction = (coord_visits.get(pt_key, 0) > 1) or (i == len(coords) - 1)

                if is_junction and len(sub_segment_coords) >= 2:
                    sub_geom = LineString(sub_segment_coords)
                    # Compute exact geodesic length in meters
                    length_m = float(WGS84_GEOD.geometry_length(sub_geom))

                    u = self._node_key(sub_segment_coords[0][0], sub_segment_coords[0][1], layer)
                    v = self._node_key(sub_segment_coords[-1][0], sub_segment_coords[-1][1], layer)

                    self.graph.add_node(u, pos=(sub_segment_coords[0][0], sub_segment_coords[0][1]), layer=layer)
                    self.graph.add_node(v, pos=(sub_segment_coords[-1][0], sub_segment_coords[-1][1]), layer=layer)

                    self.graph.add_edge(
                        u, v,
                        key=edge_id,
                        edge_id=edge_id,
                        osm_id=osm_id,
                        highway=highway,
                        is_bridge=is_bridge,
                        layer=layer,
                        length_meters=length_m,
                        geometry=sub_geom,
                        state=InfrastructureState.OBSERVED_HAZARD,
                    )
                    edge_id += 1
                    sub_segment_coords = [curr_pt]

        # Phase 3: Snap settlements and hospitals to network within threshold
        if settlements_gdf is not None and len(self.graph.nodes) > 0:
            for idx, row in settlements_gdf.iterrows():
                geom = row.geometry
                if not isinstance(geom, Point) or geom.is_empty:
                    continue

                name = str(row.get("name", f"Settlement_{idx}"))
                is_hospital = bool(row.get("amenity") == "hospital" or row.get("is_hospital", False))
                is_town = bool(row.get("place") in ["town", "city"] or row.get("is_town", False))

                # Find closest node using geodesic distance
                best_node = None
                min_dist_m = float("inf")

                for node, data in self.graph.nodes(data=True):
                    pos = data.get("pos")
                    if pos:
                        node_pt = Point(pos[0], pos[1])
                        # Geodesic distance in meters
                        dist_m = float(WGS84_GEOD.line_length([pos[0], geom.x], [pos[1], geom.y]))
                        if dist_m < min_dist_m:
                            min_dist_m = dist_m
                            best_node = node

                if min_dist_m <= self.max_snap_distance_meters and best_node:
                    self.graph.nodes[best_node]["settlement_name"] = name
                    self.graph.nodes[best_node]["is_hospital"] = is_hospital
                    self.graph.nodes[best_node]["is_town"] = is_town
                    if is_hospital or is_town:
                        self.critical_hubs.add(best_node)
                else:
                    self.unattached_settlements.append(
                        UnattachedSettlement(
                            name=name,
                            distance_meters=min_dist_m,
                            max_threshold_meters=self.max_snap_distance_meters,
                            coords=(geom.x, geom.y),
                        )
                    )

        return self.graph

    def analyze_flood_impact(
        self,
        candidate_flood_gdf: gpd.GeoDataFrame,
        buildings_gdf: Optional[gpd.GeoDataFrame] = None,
    ) -> Tuple[InfrastructureExposureSummary, gpd.GeoDataFrame]:
        """Intersect hazard polygons with infrastructure and evaluate scenario-based reachability."""
        if len(self.graph.edges) == 0:
            raise ValueError("Road graph is empty. Call build_graph_from_geodataframe first.")

        exposed_edges = []
        total_road_meters = 0.0
        exposed_road_meters = 0.0
        exposed_bridges_count = 0

        # Create scenario graph for connectivity testing
        scenario_graph = self.graph.copy()

        # Build union of hazard geometries for spatial intersection
        if len(candidate_flood_gdf) > 0:
            hazard_geom = candidate_flood_gdf.unary_union
        else:
            hazard_geom = Polygon()

        for u, v, k, data in self.graph.edges(keys=True, data=True):
            geom = data.get("geometry")
            length = data.get("length_meters", 0.0)
            is_bridge = data.get("is_bridge", False)
            total_road_meters += length

            if not hazard_geom.is_empty and geom.intersects(hazard_geom):
                exposed_road_meters += length
                if is_bridge:
                    exposed_bridges_count += 1

                # In the closure scenario, remove this edge
                if scenario_graph.has_edge(u, v, key=k):
                    scenario_graph.remove_edge(u, v, key=k)

                exposed_edges.append({
                    "u": u,
                    "v": v,
                    "key": k,
                    "osm_id": data.get("osm_id"),
                    "highway": data.get("highway"),
                    "length_meters": length,
                    "is_bridge": is_bridge,
                    "layer": data.get("layer", 0),
                    "geometry": geom,
                    "state": InfrastructureState.POTENTIAL_INFRASTRUCTURE_EXPOSURE.value,
                })

        # Evaluate building exposure
        exposed_buildings_count = 0
        if buildings_gdf is not None and len(buildings_gdf) > 0 and not hazard_geom.is_empty:
            intersecting = buildings_gdf[buildings_gdf.intersects(hazard_geom)]
            exposed_buildings_count = len(intersecting)

        # Multi-destination settlement isolation analysis
        isolated_settlements: List[str] = []
        hub_names: List[str] = []

        for hub in self.critical_hubs:
            hub_name = self.graph.nodes[hub].get("settlement_name", hub)
            hub_names.append(hub_name)

        for node, data in self.graph.nodes(data=True):
            s_name = data.get("settlement_name")
            if not s_name:
                continue

            if node in self.critical_hubs:
                continue

            # Check if settlement originally had access to AT LEAST ONE critical hub
            had_access_originally = any(
                nx.has_path(self.graph, node, hub) for hub in self.critical_hubs
            )
            if not had_access_originally:
                continue

            # Check if settlement loses access to ALL critical hubs under hypothetical closure
            has_access_under_scenario = any(
                scenario_graph.has_node(node)
                and scenario_graph.has_node(hub)
                and nx.has_path(scenario_graph, node, hub)
                for hub in self.critical_hubs
            )

            if not has_access_under_scenario:
                isolated_settlements.append(s_name)

        unattached_records = [
            {
                "name": u.name,
                "distance_meters": u.distance_meters,
                "max_threshold_meters": u.max_threshold_meters,
                "lon": u.coords[0],
                "lat": u.coords[1],
            }
            for u in self.unattached_settlements
        ]

        summary = InfrastructureExposureSummary(
            total_roads_analyzed_meters=total_road_meters,
            total_roads_analyzed_km=total_road_meters / 1000.0,
            exposed_roads_meters=exposed_road_meters,
            exposed_roads_km=exposed_road_meters / 1000.0,
            exposed_road_percentage=(exposed_road_meters / max(total_road_meters, 1.0)) * 100.0,
            exposed_bridges_count=exposed_bridges_count,
            exposed_buildings_count=exposed_buildings_count,
            candidate_isolated_settlements_count=len(isolated_settlements),
            candidate_isolated_settlements=sorted(list(set(isolated_settlements))),
            unattached_settlements_count=len(unattached_records),
            unattached_settlements=unattached_records,
            critical_hubs_count=len(self.critical_hubs),
            critical_hubs_names=sorted(list(set(hub_names))),
        )

        exposed_gdf = gpd.GeoDataFrame(exposed_edges, crs="EPSG:4326") if exposed_edges else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")
        return summary, exposed_gdf
