"""Tests for VARUNA Situation-Report Copilot Engine.

Multimodal AI Hackathon 2026 — Track B AI Component Verification.
Verifies:
1. English and Nepali question answering with quantitative grounding.
2. Anti-hallucination guard against unsupported requests (casualties, ground deaths, economic cost).
3. Zero tolerance for invented/unverified numbers.
4. Bilingual situation briefing generation.
5. FastAPI integration endpoints.
"""

import unittest
from fastapi.testclient import TestClient

from varuna.copilot.engine import (
    FactBase,
    GroundingFact,
    SituationReportCopilot,
    Language,
)
from varuna.api.main import app


class TestCopilotEngine(unittest.TestCase):
    def setUp(self):
        self.copilot = SituationReportCopilot()
        self.client = TestClient(app)

    def test_english_inundation_query_grounded(self):
        """Querying flood inundation extent returns exact computed figures."""
        resp = self.copilot.answer_query("What is the total flood inundation and debris extent?", language=Language.ENGLISH)
        self.assertTrue(resp.grounded)
        self.assertFalse(resp.unsupported_topic_flag)
        self.assertIn("126.60", resp.answer)
        self.assertIn("108.21", resp.answer)
        self.assertIn("flood_inundation_km2", resp.grounding_facts_used)
        self.assertIn("surface_debris_km2", resp.grounding_facts_used)

    def test_english_road_network_exposure_query(self):
        """Querying road network exposure returns exact 35.12 km and zero double-counting."""
        resp = self.copilot.answer_query("How many kilometers of roads and highways are cut off?", language=Language.ENGLISH)
        self.assertTrue(resp.grounded)
        self.assertIn("35.12", resp.answer)
        self.assertIn("9.62", resp.answer)
        self.assertIn("0.00", resp.answer)
        self.assertIn("Pasang Lhamu", resp.answer)

    def test_english_compound_query_flood_and_roads(self):
        """Compound query answering both floodwater extent and exposed road length."""
        resp = self.copilot.answer_query(
            "What is the total floodwater extent and how many kilometers of roads are exposed?",
            language=Language.ENGLISH
        )
        self.assertTrue(resp.grounded)
        self.assertFalse(resp.unsupported_topic_flag)
        self.assertIn("126.60", resp.answer)
        self.assertIn("35.12", resp.answer)
        self.assertIn("flood_inundation_km2", resp.grounding_facts_used)
        self.assertIn("exposed_roads_km", resp.grounding_facts_used)
        self.assertNotIn("[Grounded verification notice", resp.answer)

    def test_nepali_compound_query_flood_and_roads(self):
        """Nepali compound query returning both floodwater extent and exposed road length."""
        resp = self.copilot.answer_query(
            "कुल बाढीको क्षेत्रफल कति छ र कति किलोमिटर सडक जोखिममा परेको छ?",
            language=Language.NEPALI
        )
        self.assertTrue(resp.grounded)
        self.assertFalse(resp.unsupported_topic_flag)
        self.assertTrue("१२६.६०" in resp.answer or "126.60" in resp.answer)
        self.assertTrue("३५.१२" in resp.answer or "35.12" in resp.answer)
        self.assertIn("flood_inundation_km2", resp.grounding_facts_used)
        self.assertIn("exposed_roads_km", resp.grounding_facts_used)
        self.assertNotIn("[Grounded verification notice", resp.answer)

    def test_compound_query_buildings_and_settlements(self):
        """Compound query for infrastructure buildings and isolated settlements."""
        resp = self.copilot.answer_query(
            "How many buildings are exposed and which settlements are isolated?",
            language=Language.ENGLISH
        )
        self.assertTrue(resp.grounded)
        self.assertIn("1,062", resp.answer)
        self.assertIn("Syaphrubesi", resp.answer)
        self.assertIn("Mailung", resp.answer)
        self.assertIn("exposed_buildings_count", resp.grounding_facts_used)
        self.assertIn("isolated_settlements_count", resp.grounding_facts_used)

    def test_isolated_settlements_and_hospital_reachability(self):
        """Querying isolated villages returns settlements cut off from Nuwakot District Hospital."""
        resp = self.copilot.answer_query("Which settlements are cut off and can they reach the nearest hospital?", language=Language.ENGLISH)
        self.assertTrue(resp.grounded)
        self.assertIn("Syaphrubesi", resp.answer)
        self.assertIn("Mailung", resp.answer)
        self.assertIn("Nuwakot District Hospital", resp.answer)
        self.assertIn("isolated_settlements_count", resp.grounding_facts_used)

    def test_nepali_language_query_grounded(self):
        """Querying in Nepali returns authentic Devanagari text with grounded metrics."""
        resp = self.copilot.answer_query("बाढीले कति सडक अवरुद्ध भएको छ र कुन बस्तीहरू सम्पर्कविहीन छन्?", language=Language.NEPALI)
        self.assertTrue(resp.grounded)
        self.assertEqual(resp.language, "ne")
        # Check Devanagari numerals or standard numerals for road length and settlements
        self.assertTrue("३५.१२" in resp.answer or "35.12" in resp.answer)
        self.assertTrue("स्याफ्रुबेसी" in resp.answer)
        self.assertTrue("मैलुङ" in resp.answer)
        self.assertFalse(resp.unsupported_topic_flag)

    def test_unsupported_casualties_query_strictly_refused(self):
        """Asking for ground casualties/deaths must NOT invent numbers and must cite NDRRMA."""
        resp = self.copilot.answer_query("How many people died or were injured in the flood?", language=Language.ENGLISH)
        self.assertTrue(resp.unsupported_topic_flag)
        self.assertIsNotNone(resp.refusal_reason)
        self.assertIn("NDRRMA", resp.answer)
        self.assertIn("cannot be directly observed", resp.answer)
        # Must not fabricate a casualty count
        self.assertEqual(resp.grounding_facts_used, [])

    def test_unsupported_nepali_casualties_query_strictly_refused(self):
        """Asking for death toll in Nepali must trigger refusal with NDRRMA reference."""
        resp = self.copilot.answer_query("बाढीमा कति जनाको मृत्यु भयो र कति घाइते भए?", language=Language.NEPALI)
        self.assertTrue(resp.unsupported_topic_flag)
        self.assertIn("NDRRMA", resp.answer)
        self.assertIn("मानवीय क्षति", resp.answer)

    def test_orbit_comparison_telemetry_grounded(self):
        """Querying orbit 19 vs 85 telemetry explains 10-day lag and recession implications."""
        resp = self.copilot.answer_query("Why did you select orbit 19 instead of orbit 85 and what is the lag?", language=Language.ENGLISH)
        self.assertTrue(resp.grounded)
        self.assertIn("Orbit 19", resp.answer)
        self.assertIn("Orbit 85", resp.answer)
        self.assertIn("10", resp.answer)

    def test_numeric_grounding_rejects_hallucinated_number(self):
        """Validator rejects arbitrary fabricated statistics."""
        hallucinated_text = "The system observed 98765.43 km of submerged tunnels and 123456 casualties."
        is_grounded, ungrounded = self.copilot.verify_numeric_grounding(hallucinated_text)
        self.assertFalse(is_grounded)
        self.assertIn("98765.43", ungrounded)
        self.assertIn("123456", ungrounded)

    def test_situation_briefing_generation_en_and_ne(self):
        """Generates comprehensive bilingual situation reports with mandatory attributions."""
        brief_en = self.copilot.generate_situation_briefing(language=Language.ENGLISH)
        self.assertEqual(brief_en.language, "en")
        self.assertIn("126.60 km²", brief_en.raw_markdown)
        self.assertIn("35.12 km", brief_en.raw_markdown)
        self.assertIn("Contains modified Copernicus Sentinel data 2026.", brief_en.raw_markdown)
        self.assertIn("© OpenStreetMap contributors.", brief_en.raw_markdown)

        brief_ne = self.copilot.generate_situation_briefing(language=Language.NEPALI)
        self.assertEqual(brief_ne.language, "ne")
        self.assertIn("१२६.६० वर्ग किमी", brief_ne.raw_markdown)
        self.assertIn("स्याफ्रुबेसी", brief_ne.raw_markdown)
        self.assertIn("Contains modified Copernicus Sentinel data 2026.", brief_ne.raw_markdown)

    def test_api_copilot_query_endpoint(self):
        """FastAPI POST /api/v1/copilot/query returns grounded response."""
        res = self.client.post("/api/v1/copilot/query", json={
            "query": "What is the road exposure in the Trishuli corridor?",
            "language": "en"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["grounded"])
        self.assertIn("35.12", data["answer"])

    def test_api_copilot_report_endpoint(self):
        """FastAPI POST /api/v1/copilot/report returns structured situation report."""
        res = self.client.post("/api/v1/copilot/report", json={
            "language": "ne"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["language"], "ne")
        self.assertIn("वरुणा", data["title"])
        self.assertIn("raw_markdown", data)


if __name__ == "__main__":
    unittest.main()
