"""Copernicus Data Space Ecosystem (CDSE) Sentinel-1 Scene Discovery & Validation.

Official API: https://dataspace.copernicus.eu
Query interface: CDSE OData v1 Catalogue API
"""

from __future__ import annotations
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import httpx
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import unary_union

from varuna.contracts import RadarScene, validate_pair

logger = logging.getLogger("varuna.acquisition.cdse")

CDSE_ODATA_URL = os.getenv("CDSE_ODATA_URL", "https://catalogue.dataspace.copernicus.eu/odata/v1")


@dataclass(frozen=True)
class DiscoveredRadarScene(RadarScene):
    """Extended RadarScene with CDSE metadata, product type, and footprint."""
    product_name: str = ""
    cdse_id: str = ""
    sensor_mode: str = "IW"
    product_type: str = "GRD"
    footprint_geojson: Optional[Dict[str, Any]] = None
    coverage_ratio: float = 1.0  # Fraction of AOI covered by this scene

    @classmethod
    def from_odata_item(cls, item: Dict[str, Any], aoi_geom: Optional[Polygon] = None) -> DiscoveredRadarScene:
        """Parse raw CDSE OData item into DiscoveredRadarScene."""
        scene_id = item.get("Name", "")
        cdse_id = str(item.get("Id", ""))
        
        # Parse ContentDate
        content_date = item.get("ContentDate", {})
        start_str = content_date.get("Start")
        if not start_str:
            raise ValueError(f"Missing ContentDate/Start in CDSE product {cdse_id}")
        
        # Handle ISO strings with Z or timezone offset
        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        if start_dt.tzinfo is not None:
            # Normalize to naive UTC for consistent comparison with user dates
            start_dt = start_dt.astimezone(timezone.utc).replace(tzinfo=None)

        # Parse attributes with strict validation (no silent defaults)
        attributes = {attr.get("Name"): attr.get("Value") for attr in item.get("Attributes", []) if "Name" in attr}
        
        # Relative orbit
        if "relativeOrbitNumber" not in attributes:
            raise ValueError(f"Missing required attribute 'relativeOrbitNumber' in CDSE product {cdse_id}")
        rel_orbit = int(attributes["relativeOrbitNumber"])
        if not (1 <= rel_orbit <= 175):
            raise ValueError(f"Invalid relativeOrbitNumber {rel_orbit} in CDSE product {cdse_id}")
        
        # Orbit direction (ASCENDING / DESCENDING)
        if "orbitDirection" not in attributes:
            raise ValueError(f"Missing required attribute 'orbitDirection' in CDSE product {cdse_id}")
        raw_direction = str(attributes["orbitDirection"]).upper()
        if "ASC" in raw_direction:
            direction = "ASCENDING"
        elif "DESC" in raw_direction:
            direction = "DESCENDING"
        else:
            raise ValueError(f"Invalid orbitDirection '{raw_direction}' in CDSE product {cdse_id}")
        
        # Polarization
        if "polarisationChannels" not in attributes:
            raise ValueError(f"Missing required attribute 'polarisationChannels' in CDSE product {cdse_id}")
        polarization = str(attributes["polarisationChannels"])
        
        # Sensor Mode & Product Type
        sensor_mode_raw = attributes.get("operationalMode") or attributes.get("sensorOperationalMode")
        if not sensor_mode_raw:
            raise ValueError(f"Missing required attribute 'operationalMode' in CDSE product {cdse_id}")
        sensor_mode = str(sensor_mode_raw)
        product_type = str(attributes.get("productType") or ("GRD" if "GRD" in scene_id else "UNKNOWN"))
        
        # Footprint
        footprint = item.get("GeoFootprint")
        coverage_ratio = 1.0
        if aoi_geom and footprint:
            try:
                poly = shape(footprint)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                inter = aoi_geom.intersection(poly)
                if aoi_geom.area > 0:
                    coverage_ratio = float(inter.area / aoi_geom.area)
            except Exception as e:
                logger.warning(f"Failed to calculate footprint coverage: {e}")
                coverage_ratio = 0.0

        source_url = f"{CDSE_ODATA_URL}/Products({cdse_id})/$value"

        return cls(
            scene_id=scene_id,
            acquired_at=start_dt,
            relative_orbit=rel_orbit,
            pass_direction=direction,
            polarization=polarization,
            source_url=source_url,
            product_name=scene_id,
            cdse_id=cdse_id,
            sensor_mode=sensor_mode,
            product_type=product_type,
            footprint_geojson=footprint,
            coverage_ratio=coverage_ratio,
        )


