"""Offline tests for deterministic Internship Assistant retrieval."""

import json
import unittest

import pandas as pd

from src.retrieval import (
    build_retrieval_context,
    query_terms,
    rank_postings,
    selection_fingerprint,
)


def posting(posting_id, company, title, skills="", description="", url=""):
    return {
        "posting_id": posting_id,
        "company": company,
        "job_title": title,
        "location": "Phoenix, AZ",
        "skills_extracted": skills,
        "experience_level": "Beginner-friendly",
        "source_url": url,
        "date_collected": "2026-09-08",
        "description": description,
    }


class RetrievalTests(unittest.TestCase):
    def test_query_terms_remove_noise_and_duplicates(self):
        self.assertEqual(query_terms("Which internships mention Python and PYTHON SQL?"),
                         ["python", "sql"])

    def test_title_and_skill_matches_rank_above_description_only(self):
        frame = pd.DataFrame([
            posting("description", "A", "Data Intern", description="Uses Python"),
            posting("skill", "B", "Data Intern", skills="Python|SQL"),
            posting("title", "C", "Python Engineering Intern"),
        ])
        ranked = rank_postings(frame, "Python roles")
        self.assertEqual(ranked["posting_id"].tolist(), ["title", "skill", "description"])

    def test_context_contains_only_relevant_rows_and_citation_data(self):
        frame = pd.DataFrame([
            posting("python-role", "A", "Data Intern", skills="Python",
                    url="https://example.com/python"),
            posting("java-role", "B", "Software Intern", skills="Java",
                    url="https://example.com/java"),
        ])
        context = json.loads(build_retrieval_context(frame, "Which roles require Python?"))
        self.assertEqual(context["retrieval"]["strategy"], "lexical_relevance")
        self.assertEqual([item["citation_id"] for item in context["postings"]], ["python-role"])
        self.assertEqual(context["postings"][0]["source_url"], "https://example.com/python")

    def test_scored_match_facts_are_preserved_for_retrieved_posting(self):
        frame = pd.DataFrame([{
            **posting("python-role", "A", "Python Intern", skills="Python|SQL"),
            "match_percentage": 50.0,
            "matched_skills": ["Python"],
            "missing_skills": ["SQL"],
            "matched_count": 1,
            "required_count": 2,
        }])
        context = json.loads(build_retrieval_context(frame, "Python"))
        result = context["postings"][0]
        self.assertEqual(result["match_percentage"], 50.0)
        self.assertEqual(result["matched_skills"], ["Python"])
        self.assertEqual(result["missing_skills"], ["SQL"])

    def test_no_match_uses_bounded_representative_fallback(self):
        frame = pd.DataFrame([posting(str(index), "A", f"Role {index}") for index in range(20)])
        context = json.loads(build_retrieval_context(frame, "Explain difficulty", max_postings=4))
        self.assertEqual(context["retrieval"]["strategy"], "representative_fallback")
        self.assertEqual(len(context["postings"]), 4)

    def test_duplicate_ids_are_removed_and_missing_ids_are_stable(self):
        rows = [
            posting("duplicate", "A", "First"),
            posting("duplicate", "A", "Second"),
            posting("", "B", "No ID", url="https://example.com/no-id"),
        ]
        first = rank_postings(pd.DataFrame(rows), "")
        second = rank_postings(pd.DataFrame(rows), "")
        self.assertEqual(len(first), 2)
        self.assertEqual(first["citation_id"].tolist(), second["citation_id"].tolist())
        self.assertTrue(first.iloc[1]["citation_id"].startswith("posting-"))

    def test_invalid_source_url_is_removed(self):
        frame = pd.DataFrame([posting("unsafe", "A", "Role", url="javascript:alert(1)")])
        context = json.loads(build_retrieval_context(frame, "role"))
        self.assertEqual(context["postings"][0]["source_url"], "")

    def test_description_and_total_context_are_bounded(self):
        frame = pd.DataFrame([
            posting(str(index), "A", "Python Role", description="x" * 2000)
            for index in range(30)
        ])
        encoded = build_retrieval_context(
            frame, "Python", max_postings=10, description_chars=200, max_context_chars=4_000
        )
        context = json.loads(encoded)
        self.assertLessEqual(len(encoded), 4_000)
        self.assertLessEqual(len(context["postings"]), 10)
        self.assertTrue(all(len(item["description"]) <= 200 for item in context["postings"]))

    def test_empty_and_incomplete_data_is_safe(self):
        context = json.loads(build_retrieval_context(pd.DataFrame([{"company": None}]), "Python"))
        self.assertEqual(context["total_postings"], 1)
        self.assertEqual(context["postings"][0]["source_url"], "")
        self.assertTrue(context["postings"][0]["citation_id"].startswith("posting-"))

    def test_selection_fingerprint_is_order_independent_but_detects_change(self):
        first = pd.DataFrame([
            posting("one", "A", "One", url="https://example.com/1"),
            posting("two", "B", "Two", url="https://example.com/2"),
        ])
        self.assertEqual(selection_fingerprint(first), selection_fingerprint(first.iloc[::-1]))
        self.assertNotEqual(selection_fingerprint(first), selection_fingerprint(first.iloc[:1]))


if __name__ == "__main__":
    unittest.main()
