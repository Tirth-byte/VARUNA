"""VARUNA — Satellite-Powered Flood Intelligence System.

Track B: Mapping Flood Damage from Space (Multimodal AI Hackathon 2026).
"""

from varuna.contracts import RadarScene, validate_pair, validate_osm_snapshot

__version__ = "0.1.0"
__all__ = [
    "RadarScene",
    "validate_pair",
    "validate_osm_snapshot",
]
