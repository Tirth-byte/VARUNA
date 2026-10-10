"""Unit tests for independent reference validation and held-out benchmark engine."""

import unittest
from datetime import datetime
import numpy as np

from varuna.validation.leakage_guard import DatasetRole, DataProvenance
from varuna.validation.benchmark import IndependentValidationBenchmark


class TestValidationBenchmark(unittest.TestCase):
    def setUp(self):
        self.prov = DataProvenance(
            dataset_name="Copernicus EMS EMSR927 Rapid Mapping Delineation",
            dataset_role=DatasetRole.INDEPENDENT_VALIDATION,
            source_uri="https://emergency.copernicus.eu/mapping/list-of-activations-rapid/EMSR927",
            acquisition_or_snapshot_date=datetime(2026, 8, 27),
            event_date=datetime(2026, 8, 26),
            license="Copernicus Open Access",
            description="Reference delineation map",
        )
        self.benchmark = IndependentValidationBenchmark(self.prov)

    def test_benchmark_metrics_computation(self):
        # 10x10 grid with:
        # 4 True Positives (pred=1, ref=1)
        # 1 False Positive (pred=1, ref=0)
        # 1 False Negative (pred=0, ref=1)
        # 94 True Negatives (pred=0, ref=0)
        pred = np.zeros((10, 10), dtype=np.uint8)
        ref = np.zeros((10, 10), dtype=np.uint8)

        # TP
        pred[0:2, 0:2] = 1
        ref[0:2, 0:2] = 1

        # FP
        pred[5, 5] = 1

        # FN
        ref[6, 6] = 1

        valid_mask = np.ones((10, 10), dtype=bool)
        report = self.benchmark.evaluate_raster_alignment_and_metrics(pred, ref, valid_mask, pixel_area_m2=100.0)

        # IoU = TP / (TP + FP + FN) = 4 / (4 + 1 + 1) = 4 / 6 = 0.6667
        self.assertAlmostEqual(report.iou_score, 4.0 / 6.0, places=4)

        # Precision = TP / (TP + FP) = 4 / 5 = 0.80
        self.assertAlmostEqual(report.precision_score, 0.80, places=4)

        # Recall = TP / (TP + FN) = 4 / 5 = 0.80
        self.assertAlmostEqual(report.recall_score, 0.80, places=4)

        # F1 = 2 * P * R / (P + R) = 0.80
        self.assertAlmostEqual(report.f1_score, 0.80, places=4)

        self.assertEqual(report.confusion_matrix["True_Positive_TP"], 4)
        self.assertEqual(report.confusion_matrix["False_Positive_FP"], 1)
        self.assertEqual(report.confusion_matrix["False_Negative_FN"], 1)

    def test_spatial_agreement_mask(self):
        pred = np.array([[1, 0], [1, 0]], dtype=np.uint8)
        ref = np.array([[1, 1], [0, 0]], dtype=np.uint8)
        valid = np.ones((2, 2), dtype=bool)

        mask = self.benchmark.generate_spatial_agreement_mask(pred, ref, valid)
        # (0,0): TP -> 2
        # (0,1): FN -> 4
        # (1,0): FP -> 3
        # (1,1): TN -> 1
        self.assertEqual(mask[0, 0], 2)
        self.assertEqual(mask[0, 1], 4)
        self.assertEqual(mask[1, 0], 3)
        self.assertEqual(mask[1, 1], 1)

    def test_rejection_if_dataset_role_not_validation(self):
        bad_prov = DataProvenance(
            dataset_name="Copernicus EMS EMSR927",
            dataset_role=DatasetRole.PREDICTION_INPUT,  # Illegal role for benchmark
            source_uri="https://emergency.copernicus.eu",
            acquisition_or_snapshot_date=datetime(2026, 8, 25),
            event_date=datetime(2026, 8, 26),
            license="Open",
            description="Bad role",
        )
        with self.assertRaises(ValueError):
            IndependentValidationBenchmark(bad_prov)


if __name__ == "__main__":
    unittest.main()
