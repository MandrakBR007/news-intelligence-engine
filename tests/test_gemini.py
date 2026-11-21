import os
import types
import unittest
from unittest import mock

from news_engine import gemini_client


class GeminiTests(unittest.TestCase):
    def test_disabled_without_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(gemini_client.enabled())
            result = gemini_client.review("Title", "Summary")
            self.assertFalse(result["enabled"])
            self.assertIn("GEMINI_API_KEY", result["reason"])

    def test_public_decision_api_contract_with_fake_client(self):
        captured = {}
        def call(**kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(answers={
                "category": types.SimpleNamespace(choice="economy", confidence=0.7,
                                                   probabilities={"economy": 0.7, "other": 0.3}),
                "text_sufficient": types.SimpleNamespace(noul=0.9, confidence=0.9),
            })
        fake = types.SimpleNamespace(decisions=types.SimpleNamespace(create=call))
        result = gemini_client.review("Synthetic economic report", "Synthetic summary", client=fake)
        self.assertEqual(captured["model"], "gemini-decision-1")
        self.assertIn("category", captured["questions"])
        self.assertEqual(result["answers"]["category"]["choice"], "economy")
        self.assertEqual(result["answers"]["text_sufficient"]["noul"], 0.9)


if __name__ == "__main__":
    unittest.main()
