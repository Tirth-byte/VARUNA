"""VARUNA geospatial data contracts; no fake data or claims."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class RadarScene:
    scene_id: str
    acquired_at: datetime
    relative_orbit: int
    pass_direction: Literal['ASCENDING', 'DESCENDING']
    polarization: str
    source_url: str

    def __post_init__(self):
        if not self.scene_id.strip() or not self.source_url.startswith('https://'):
            raise ValueError('Satellite scene ID and HTTPS source URL required')
        if not 1 <= self.relative_orbit <= 175:
            raise ValueError('Invalid Sentinel-1 relative orbit')


def validate_pair(before: RadarScene, after: RadarScene, event_date: datetime) -> None:
    """Fail closed on obvious mismatches; not a substitute for image co-registration."""
    if not before.acquired_at < event_date <= after.acquired_at:
        raise ValueError('Before/after scenes do not bracket event date')
    if before.relative_orbit != after.relative_orbit:
        raise ValueError('Different radar relative orbits: invalid pixel comparison')
    if before.pass_direction != after.pass_direction:
        raise ValueError('Different pass directions')
    if before.polarization != after.polarization:
        raise ValueError('Different polarizations')


def validate_osm_snapshot(snapshot_at: datetime, event_date: datetime) -> None:
    if snapshot_at >= event_date:
        raise ValueError('OSM snapshot is not strictly pre-event; leakage risk')
