"""VARUNA Situation-Report Copilot Engine.

Multimodal AI Hackathon 2026 — Track B AI Component.
Evidence-grounded assistant for answering rescue operations queries and
generating situation reports in English and Nepali, with strict numeric
grounding and anti-hallucination controls.
"""

from varuna.copilot.engine import (
    GroundingFact,
    FactBase,
    SituationReportCopilot,
    CopilotQueryResponse,
    SituationBriefing,
)

__all__ = [
    "GroundingFact",
    "FactBase",
    "SituationReportCopilot",
    "CopilotQueryResponse",
    "SituationBriefing",
]
