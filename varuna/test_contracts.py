import unittest
from datetime import datetime
try:
    from varuna.contracts import RadarScene, validate_pair, validate_osm_snapshot
except ImportError:
    from contracts import RadarScene, validate_pair, validate_osm_snapshot

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.event = datetime(2026, 8, 26)
        self.before = RadarScene('S1_before', datetime(2026, 8, 20), 42, 'ASCENDING', 'VV', 'https://example.org/before')
        self.after = RadarScene('S1_after', datetime(2026, 9, 1), 42, 'ASCENDING', 'VV', 'https://example.org/after')

    def test_compatible_pair(self):
        validate_pair(self.before, self.after, self.event)

    def test_orbit_mismatch_rejected(self):
        bad = RadarScene('bad', self.after.acquired_at, 43, 'ASCENDING', 'VV', self.after.source_url)
        with self.assertRaises(ValueError): validate_pair(self.before, bad, self.event)

    def test_future_osm_rejected(self):
        with self.assertRaises(ValueError): validate_osm_snapshot(datetime(2026, 9, 1), self.event)

    def test_pre_event_osm_accepted(self):
        validate_osm_snapshot(datetime(2026, 7, 27), self.event)

if __name__ == '__main__': unittest.main()
