"""Offline tests for the Internship Assistant's read-only tools."""

import unittest

import pandas as pd

from src.agent_tools import (
    SEARCH_INTERNSHIPS_TOOL,
    SKILL_GAP_TOOL,
    analyze_skill_gap_tool,
    dispatch_tool_call,
    search_internships_tool,
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


class InternshipSearchToolTests(unittest.TestCase):
    def setUp(self):
        self.postings = pd.DataFrame([
            {"posting_id": "1", "company": "Alpha", "job_title": "Data Intern",
             "location": "Phoenix, AZ, US", "experience_level": "Beginner-friendly",
             "skills_extracted": "Python|SQL", "source_url": "https://example.com/1"},
            {"posting_id": "2", "company": "Beta", "job_title": "ML Intern",
             "location": "Seattle, WA, US", "experience_level": "Advanced",
             "skills_extracted": "Python|Machine Learning", "source_url": "https://example.com/2"},
            {"posting_id": "3", "company": "Alpha", "job_title": "Analytics Intern",
             "location": "Remote - US", "experience_level": "Beginner-friendly",
             "skills_extracted": "SQL|Tableau", "source_url": "not-a-url"},
        ])

    def test_search_schema_is_strict_and_capped(self):
        self.assertTrue(SEARCH_INTERNSHIPS_TOOL["strict"])
        self.assertFalse(SEARCH_INTERNSHIPS_TOOL["parameters"]["additionalProperties"])
        self.assertEqual(SEARCH_INTERNSHIPS_TOOL["parameters"]["properties"]["limit"]["maximum"], 10)

    def test_each_text_and_difficulty_filter(self):
        company = search_internships_tool(self.postings, ["Python"], company="alpha")
        self.assertEqual(company["total_matches"], 2)
        title = search_internships_tool(self.postings, ["Python"], job_title="ML")
        self.assertEqual(title["results"][0]["posting_id"], "2")
        location = search_internships_tool(self.postings, ["Python"], location="Phoenix")
        self.assertEqual(location["results"][0]["posting_id"], "1")
        difficulty = search_internships_tool(
            self.postings, ["Python"], difficulty="Advanced"
        )
        self.assertEqual(difficulty["results"][0]["posting_id"], "2")

    def test_combined_skills_overlap_and_limit(self):
        result = search_internships_tool(
            self.postings, ["Python"], skills=["Python"],
            minimum_skill_overlap=50, limit=1,
        )
        self.assertEqual(result["total_matches"], 2)
        self.assertEqual(result["returned_count"], 1)
        self.assertEqual(result["results"][0]["match_percentage"], 50.0)

    def test_empty_result_is_success(self):
        result = search_internships_tool(self.postings, ["Python"], company="Missing")
        self.assertTrue(result["ok"])
        self.assertEqual(result["results"], [])

    def test_invalid_values_are_safe_errors(self):
        self.assertEqual(
            search_internships_tool(self.postings, ["Python"], skills=["ImaginaryDB"])["error"]["code"],
            "unknown_skills",
        )
        self.assertEqual(
            search_internships_tool(self.postings, [], minimum_skill_overlap=20)["error"]["code"],
            "no_user_skills",
        )
        self.assertEqual(
            search_internships_tool(self.postings, ["Python"], limit=11)["error"]["code"],
            "invalid_limit",
        )

    def test_dispatches_complete_search_arguments(self):
        arguments = (
            '{"company":null,"job_title":"Data","location":null,"skills":[],'
            '"difficulty":null,"minimum_skill_overlap":null,"limit":5}'
        )
        result = dispatch_tool_call("search_internships", arguments, self.postings, ["Python"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["results"][0]["posting_id"], "1")


if __name__ == "__main__":
    unittest.main()
