"""VARUNA flood and debris detection package."""
from varuna.detection.baseline import (
    LandCoverChangeClass,
    BaselineDetectionConfig,
    BaselineDetectionResult,
    run_baseline_detection,
    compute_otsu_threshold,
)

__all__ = [
    "LandCoverChangeClass",
    "BaselineDetectionConfig",
    "BaselineDetectionResult",
    "run_baseline_detection",
    "compute_otsu_threshold",
]
