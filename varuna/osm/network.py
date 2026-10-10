"""OpenStreetMap Road Network Connectivity and Infrastructure Exposure Engine.

Evaluates potential infrastructure exposure and isolation of settlements without
conflating remote sensing exposure with confirmed ground truth destruction.

Core Principle: "A satellite observation indicating possible flood exposure does
not prove a road or bridge is destroyed. Represent this distinction explicitly."
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple

import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import nearest_points

from varuna.contracts import validate_osm_snapshot


@dataclass
class InfrastructureExposureSummary:
    """Summary of infrastructure intersecting candidate flood or debris zones."""
    total_roads_analyzed_km: float
    exposed_roads_km: float
    exposed_road_percentage: float
    exposed_bridges_count: int
    exposed_buildings_count: int
    candidate_isolated_settlements_count: int
    candidate_isolated_settlements: List[str]
    disclaimer: str = (
        "IMPORTANT SCIENTIFIC LIMITATION: Remote sensing indicates potential hazard exposure, "
        "not confirmed structural destruction. Field inspection is required for ground truth."
    )


class RoadNetworkConnectivityAnalyzer:
    """Builds pre-event road graphs and assesses settlement connectivity loss after flood exposure."""

    def __init__(self, snapshot_date: datetime, event_date: datetime):
        # Strict temporal guard
        validate_osm_snapshot(snapshot_date, event_date)
        self.snapshot_date = snapshot_date
        self.event_date = event_date
        self.graph = nx.Graph()
        self.critical_hubs: Set[str] = set()  # Towns, hospitals, emergency depots

    def build_graph_from_geodataframe(
        self,
        roads_gdf: gpd.GeoDataFrame,
        settlements_gdf: Optional[gpd.GeoDataFrame] = None,
    ) -> nx.Graph:
        """Construct NetworkX graph from road LineStrings and settlement Points."""
        self.graph.clear()
        self.critical_hubs.clear()

        # Add edges from road geometries
        for idx, row in roads_gdf.iterrows():
            geom = row.geometry
            if not isinstance(geom, LineString):
                continue

            coords = list(geom.coords)
            u = f"{coords[0][0]:.6f}_{coords[0][1]:.6f}"
            v = f"{coords[-1][0]:.6f}_{coords[-1][1]:.6f}"

            length_m = float(row.get("length_m", geom.length * 111320.0))
            is_bridge = bool(row.get("bridge", False) or row.get("is_bridge", False))
            highway = str(row.get("highway", "unclassified"))
            road_id = str(row.get("osm_id", idx))

            self.graph.add_node(u, pos=(coords[0][0], coords[0][1]))
            self.graph.add_node(v, pos=(coords[-1][0], coords[-1][1]))
            self.graph.add_edge(
                u, v,
                road_id=road_id,
                length_m=length_m,
                highway=highway,
                is_bridge=is_bridge,
                geometry=geom,
                exposed_to_hazard=False,
            )

        # Attach settlements and hospitals to nearest graph nodes
        if settlements_gdf is not None:
            for idx, row in settlements_gdf.iterrows():
                geom = row.geometry
                if not isinstance(geom, Point):
                    continue
                name = str(row.get("name", f"Settlement_{idx}"))
                is_hospital = bool(row.get("amenity") == "hospital" or row.get("is_hospital", False))
                is_town = bool(row.get("place") in ["town", "city"] or row.get("is_town", False))

                # Find closest node in graph
                best_node = None
                min_dist = float("inf")
                for node, data in self.graph.nodes(data=True):
                    pos = data.get("pos")
                    if pos:
                        dist = (pos[0] - geom.x) ** 2 + (pos[1] - geom.y) ** 2
                        if dist < min_dist:
                            min_dist = dist
                            best_node = node

                if best_node:
                    self.graph.nodes[best_node]["settlement_name"] = name
                    self.graph.nodes[best_node]["is_hospital"] = is_hospital
                    self.graph.nodes[best_node]["is_town"] = is_town
                    if is_hospital or is_town:
                        self.critical_hubs.add(best_node)

        return self.graph

    def analyze_flood_impact(
        self,
        candidate_flood_gdf: gpd.GeoDataFrame,
        buildings_gdf: Optional[gpd.GeoDataFrame] = None,
    ) -> Tuple[InfrastructureExposureSummary, gpd.GeoDataFrame]:
        """Intersect hazard polygons with infrastructure and compute isolation impact."""
        if len(self.graph.edges) == 0:
            raise ValueError("Road graph is empty. Call build_graph_from_geodataframe first.")

        # Prepare exposed edges
        exposed_edges = []
        total_road_length_m = 0.0
        exposed_road_length_m = 0.0
        exposed_bridges_count = 0

        # Create scenario graph for connectivity testing
        scenario_graph = self.graph.copy()

        # Spatial union of flood/debris polygons for fast spatial intersection
        if len(candidate_flood_gdf) > 0:
            hazard_geom = candidate_flood_gdf.unary_union
        else:
            hazard_geom = Polygon()

        for u, v, data in self.graph.edges(data=True):
            geom = data.get("geometry")
            length = data.get("length_m", 0.0)
            is_bridge = data.get("is_bridge", False)
            total_road_length_m += length

            if not hazard_geom.is_empty and geom.intersects(hazard_geom):
                data["exposed_to_hazard"] = True
                exposed_road_length_m += length
                if is_bridge:
                    exposed_bridges_count += 1

                # In the scenario graph, remove or sever the exposed edge
                if scenario_graph.has_edge(u, v):
                    scenario_graph.remove_edge(u, v)

                exposed_edges.append({
                    "u": u,
                    "v": v,
                    "road_id": data.get("road_id"),
                    "highway": data.get("highway"),
                    "length_m": length,
                    "is_bridge": is_bridge,
                    "geometry": geom,
                    "exposure_status": "POTENTIALLY_EXPOSED",
                })

        # Evaluate building exposure
        exposed_buildings_count = 0
        if buildings_gdf is not None and len(buildings_gdf) > 0 and not hazard_geom.is_empty:
            intersecting = buildings_gdf[buildings_gdf.intersects(hazard_geom)]
            exposed_buildings_count = len(intersecting)

        # Assess settlement isolation
        isolated_settlements: List[str] = []
        for node, data in self.graph.nodes(data=True):
            s_name = data.get("settlement_name")
            if not s_name:
                continue

            # If node is a hub itself, it's not isolated from itself
            if node in self.critical_hubs:
                continue

            # Check if settlement originally had access to any critical hub
            had_access_originally = any(
                nx.has_path(self.graph, node, hub) for hub in self.critical_hubs
            )
            if not had_access_originally:
                continue

            # Check if settlement loses access to ALL critical hubs in scenario graph
            has_access_now = any(
                scenario_graph.has_node(node) and scenario_graph.has_node(hub) and nx.has_path(scenario_graph, node, hub)
                for hub in self.critical_hubs
            )

            if not has_access_now:
                isolated_settlements.append(s_name)

        summary = InfrastructureExposureSummary(
            total_roads_analyzed_km=total_road_length_m / 1000.0,
            exposed_roads_km=exposed_road_length_m / 1000.0,
            exposed_road_percentage=(exposed_road_length_m / max(total_road_length_m, 1.0)) * 100.0,
            exposed_bridges_count=exposed_bridges_count,
            exposed_buildings_count=exposed_buildings_count,
            candidate_isolated_settlements_count=len(isolated_settlements),
            candidate_isolated_settlements=sorted(list(set(isolated_settlements))),
        )

        exposed_gdf = gpd.GeoDataFrame(exposed_edges, crs="EPSG:4326") if exposed_edges else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")
        return summary, exposed_gdf
