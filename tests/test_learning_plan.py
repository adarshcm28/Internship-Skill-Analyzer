"""Offline tests for structured personalized learning plans."""

import json
import unittest
from unittest.mock import MagicMock

import pandas as pd

from src.learning_plan import (
    build_learning_plan_evidence,
    fallback_learning_plan,
    generate_learning_plan,
    parse_learning_plan,
)


class LearningPlanTests(unittest.TestCase):
    def setUp(self):
        self.scored = pd.DataFrame([
            {"posting_id": "1", "missing_skills": ["SQL", "Tableau"]},
            {"posting_id": "2", "missing_skills": ["SQL"]},
        ])

    def test_priorities_are_deterministic_counts(self):
        evidence = build_learning_plan_evidence(self.scored, ["Python"], 2)
        self.assertEqual(evidence["missing_skill_frequencies"][0], {"skill": "SQL", "posting_count": 2})
        self.assertEqual(evidence["timeframe_weeks"], 2)

    def test_empty_gaps_are_supported(self):
        scored = pd.DataFrame([{"posting_id": "1", "missing_skills": []}])
        evidence = build_learning_plan_evidence(scored, ["Python"], 4)
        self.assertEqual(evidence["missing_skill_frequencies"], [])
        self.assertEqual(fallback_learning_plan(evidence)["data_backed_priorities"], [])

    def test_invalid_timeframe_is_rejected(self):
        with self.assertRaises(ValueError):
            build_learning_plan_evidence(self.scored, ["Python"], 3)

    def test_malformed_output_uses_fallback(self):
        evidence = build_learning_plan_evidence(self.scored, ["Python"], 2)
        client = MagicMock()
        client.responses.create.return_value.output_text = "not-json"
        factory = MagicMock()
        factory.return_value.__enter__.return_value = client
        plan, used_fallback = generate_learning_plan("key", "model", evidence, factory)
        self.assertTrue(used_fallback)
        self.assertEqual(plan["timeframe_weeks"], 2)
        self.assertIn("does not guarantee", plan["limitations"])
        self.assertFalse(client.responses.create.call_args.kwargs["store"])
        self.assertEqual(
            client.responses.create.call_args.kwargs["text"]["format"]["type"],
            "json_schema",
        )

    def test_valid_plan_is_parsed(self):
        evidence = build_learning_plan_evidence(self.scored, ["Python"], 2)
        plan = fallback_learning_plan(evidence)
        self.assertEqual(parse_learning_plan(json.dumps(plan), 2), plan)
