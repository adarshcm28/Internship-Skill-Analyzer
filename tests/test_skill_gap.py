"""Unit tests for the personal skill-gap matching rules."""

import unittest

import pandas as pd

from src.skill_gap import calculate_skill_gap, normalize_skills, rank_missing_skills, score_postings


class NormalizeSkillsTests(unittest.TestCase):
    def test_normalizes_case_whitespace_duplicates_and_nulls(self):
        values = [" python ", "PYTHON", "sql", "", "   ", None, float("nan")]
        self.assertEqual(normalize_skills(values), ["Python", "SQL"])

    def test_ignores_values_outside_catalog(self):
        self.assertEqual(normalize_skills(["Python", "Unknown Framework"]), ["Python"])

    def test_none_is_empty(self):
        self.assertEqual(normalize_skills(None), [])

    def test_rejects_ambiguous_string_input(self):
        with self.assertRaises(TypeError):
            normalize_skills("Python|SQL")


class CalculateSkillGapTests(unittest.TestCase):
    def test_partial_overlap_matches_documented_example(self):
        result = calculate_skill_gap(
            ["Python", "SQL", "Tableau"], ["Python", "SQL", "Git"]
        )
        self.assertEqual(result, {
            "matched_skills": ["Python", "SQL"],
            "missing_skills": ["Tableau"],
            "matched_count": 2,
            "required_count": 3,
            "match_percentage": 66.7,
        })

    def test_full_overlap(self):
        result = calculate_skill_gap(["SQL", "Python"], ["Python", "SQL"])
        self.assertEqual(result["match_percentage"], 100.0)
        self.assertEqual(result["missing_skills"], [])

    def test_no_user_skills(self):
        result = calculate_skill_gap(["Python", "SQL"], [])
        self.assertEqual(result["match_percentage"], 0.0)
        self.assertEqual(result["missing_skills"], ["Python", "SQL"])

    def test_no_detected_job_skills_is_unavailable(self):
        result = calculate_skill_gap([], ["Python"])
        self.assertIsNone(result["match_percentage"])
        self.assertEqual(result["required_count"], 0)
        self.assertEqual(result["matched_skills"], [])
        self.assertEqual(result["missing_skills"], [])

    def test_both_inputs_empty(self):
        self.assertIsNone(calculate_skill_gap(None, None)["match_percentage"])

    def test_inputs_are_not_modified(self):
        jobs, user = ["SQL", "Python", "SQL"], ["python"]
        calculate_skill_gap(jobs, user)
        self.assertEqual(jobs, ["SQL", "Python", "SQL"])
        self.assertEqual(user, ["python"])


class ScorePostingsTests(unittest.TestCase):
    def setUp(self):
        self.postings = pd.DataFrame([
            {"posting_id": 1, "company": "One", "skills_extracted": "Python|SQL"},
            {"posting_id": 2, "company": "Two", "skills_extracted": "Python|Tableau|AWS"},
            {"posting_id": 3, "company": "Three", "skills_extracted": ""},
        ])

    def test_scores_every_posting_without_mutating_input(self):
        original = self.postings.copy(deep=True)
        scored = score_postings(self.postings, ["Python", "SQL"])
        self.assertEqual(scored["match_percentage"].tolist()[:2], [100.0, 33.3])
        self.assertTrue(pd.isna(scored.iloc[2]["match_percentage"]))
        pd.testing.assert_frame_equal(self.postings, original)

    def test_requires_extracted_skills_column(self):
        with self.assertRaises(ValueError):
            score_postings(pd.DataFrame({"posting_id": [1]}), ["Python"])

    def test_ranks_missing_skills_by_posting_frequency(self):
        scored = score_postings(self.postings, ["Python"])
        ranked = rank_missing_skills(scored)
        self.assertEqual(ranked.to_dict("records"), [
            {"skill": "AWS", "posting_count": 1},
            {"skill": "SQL", "posting_count": 1},
            {"skill": "Tableau", "posting_count": 1},
        ])

    def test_no_missing_skills_returns_empty_contract(self):
        scored = score_postings(self.postings.iloc[:1], ["Python", "SQL"])
        self.assertEqual(list(rank_missing_skills(scored).columns), ["skill", "posting_count"])
        self.assertTrue(rank_missing_skills(scored).empty)


if __name__ == "__main__":
    unittest.main()
