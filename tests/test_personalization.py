"""Tests for verified, session-scoped assistant personalization."""

import json
import unittest

import pandas as pd

from src.personalization import (
    build_personalization_context,
    build_user_profile,
    profile_fingerprint,
)


class PersonalizationTests(unittest.TestCase):
    def setUp(self):
        self.postings = pd.DataFrame([
            {"posting_id": "one", "skills_extracted": "Python|SQL"},
            {"posting_id": "two", "skills_extracted": "Python|Tableau"},
            {"posting_id": "three", "skills_extracted": ""},
        ])

    def test_empty_profile_does_not_claim_calculated_matches(self):
        context = json.loads(build_personalization_context(self.postings, []))
        self.assertEqual(context["profile"]["status"], "no_skills_selected")
        self.assertEqual(context["match_summary"]["status"], "not_calculated")
        self.assertIsNone(context["match_summary"]["average_match_percentage"])

    def test_partial_match_summary_uses_deterministic_scores(self):
        context = json.loads(build_personalization_context(self.postings, ["python"]))
        self.assertEqual(context["profile"]["selected_skills"], ["Python"])
        self.assertEqual(context["match_summary"]["scored_postings"], 2)
        self.assertEqual(context["match_summary"]["average_match_percentage"], 50.0)
        self.assertEqual(context["match_summary"]["best_match_percentage"], 50.0)

    def test_complete_match_summary(self):
        one = self.postings.iloc[:1]
        context = json.loads(build_personalization_context(one, ["Python", "SQL"]))
        self.assertEqual(context["match_summary"]["average_match_percentage"], 100.0)
        self.assertEqual(context["match_summary"]["best_match_percentage"], 100.0)

    def test_unknown_skills_are_ignored_and_disclosed(self):
        profile = build_user_profile(["Python", "Unknown Tool"])
        self.assertEqual(profile["selected_skills"], ["Python"])
        self.assertEqual(profile["ignored_unknown_skills"], ["Unknown Tool"])

    def test_profile_is_marked_current_session_only(self):
        profile = build_user_profile(["SQL"])
        self.assertEqual(profile["persistence"], "current_session_only")

    def test_profile_fingerprint_is_stable_and_detects_changes(self):
        self.assertEqual(profile_fingerprint(["SQL", "Python"]),
                         profile_fingerprint(["python", "sql"]))
        self.assertNotEqual(profile_fingerprint(["Python"]), profile_fingerprint(["SQL"]))


if __name__ == "__main__":
    unittest.main()
