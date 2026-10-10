"""Independent Reference Validation & Benchmark Engine.

Strictly evaluates predicted flood maps against independent held-out reference layers
such as Copernicus EMS EMSR927 or UNOSAT damage delineations.

ANTI-LEAKAGE RULE:
Reference layers must NEVER enter prediction models, preprocessing, or threshold tuning.
They are utilized exclusively in this held-out benchmarking framework.
"""

from __future__ import annotations
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

import numpy as np
import geopandas as gpd
from shapely.geometry import shape, Polygon
import pyproj

from varuna.validation.leakage_guard import (
    DatasetRole,
    DataProvenance,
    assert_not_reference_damage_map,
)

WGS84_GEOD = pyproj.Geod(ellps="WGS84")


@dataclass
class ValidationBenchmarkReport:
    """Scientific evaluation report comparing predictions against held-out reference."""
    reference_dataset_name: str
    reference_activation_code: str  # e.g. "EMSR927"
    event_date: str
    evaluation_date: str
    valid_evaluated_area_km2: float
    true_positive_pixels: int
    false_positive_pixels: int
    false_negative_pixels: int
    true_negative_pixels: int
    iou_score: float               # Intersection over Union (Jaccard Index)
    precision_score: float         # TP / (TP + FP)
    recall_score: float            # TP / (TP + FN)
    f1_score: float                # Harmonic mean of Precision and Recall
    accuracy_score: float          # (TP + TN) / Total
    confusion_matrix: Dict[str, int]
    methodological_notes: str
    limitations: Dict[str, str] = field(default_factory=dict)


class IndependentValidationBenchmark:
    """Computes held-out performance metrics between predictions and reference damage maps."""

    def __init__(
        self,
        reference_provenance: DataProvenance,
    ):
        # Strict validation role assertion
        if reference_provenance.dataset_role != DatasetRole.INDEPENDENT_VALIDATION:
            raise ValueError(
                f"Data role violation: Benchmark requires INDEPENDENT_VALIDATION dataset role, "
                f"got {reference_provenance.dataset_role}"
            )
        self.provenance = reference_provenance

    def evaluate_raster_alignment_and_metrics(
        self,
        predicted_binary_mask: np.ndarray,
        reference_binary_mask: np.ndarray,
        valid_evaluation_mask: np.ndarray,
        pixel_area_m2: float,
    ) -> ValidationBenchmarkReport:
        """Calculate pixel-level confusion matrix and IoU over aligned valid area."""
        if predicted_binary_mask.shape != reference_binary_mask.shape:
            raise ValueError(
                f"Dimension mismatch between prediction {predicted_binary_mask.shape} "
                f"and reference {reference_binary_mask.shape}. Must be pre-aligned."
            )

        # Restrict strictly to valid evaluated region
        valid = valid_evaluation_mask.astype(bool)
        pred = predicted_binary_mask[valid].astype(bool)
        ref = reference_binary_mask[valid].astype(bool)

        total_valid_pixels = int(np.sum(valid))
        valid_area_km2 = (total_valid_pixels * pixel_area_m2) / 1e6

        tp = int(np.sum(pred & ref))
        fp = int(np.sum(pred & (~ref)))
        fn = int(np.sum((~pred) & ref))
        tn = int(np.sum((~pred) & (~ref)))

        # Metrics
        denom_iou = tp + fp + fn
        iou = float(tp / denom_iou) if denom_iou > 0 else 0.0

        denom_prec = tp + fp
        precision = float(tp / denom_prec) if denom_prec > 0 else 0.0

        denom_rec = tp + fn
        recall = float(tp / denom_rec) if denom_rec > 0 else 0.0

        f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        accuracy = float((tp + tn) / max(total_valid_pixels, 1))

        matrix = {
            "True_Positive_TP": tp,
            "False_Positive_FP": fp,
            "False_Negative_FN": fn,
            "True_Negative_TN": tn,
        }

        notes = (
            f"Evaluated against reference layer '{self.provenance.dataset_name}' "
            f"(Source: {self.provenance.source_uri}). "
            "Classes: 1 = Inundated / Flood Hazard, 0 = Non-inundated. "
            "Excludes nodata and non-overlapping areas."
        )

        limitations = {
            "temporal_lag": "Sentinel SAR acquisition timestamp differs by hours/days from optical EMS reference.",
            "definition_discrepancy": "Copernicus EMS delineations may include manual photo-interpretation of mud/debris not purely water.",
            "sensor_resolution": "Sentinel-1 resolution (10m-20m) vs EMS very-high-resolution aerial/Pleiades inputs.",
        }

        return ValidationBenchmarkReport(
            reference_dataset_name=self.provenance.dataset_name,
            reference_activation_code="EMSR927" if "927" in self.provenance.dataset_name else "UNKNOWN_ACTIVATION",
            event_date=self.provenance.event_date.isoformat(),
            evaluation_date=datetime.now(timezone.utc).isoformat(),
            valid_evaluated_area_km2=valid_area_km2,
            true_positive_pixels=tp,
            false_positive_pixels=fp,
            false_negative_pixels=fn,
            true_negative_pixels=tn,
            iou_score=iou,
            precision_score=precision,
            recall_score=recall,
            f1_score=f1,
            accuracy_score=accuracy,
            confusion_matrix=matrix,
            methodological_notes=notes,
            limitations=limitations,
        )

    def generate_spatial_agreement_mask(
        self,
        predicted_binary_mask: np.ndarray,
        reference_binary_mask: np.ndarray,
        valid_mask: np.ndarray,
    ) -> np.ndarray:
        """Create categorical spatial agreement raster:

        Values:
          0 = NoData / Invalid
          1 = True Negative (Agreement: No Flood)
          2 = True Positive (Agreement: Inundation Confirmed)
          3 = False Positive (Over-prediction: Candidate Flood not in Reference)
          4 = False Negative (Under-prediction: Reference Flood missed by SAR)
        """
        out = np.zeros(predicted_binary_mask.shape, dtype=np.uint8)
        p = predicted_binary_mask.astype(bool)
        r = reference_binary_mask.astype(bool)
        v = valid_mask.astype(bool)

        out[v & (~p) & (~r)] = 1
        out[v & p & r] = 2
        out[v & p & (~r)] = 3
        out[v & (~p) & r] = 4
        return out
