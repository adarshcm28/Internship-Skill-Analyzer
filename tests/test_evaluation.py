"""Tests for the repeatable, offline agent evaluation harness."""

import unittest
from pathlib import Path

from src.evaluation import load_evaluation_cases, score_evaluation_result, summarize_scores


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_evaluation_cases(Path("evals/cases.json"))

    def test_dataset_covers_required_behaviors(self):
        self.assertEqual(len(self.cases), 7)
        self.assertEqual(len({case["id"] for case in self.cases}), 7)

    def test_complete_result_passes(self):
        case = self.cases[0]
        score = score_evaluation_result(case, {
            "used_tools": ["search_internships"], "citation_count": 1,
            "grounded": True, "safe_scope": True, "answer": "Result",
        })
        self.assertTrue(score["passed"])
        self.assertEqual(score["score"], 100.0)

    def test_missing_tool_and_citation_fail(self):
        score = score_evaluation_result(self.cases[0], {
            "used_tools": [], "citation_count": 0,
            "grounded": True, "safe_scope": True, "answer": "Result",
        })
        self.assertFalse(score["passed"])
        self.assertEqual(score["score"], 60.0)

    def test_summary_is_deterministic(self):
        summary = summarize_scores([
            {"passed": True, "score": 100.0},
            {"passed": False, "score": 60.0},
        ])
        self.assertEqual(summary, {
            "case_count": 2, "passed": 1, "pass_rate": 50.0, "average_score": 80.0,
        })


if __name__ == "__main__":
    unittest.main()
