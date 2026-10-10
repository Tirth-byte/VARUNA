"""VARUNA Data Leakage Prevention and Reference Separation Guard.

Strict scientific boundary separating prediction inputs (Sentinel-1/2, pre-event OSM, DEM)
from prohibited reference validation datasets (Copernicus EMS EMSR927, UNOSAT, post-event OSM).
"""

from enum import Enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetRole(str, Enum):
    """Explicit role of a dataset in the VARUNA processing pipeline."""
    PREDICTION_INPUT = "PREDICTION_INPUT"
    INDEPENDENT_VALIDATION = "INDEPENDENT_VALIDATION"
    PROHIBITED = "PROHIBITED"


class DataProvenance(BaseModel):
    """Full provenance record for any vector, raster, or table artifact."""
    dataset_name: str
    dataset_role: DatasetRole
    source_uri: str
    acquisition_or_snapshot_date: datetime
    event_date: datetime
    crs: str = "EPSG:4326"
    license: str
    description: str
    is_synthetic_fixture: bool = False

    def validate_for_inference(self) -> None:
        """Enforce strict anti-leakage rules before processing."""
        # 1. Prohibited sources cannot enter inference
        prohibited_keywords = ["copernicus ems", "emsr", "unosat", "damage assessment"]
        name_lower = self.dataset_name.lower()
        for kw in prohibited_keywords:
            if kw in name_lower and self.dataset_role == DatasetRole.PREDICTION_INPUT:
                raise ValueError(
                    f"DATA LEAKAGE VIOLATION: '{self.dataset_name}' contains reference damage assessment keywords "
                    f"and cannot be used as PREDICTION_INPUT. Allowed exclusively for INDEPENDENT_VALIDATION."
                )

        # 2. Strict temporal ordering: inputs must not be post-event unless they are post-event satellite observations
        is_satellite = any(s in name_lower for s in ["sentinel-1", "sentinel-2", "copernicus s1", "s1", "s2"])
        if not is_satellite and self.acquisition_or_snapshot_date >= self.event_date:
            raise ValueError(
                f"TEMPORAL LEAKAGE VIOLATION: Non-satellite input '{self.dataset_name}' dated "
                f"{self.acquisition_or_snapshot_date.isoformat()} is on or after the event date "
                f"{self.event_date.isoformat()}. Historical baseline data (OSM, DEM) must strictly precede the event."
            )

        if self.dataset_role != DatasetRole.PREDICTION_INPUT:
            raise ValueError(
                f"INVALID DATA ROLE: Dataset '{self.dataset_name}' has role {self.dataset_role}, "
                f"expected PREDICTION_INPUT for processing pipeline."
            )


def assert_not_reference_damage_map(dataset_name: str, intended_role: DatasetRole) -> None:
    """Guard against accidentally ingesting Copernicus EMS or UNOSAT into prediction models."""
    reference_signatures = ["EMSR927", "EMSR", "UNOSAT", "COPERNICUS_EMS", "DAMAGE_MAP"]
    upper = dataset_name.upper()
    if any(sig in upper for sig in reference_signatures):
        if intended_role != DatasetRole.INDEPENDENT_VALIDATION:
            raise ValueError(
                f"Scientific integrity violation: Reference layer '{dataset_name}' is reserved exclusively "
                f"for held-out validation. Cannot be assigned to {intended_role}."
            )
