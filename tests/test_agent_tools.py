"""Offline tests for the Internship Assistant's read-only tools."""

import unittest

import pandas as pd

from src.agent_tools import (
    COMPARE_INTERNSHIPS_TOOL,
    MARKET_INSIGHTS_TOOL,
    SEARCH_INTERNSHIPS_TOOL,
    SKILL_GAP_TOOL,
    analyze_skill_gap_tool,
    compare_internships_tool,
    dispatch_tool_call,
    market_insights_tool,
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


class ComparisonToolTests(unittest.TestCase):
    def setUp(self):
        self.postings = pd.DataFrame([
            {"posting_id": "1", "company": "Alpha", "job_title": "Data Intern",
             "location": "Phoenix", "skills_extracted": "Python|SQL",
             "source_url": "https://example.com/1"},
            {"posting_id": "2", "company": "Beta", "job_title": "ML Intern",
             "location": "Seattle", "skills_extracted": "Python|Machine Learning",
             "source_url": "https://example.com/2"},
            {"posting_id": "3", "company": "Gamma", "job_title": "BI Intern",
             "location": "", "skills_extracted": "SQL|Tableau", "source_url": ""},
        ])

    def test_schema_accepts_two_or_three_ids(self):
        items = COMPARE_INTERNSHIPS_TOOL["parameters"]["properties"]["posting_ids"]
        self.assertEqual((items["minItems"], items["maxItems"]), (2, 3))
        self.assertTrue(COMPARE_INTERNSHIPS_TOOL["strict"])

    def test_two_postings_preserve_order_and_calculations(self):
        result = compare_internships_tool(self.postings, ["2", "1"], ["Python"])
        self.assertTrue(result["ok"])
        self.assertEqual([row["posting_id"] for row in result["postings"]], ["2", "1"])
        self.assertEqual(result["shared_skills"], ["Python"])
        self.assertEqual(result["postings"][0]["unique_skills"], ["Machine Learning"])
        self.assertEqual(result["postings"][1]["missing_skills"], ["SQL"])

    def test_three_postings_and_incomplete_optional_fields(self):
        result = compare_internships_tool(self.postings, ["1", "2", "3"], ["SQL"])
        self.assertEqual(result["posting_count"], 3)
        self.assertEqual(result["shared_skills"], [])
        self.assertEqual(result["postings"][2]["location"], "")

    def test_missing_and_duplicate_ids_are_rejected(self):
        duplicate = compare_internships_tool(self.postings, ["1", "1"], [])
        self.assertEqual(duplicate["error"]["code"], "duplicate_posting_ids")
        missing = compare_internships_tool(self.postings, ["1", "missing"], [])
        self.assertEqual(missing["error"]["code"], "posting_not_found")


class MarketInsightsToolTests(unittest.TestCase):
    def setUp(self):
        self.postings = pd.DataFrame([
            {"posting_id": "1", "company": "Alpha", "location": "Phoenix",
             "experience_level": "Beginner-friendly", "skills_extracted": "Python|SQL"},
            {"posting_id": "2", "company": "Beta", "location": "Seattle",
             "experience_level": "Advanced", "skills_extracted": "Python|Tableau"},
            {"posting_id": "3", "company": "Alpha", "location": "Phoenix",
             "experience_level": "Beginner-friendly", "skills_extracted": "SQL|Tableau"},
        ])

    def test_schema_is_strict(self):
        self.assertTrue(MARKET_INSIGHTS_TOOL["strict"])
        self.assertFalse(MARKET_INSIGHTS_TOOL["parameters"]["additionalProperties"])

    def test_counts_use_current_selection(self):
        result = market_insights_tool(self.postings.iloc[:2], "counts", 10)
        self.assertEqual(result["selection_posting_count"], 2)
        self.assertEqual(result["values"]["companies"], 2)

    def test_top_skills_ties_are_stable(self):
        result = market_insights_tool(self.postings, "top_skills", 2)
        self.assertEqual(result["values"], [
            {"skill": "Python", "posting_count": 2},
            {"skill": "SQL", "posting_count": 2},
        ])

    def test_category_and_difficulty_distributions(self):
        categories = market_insights_tool(self.postings, "category_distribution", 10)
        self.assertEqual(categories["values"][0]["category"], "Programming Languages")
        difficulty = market_insights_tool(self.postings, "difficulty_distribution", 10)
        self.assertEqual(difficulty["values"][0], {
            "difficulty": "Beginner-friendly", "posting_count": 2,
        })

    def test_empty_dataset_has_empty_top_skills(self):
        result = market_insights_tool(self.postings.iloc[0:0], "top_skills", 5)
        self.assertTrue(result["ok"])
        self.assertEqual(result["selection_posting_count"], 0)
        self.assertEqual(result["values"], [])


if __name__ == "__main__":
    unittest.main()
