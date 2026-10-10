"""Unit tests for scientific anti-leakage guards and reference dataset separation."""

import unittest
from datetime import datetime

from varuna.validation.leakage_guard import (
    DatasetRole,
    DataProvenance,
    assert_not_reference_damage_map,
)


class TestLeakageGuard(unittest.TestCase):
    def setUp(self):
        self.event_date = datetime(2026, 8, 26)

    def test_emsr927_cannot_be_prediction_input(self):
        # Copernicus EMS EMSR927 damage map must be rejected as model input
        with self.assertRaises(ValueError) as ctx:
            prov = DataProvenance(
                dataset_name="Copernicus EMS EMSR927 Delineation Map",
                dataset_role=DatasetRole.PREDICTION_INPUT,
                source_uri="https://emergency.copernicus.eu/mapping/list-of-activations-rapid/EMSR927",
                acquisition_or_snapshot_date=datetime(2026, 8, 27),
                event_date=self.event_date,
                license="Copernicus Open Access",
                description="Reference validation layer",
            )
            prov.validate_for_inference()
        self.assertIn("DATA LEAKAGE VIOLATION", str(ctx.exception))

    def test_post_event_osm_cannot_be_prediction_input(self):
        # OSM snapshot after the flood event must be rejected
        with self.assertRaises(ValueError) as ctx:
            prov = DataProvenance(
                dataset_name="OpenStreetMap Nepal Snapshot",
                dataset_role=DatasetRole.PREDICTION_INPUT,
                source_uri="https://overpass-api.de",
                acquisition_or_snapshot_date=datetime(2026, 8, 28),
                event_date=self.event_date,
                license="ODbL",
                description="OSM road and building vectors",
            )
            prov.validate_for_inference()
        self.assertIn("TEMPORAL LEAKAGE VIOLATION", str(ctx.exception))

    def test_valid_pre_event_sentinel_accepted(self):
        prov = DataProvenance(
            dataset_name="Sentinel-1A IW GRD",
            dataset_role=DatasetRole.PREDICTION_INPUT,
            source_uri="https://catalogue.dataspace.copernicus.eu/odata/v1/Products(123)",
            acquisition_or_snapshot_date=datetime(2026, 8, 20),
            event_date=self.event_date,
            license="Copernicus Sentinel Data Terms",
            description="Pre-event radar observation",
        )
        prov.validate_for_inference()

    def test_assert_not_reference_damage_map(self):
        with self.assertRaises(ValueError) as ctx:
            assert_not_reference_damage_map("EMSR927_DELINEATION", DatasetRole.PREDICTION_INPUT)
        self.assertIn("Scientific integrity violation", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