@dataclass
class ScenePairRecommendation:
    """Scientifically validated pair of Sentinel-1 scenes suitable for change detection."""
    before_scene: DiscoveredRadarScene
    after_scene: DiscoveredRadarScene
    event_date: datetime
    orbit_direction: str
    relative_orbit: int
    temporal_baseline_days: float
    scientific_rationale: str
    provenance_metadata: Dict[str, Any] = field(default_factory=dict)


class CDSEDiscoveryError(RuntimeError):
    """Raised when scene discovery encounters API or validation failures."""
    pass


class IncompatibleScenePairError(ValueError):
    """Raised when no scientifically defensible pre/post scene pair can be formed."""
    pass


class CDSEDiscoveryService:
    """Service to discover and pair Sentinel-1 scenes from CDSE."""

    def __init__(self, base_url: str = CDSE_ODATA_URL, client: Optional[httpx.Client] = None):
        self.base_url = base_url.rstrip("/")
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client:
            return self._client
        return httpx.Client(timeout=30.0)

    def _build_wkt_polygon(self, geom: Polygon) -> str:
        """Convert a Shapely Polygon to WKT string formatted for CDSE OData."""
        coords = list(geom.exterior.coords)
        coord_str = ", ".join([f"{lon} {lat}" for lon, lat in coords])
        return f"geography'SRID=4326;POLYGON(({coord_str}))'"

    def query_scenes(
        self,
        aoi_geom: Polygon,
        start_date: datetime,
        end_date: datetime,
        sensor_mode: str = "IW",
        product_type: str = "GRD",
        top: int = 50,
    ) -> List[DiscoveredRadarScene]:
        """Query CDSE OData catalogue for Sentinel-1 scenes intersecting the AOI."""
        wkt_area = self._build_wkt_polygon(aoi_geom)
        start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # CDSE OData filter
        filters = [
            "Collection/Name eq 'SENTINEL-1'",
            f"ContentDate/Start ge {start_iso}",
            f"ContentDate/Start le {end_iso}",
            f"OData.CSC.Intersects(area={wkt_area})",
        ]
        
        if product_type:
            filters.append("contains(Name, 'GRD')")
        if sensor_mode:
            filters.append(
                f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'operationalMode' and att/OData.CSC.StringAttribute/Value eq '{sensor_mode}')"
            )

        filter_query = " and ".join(filters)
        url = f"{self.base_url}/Products"
        params = {
            "$filter": filter_query,
            "$orderby": "ContentDate/Start desc",
            "$top": str(top),
            "$expand": "Attributes",
        }

        raw_items = []
        last_err = None
        for attempt in range(1, 4):
            client = self._get_client()
            try:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                raw_items = data.get("value", [])
                last_err = None
                break
            except httpx.HTTPStatusError as e:
                logger.error(f"CDSE OData HTTP error: {e.response.status_code} - {e.response.text}")
                raise CDSEDiscoveryError(f"CDSE catalogue request failed: HTTP {e.response.status_code}") from e
            except Exception as e:
                last_err = e
                logger.warning(f"CDSE network request attempt {attempt}/3 failed: {e}. Retrying...")
                if self._client:
                    try:
                        self._client.close()
                    except Exception:
                        pass
                    self._client = None
                import time
                time.sleep(1.0 * attempt)

        if last_err is not None:
            logger.error(f"CDSE network request failed after 3 attempts: {last_err}")
            raise CDSEDiscoveryError(f"Could not connect to CDSE catalogue: {str(last_err)}") from last_err

        scenes = []
        for item in raw_items:
            try:
                scene = DiscoveredRadarScene.from_odata_item(item, aoi_geom)
                scenes.append(scene)
            except Exception as e:
                logger.warning(f"Could not parse scene {item.get('Id')}: {e}")

        return scenes

    def discover_compatible_pair(
        self,
        aoi_geom: Polygon,
        event_date: datetime,
        pre_event_window_days: int = 30,
        post_event_window_days: int = 15,
        min_aoi_coverage: float = 0.50,
    ) -> ScenePairRecommendation:
        """Find the most scientifically sound Sentinel-1 pre/post pair bracketing the event.

        Strict radar geometry requirements:
        1. Identical relative orbit (ensures matching repeat pass geometry).
        2. Identical pass direction (ASCENDING vs DESCENDING).
        3. Identical polarization mode (e.g., VV or VV+VH).
        4. Acquisition dates bracket the event (pre < event <= post).
        5. Significant coverage of the requested AOI.
        """
        # Ensure event_date is naive UTC
        if event_date.tzinfo is not None:
            event_date = event_date.astimezone(timezone.utc).replace(tzinfo=None)

        start_pre = event_date - timedelta(days=pre_event_window_days)
        end_post = event_date + timedelta(days=post_event_window_days)

        all_scenes = self.query_scenes(aoi_geom, start_pre, end_post)

        if not all_scenes:
            raise IncompatibleScenePairError(
                f"No Sentinel-1 scenes found intersecting AOI between {start_pre.date()} and {end_post.date()}."
            )

        pre_scenes = [s for s in all_scenes if s.acquired_at < event_date and s.coverage_ratio >= min_aoi_coverage]
        post_scenes = [s for s in all_scenes if s.acquired_at >= event_date and s.coverage_ratio >= min_aoi_coverage]

        if not pre_scenes:
            raise IncompatibleScenePairError(
                f"No valid pre-event Sentinel-1 scenes found with AOI coverage >= {min_aoi_coverage*100}% "
                f"in window [{start_pre.date()} to {event_date.date()}]."
            )
        if not post_scenes:
            raise IncompatibleScenePairError(
                f"No valid post-event Sentinel-1 scenes found with AOI coverage >= {min_aoi_coverage*100}% "
                f"in window [{event_date.date()} to {end_post.date()}]."
            )

        # Search for compatible pairs
        candidate_pairs: List[Tuple[DiscoveredRadarScene, DiscoveredRadarScene, float]] = []

        for pre in pre_scenes:
            for post in post_scenes:
                try:
                    # Enforce the strict core contracts
                    validate_pair(pre, post, event_date)
                    
                    # Temporal baseline (absolute days between acquisitions)
                    dt_days = abs((post.acquired_at - pre.acquired_at).total_seconds()) / 86400.0
                    candidate_pairs.append((pre, post, dt_days))
                except ValueError:
                    # Incompatible orbit, direction, polarization, or temporal sequence
                    continue

        if not candidate_pairs:
            # Diagnose specific incompatibility for scientific transparency
            pre_orbits = sorted(list(set(s.relative_orbit for s in pre_scenes)))
            post_orbits = sorted(list(set(s.relative_orbit for s in post_scenes)))
            raise IncompatibleScenePairError(
                f"Incompatible radar geometry: Discovered {len(pre_scenes)} pre-event scenes (orbits: {pre_orbits}) "
                f"and {len(post_scenes)} post-event scenes (orbits: {post_orbits}), but zero matching relative orbit pairs. "
                f"Comparing different radar relative orbits causes severe pseudo-change from terrain layover and differing look angles."
            )

        # Sort candidate pairs by shortest temporal baseline (minimizes seasonal land-cover change)
        candidate_pairs.sort(key=lambda item: item[2])
        best_pre, best_post, baseline_days = candidate_pairs[0]

        rationale = (
            f"Selected Sentinel-1 pair with matching Relative Orbit {best_pre.relative_orbit} "
            f"({best_pre.pass_direction}, {best_pre.polarization}). "
            f"Pre-event acquisition: {best_pre.acquired_at.isoformat()} (AOI coverage: {best_pre.coverage_ratio*100:.1f}%). "
            f"Post-event acquisition: {best_post.acquired_at.isoformat()} (AOI coverage: {best_post.coverage_ratio*100:.1f}%). "
            f"Temporal baseline: {baseline_days:.1f} days. Minimal seasonal false positive risk."
        )

        provenance = {
            "search_aoi_wkt": aoi_geom.wkt,
            "event_date": event_date.isoformat(),
            "pre_scene_id": best_pre.scene_id,
            "pre_acquired_at": best_pre.acquired_at.isoformat(),
            "pre_cdse_id": best_pre.cdse_id,
            "post_scene_id": best_post.scene_id,
            "post_acquired_at": best_post.acquired_at.isoformat(),
            "post_cdse_id": best_post.cdse_id,
            "relative_orbit": best_pre.relative_orbit,
            "pass_direction": best_pre.pass_direction,
            "polarization": best_pre.polarization,
            "temporal_baseline_days": baseline_days,
            "query_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return ScenePairRecommendation(
            before_scene=best_pre,
            after_scene=best_post,
            event_date=event_date,
            orbit_direction=best_pre.pass_direction,
            relative_orbit=best_pre.relative_orbit,
            temporal_baseline_days=baseline_days,
            scientific_rationale=rationale,
            provenance_metadata=provenance,
        )
