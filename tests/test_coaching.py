"""Tests for job-specific coaching requests."""

import unittest

from src.coaching import build_coaching_question


class CoachingTests(unittest.TestCase):
    def test_request_uses_stable_job_facts_and_required_sections(self):
        question = build_coaching_question({
            "posting_id": "job-42", "company": "Example", "job_title": "Data Intern"
        })
        self.assertIn("job-42", question)
        self.assertIn("Data Intern at Example", question)
        self.assertIn("verified skill-gap tool", question)
        self.assertIn("questions I should research", question)
        self.assertIn("original posting source", question)
