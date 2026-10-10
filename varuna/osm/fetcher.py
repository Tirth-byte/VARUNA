"""Historical OpenStreetMap Retrieval Engine via Overpass API.

Strictly queries historical OSM snapshots dated PRIOR to the flood event date.
Enforces data leakage constraints and outputs GeoDataFrames for roads, bridges,
buildings, settlements, and hospitals.
"""

from __future__ import annotations
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

import httpx
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from varuna.contracts import validate_osm_snapshot

logger = logging.getLogger("varuna.osm.fetcher")

OVERPASS_API_URL = os.getenv("OVERPASS_API_URL", "https://overpass-api.de/api/interpreter")


class OverpassQueryError(RuntimeError):
    """Raised when Overpass API query fails."""
    pass


class HistoricalOSMFetcher:
    """Retrieves point-in-time OpenStreetMap vector layers before a disaster event."""

    def __init__(self, endpoint_url: str = OVERPASS_API_URL, client: Optional[httpx.Client] = None):
        self.endpoint_url = endpoint_url
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client:
            return self._client
        return httpx.Client(timeout=60.0)

    def build_overpass_query(
        self,
        bbox: Tuple[float, float, float, float],  # (min_lat, min_lon, max_lat, max_lon)
        snapshot_date: datetime,
        event_date: datetime,
    ) -> str:
        """Construct Overpass QL query with strict temporal point-in-time snapshot constraint."""
        validate_osm_snapshot(snapshot_date, event_date)
        date_iso = snapshot_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        min_lat, min_lon, max_lat, max_lon = bbox

        # Overpass QL with [date:"..."] sets point-in-time historical evaluation
        query = f"""
        [out:json][timeout:60][date:"{date_iso}"];
        (
          // Roads and bridges
          way["highway"]({min_lat},{min_lon},{max_lat},{max_lon});
          // Settlements, towns, cities
          node["place"~"city|town|village|hamlet"]({min_lat},{min_lon},{max_lat},{max_lon});
          // Hospitals and healthcare facilities
          node["amenity"="hospital"]({min_lat},{min_lon},{max_lat},{max_lon});
          way["amenity"="hospital"]({min_lat},{min_lon},{max_lat},{max_lon});
          // Buildings (sample)
          way["building"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out body;
        >;
        out skel qt;
        """
        return query

    def fetch_historical_osm(
        self,
        bbox: Tuple[float, float, float, float],
        snapshot_date: datetime,
        event_date: datetime,
    ) -> Dict[str, Any]:
        """Execute historical Overpass query."""
        validate_osm_snapshot(snapshot_date, event_date)
        query = self.build_overpass_query(bbox, snapshot_date, event_date)

        client = self._get_client()
        try:
            resp = client.post(self.endpoint_url, data={"data": query})
            resp.raise_for_status()
            data = resp.json()
            return data
        except Exception as e:
            raise OverpassQueryError(f"Overpass historical API request failed: {e}") from e

    def parse_osm_elements_to_geodataframes(
        self,
        osm_json: Dict[str, Any],
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Convert Overpass JSON elements into (roads_gdf, settlements_gdf, buildings_gdf)."""
        elements = osm_json.get("elements", [])
        nodes: Dict[int, Tuple[float, float]] = {}
        for elem in elements:
            if elem.get("type") == "node":
                nodes[elem["id"]] = (elem.get("lon", 0.0), elem.get("lat", 0.0))

        road_records = []
        settlement_records = []
        building_records = []

        for elem in elements:
            tags = elem.get("tags", {})
            elem_type = elem.get("type")

            if elem_type == "node" and ("place" in tags or tags.get("amenity") == "hospital"):
                lon, lat = elem.get("lon"), elem.get("lat")
                if lon is not None and lat is not None:
                    settlement_records.append({
                        "osm_id": elem.get("id"),
                        "name": tags.get("name", f"OSM_Node_{elem.get('id')}"),
                        "place": tags.get("place"),
                        "amenity": tags.get("amenity"),
                        "is_hospital": tags.get("amenity") == "hospital",
                        "is_town": tags.get("place") in ["city", "town"],
                        "geometry": Point(lon, lat),
                    })

            elif elem_type == "way":
                node_ids = elem.get("nodes", [])
                coords = [nodes[nid] for nid in node_ids if nid in nodes]
                if len(coords) >= 2:
                    if "highway" in tags:
                        road_records.append({
                            "osm_id": elem.get("id"),
                            "highway": tags.get("highway"),
                            "bridge": tags.get("bridge") in ["yes", "true", "1"],
                            "tunnel": tags.get("tunnel") in ["yes", "true", "1"],
                            "layer": int(tags.get("layer", 0)) if tags.get("layer", "0").lstrip("-").isdigit() else 0,
                            "name": tags.get("name"),
                            "geometry": LineString(coords),
                        })
                    elif "building" in tags and len(coords) >= 3:
                        # Close polygon if necessary
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        poly = Polygon(coords)
                        if poly.is_valid:
                            building_records.append({
                                "osm_id": elem.get("id"),
                                "building": tags.get("building"),
                                "geometry": poly,
                            })

        roads_gdf = gpd.GeoDataFrame(road_records, crs="EPSG:4326") if road_records else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")
        settlements_gdf = gpd.GeoDataFrame(settlement_records, crs="EPSG:4326") if settlement_records else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")
        buildings_gdf = gpd.GeoDataFrame(building_records, crs="EPSG:4326") if building_records else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")

        return roads_gdf, settlements_gdf, buildings_gdf
