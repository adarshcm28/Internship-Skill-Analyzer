"""Offline checks: never send credentials or data to a live model during tests."""

import json
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from src.chatbot import answer_question, dataset_context


class ChatbotTests(unittest.TestCase):
    def test_context_counts_and_bounds(self):
        frame = pd.DataFrame([{"company": "Example", "experience_level": "Advanced",
                               "description": "x" * 2000}] * 105)
        context = json.loads(dataset_context(frame))
        self.assertEqual(context["total_postings"], 105)
        self.assertEqual(context["included_rows"], 100)
        self.assertEqual(len(context["postings"][0]["description"]), 1200)

    def test_empty_selection(self):
        context = json.loads(dataset_context(pd.DataFrame(columns=["company", "experience_level"])))
        self.assertEqual(context["postings"], [])

    @patch("src.chatbot.OpenAI")
    def test_model_request(self, client_type):
        client = MagicMock()
        client_type.return_value.__enter__.return_value = client
        client.responses.create.return_value.output_text = "Use the source listing."
        answer = answer_question("test-key", "test-model", "{}", [], "Which roles?")
        self.assertEqual(answer, "Use the source listing.")
        args = client.responses.create.call_args.kwargs
        self.assertFalse(args["store"])
        self.assertEqual(args["model"], "test-model")
        self.assertEqual(args["input"][-1]["content"], "Which roles?")


if __name__ == "__main__":
    unittest.main()
