"""Offline regression tests for US-only job collection."""

import unittest
from dataclasses import replace
from unittest.mock import patch

from src.collect_postings import (
    JobBoard, ashby_us_locations, lever_us_locations, is_us_location,
    collect_ashby, collect_lever, collect_greenhouse, collect_amazon,
    collect_workday, is_target_posting, postings_frame,
)


class USLocationTests(unittest.TestCase):
    @patch("src.collect_postings.fetch_json")
    def test_amazon_filters_country_and_role(self, fetch):
        job = {"title": "Software Development Intern", "description": "Python",
               "country_code": "USA", "location": "US, WA, Seattle",
               "job_path": "/en/jobs/1/example", "id_icims": "1"}
        fetch.return_value = {"jobs": [job, dict(job, country_code="CAN"),
            dict(job, title="Sales Intern")], "hits": 3}
        rows = collect_amazon(JobBoard("Amazon", "amazon", "amazon.jobs"), None, "2026-08-29")
        self.assertEqual([row.external_posting_id for row in rows], ["1"])

    @patch("src.collect_postings.fetch_json")
    @patch("src.collect_postings.post_json")
    def test_workday_hydrates_and_filters_country(self, post, fetch):
        post.return_value = {"jobPostings": [
            {"title": "AI Software Intern", "externalPath": "/job/us/1"},
            {"title": "Sales Intern", "externalPath": "/job/us/2"}], "total": 2}
        fetch.return_value = {"jobPostingInfo": {"jobDescription": "<p>Python</p>",
            "location": "US, Arizona, Phoenix", "country": {"descriptor": "United States of America"},
            "externalUrl": "https://example.com/1", "jobReqId": "1"}}
        board = JobBoard("Intel", "workday", "host|tenant|site")
        rows = collect_workday(board, None, "2026-08-29")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].description, "Python")

    def test_city_state(self):
        for location in ("San Francisco, CA", "Boston, MA", "Washington, DC"):
            self.assertTrue(is_us_location(location))
        for location in ("Toronto, ON", "CA", "Remote", "London, UK"):
            self.assertFalse(is_us_location(location))
        self.assertFalse(is_us_location("San Francisco, CA", "GB"))

    def test_role_matching(self):
        for title in ("Software Engineering Intern", "Data Science Internship", "Frontend Developer Co-op"):
            self.assertTrue(is_target_posting(title, "", ""))
        self.assertTrue(is_target_posting("Software Engineer", "", "Intern"))
        for title in ("Senior Software Engineer", "Graduate Data Analyst", "Sales Intern"):
            self.assertFalse(is_target_posting(title, "Mentor interns; graduate degree required", "Full-time"))

    @patch("src.collect_postings.fetch_json")
    def test_greenhouse_and_cap(self, fetch):
        base = {"title": "Software Engineer Intern", "content": "&lt;p&gt;Python &amp; SQL&lt;/p&gt;",
                "absolute_url": "https://example.com/jobs/1", "id": 1, "updated_at": "2026-08-28"}
        fetch.return_value = {"jobs": [dict(base, location={"name": "Boston, MA"}),
            dict(base, location={"name": "London, UK"}),
            dict(base, location={"name": "Remote"}, offices=[{"location": "United States"}])]}
        rows = collect_greenhouse(JobBoard("Example", "greenhouse", "example"), None, "2026-08-28")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].description, "Python & SQL")
        self.assertEqual(rows[0].published_at, "")
        self.assertEqual(len(postings_frame(rows, 5)), 1)  # Duplicate URL.
        distinct = [replace(rows[0], source_url=f"https://example.com/jobs/{i}") for i in range(8)]
        self.assertEqual(len(postings_frame(distinct, 5)), 5)

    def test_country_metadata(self):
        for country in ("US", "USA", "United States"):
            self.assertTrue(is_us_location("Remote", country))
        self.assertFalse(is_us_location("US", "CA"))

    def test_ambiguous_locations(self):
        for location in ("Remote", "Worldwide", "North America", "London", "San Francisco", ""):
            self.assertFalse(is_us_location(location))
        self.assertTrue(is_us_location("Remote - United States"))
        self.assertTrue(is_us_location("USA"))
        self.assertFalse(is_us_location("Australia"))

    def test_ashby_secondary_location(self):
        job = {"location": "London", "address": {"postalAddress": {"addressCountry": "GB"}},
               "secondaryLocations": [{"location": "New York", "address": {"addressCountry": "USA"}}]}
        self.assertEqual(ashby_us_locations(job), ["New York"])

    def test_lever_country_applies_only_to_primary(self):
        job = {"country": "US", "categories": {"location": "Boston", "allLocations": ["Boston", "London"]}}
        self.assertEqual(lever_us_locations(job), ["Boston"])
        job = {"country": "GB", "categories": {"location": "London", "allLocations": ["London", "Remote - US"]}}
        self.assertEqual(lever_us_locations(job), ["Remote - US"])

    @patch("src.collect_postings.fetch_json")
    def test_provider_filters(self, fetch):
        base = {"title": "Data Science Intern", "descriptionPlain": "Python SQL", "employmentType": "Intern", "jobUrl": "https://jobs.ashbyhq.com/example/1"}
        fetch.return_value = {"jobs": [dict(base, location="Remote"), dict(base, location="New York", address={"postalAddress": {"addressCountry": "US"}})]}
        rows = collect_ashby(JobBoard("Example", "ashby", "example"), None, "2026-08-28")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].country, "US")
        base = {"text": "Data Science Intern", "descriptionPlain": "Python SQL", "hostedUrl": "https://jobs.lever.co/example/1", "id": "1"}
        fetch.return_value = [dict(base, country="GB", categories={"location": "London"}), dict(base, country="US", categories={"location": "Boston"})]
        rows = collect_lever(JobBoard("Example", "lever", "example"), None, "2026-08-28")
        self.assertEqual([row.location for row in rows], ["Boston"])


if __name__ == "__main__":
    unittest.main()
