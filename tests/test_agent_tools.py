"""Offline tests for the Internship Assistant's read-only tools."""

import unittest

import pandas as pd

from src.agent_tools import (
    SKILL_GAP_TOOL,
    analyze_skill_gap_tool,
    dispatch_tool_call,
)


class SkillGapToolTests(unittest.TestCase):
    def setUp(self):
        self.postings = pd.DataFrame([{
            "posting_id": "job-1",
            "company": "Example Company",
            "job_title": "Data Intern",
            "skills_extracted": "Python|SQL|Tableau",
        }])

    def test_schema_is_strict_and_accepts_only_posting_id(self):
        self.assertTrue(SKILL_GAP_TOOL["strict"])
        parameters = SKILL_GAP_TOOL["parameters"]
        self.assertEqual(parameters["required"], ["posting_id"])
        self.assertFalse(parameters["additionalProperties"])

    def test_verified_partial_match(self):
        result = analyze_skill_gap_tool(self.postings, "job-1", ["Python", "SQL"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["company"], "Example Company")
        self.assertEqual(result["calculation"]["match_percentage"], 66.7)
        self.assertEqual(result["calculation"]["matched_skills"], ["Python", "SQL"])
        self.assertEqual(result["calculation"]["missing_skills"], ["Tableau"])
        self.assertEqual(result["calculation"]["matched_count"], 2)
        self.assertEqual(result["calculation"]["required_count"], 3)

    def test_unknown_posting_is_safe_error(self):
        result = analyze_skill_gap_tool(self.postings, "missing", ["Python"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "posting_not_found")

    def test_unknown_profile_skill_is_safe_error(self):
        result = analyze_skill_gap_tool(self.postings, "job-1", ["Python", "ImaginaryDB"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "unknown_user_skills")

    def test_empty_profile_requests_skill_selection(self):
        result = analyze_skill_gap_tool(self.postings, "job-1", [])
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "no_user_skills")

    def test_empty_posting_id_is_safe_error(self):
        result = analyze_skill_gap_tool(self.postings, "", ["Python"])
        self.assertEqual(result["error"]["code"], "invalid_posting_id")

    def test_duplicate_posting_id_is_rejected(self):
        duplicate = pd.concat([self.postings, self.postings], ignore_index=True)
        result = analyze_skill_gap_tool(duplicate, "job-1", ["Python"])
        self.assertEqual(result["error"]["code"], "duplicate_posting_id")

    def test_malformed_arguments_are_safe_error(self):
        result = dispatch_tool_call("analyze_skill_gap", "not json", self.postings, ["Python"])
        self.assertEqual(result["error"]["code"], "invalid_arguments")
        extra = dispatch_tool_call(
            "analyze_skill_gap", '{"posting_id":"job-1","extra":true}',
            self.postings, ["Python"],
        )
        self.assertEqual(extra["error"]["code"], "invalid_arguments")

    def test_unknown_tool_is_not_executed(self):
        result = dispatch_tool_call("delete_posting", "{}", self.postings, ["Python"])
        self.assertEqual(result["error"]["code"], "unknown_tool")


if __name__ == "__main__":
    unittest.main()
