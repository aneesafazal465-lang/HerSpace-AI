"""Tests for ai_service.py. No internet and no real API key are needed."""

import os
import unittest
from unittest import mock

import ai_service as ai


class FakeAPIError(Exception):
    def __init__(self, code, message="secret-details-sk-12345"):
        super().__init__(message)
        self.code = code


class NoKeyTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL"):
            os.environ.pop(name, None)

    def test_not_configured_without_key(self):
        self.assertFalse(ai.is_configured())

    def test_placeholder_key_counts_as_missing(self):
        os.environ["GEMINI_API_KEY"] = "YOUR_GEMINI_API_KEY_HERE"
        self.assertFalse(ai.is_configured())

    def test_generate_text_without_key_raises_friendly_error(self):
        with self.assertRaises(ai.AIError) as ctx:
            ai.generate_text("hello")
        self.assertIn("not set up", str(ctx.exception))

    def test_every_feature_fails_gracefully_without_key(self):
        calls = [
            lambda: ai.chat_reply([], "hi"),
            lambda: ai.journaling_prompts(""),
            lambda: ai.reflect_on_entry("t", "c", "Happy"),
            lambda: ai.summarize_entry("t", "c"),
            lambda: ai.selfcare_suggestions(""),
            lambda: ai.new_affirmation(),
            lambda: ai.goal_plan("g", "d", 0, "", None, ""),
        ]
        for call in calls:
            with self.assertRaises(ai.AIError):
                call()

    def test_default_model_and_override(self):
        self.assertEqual(ai.get_model_name(), ai.DEFAULT_MODEL)
        os.environ["GEMINI_MODEL"] = "my-model"
        self.assertEqual(ai.get_model_name(), "my-model")

    def test_local_collections_are_available(self):
        self.assertGreater(len(ai.LOCAL_AFFIRMATIONS), 10)
        self.assertGreaterEqual(len(ai.LOCAL_JOURNAL_PROMPTS), 5)


class ErrorHandlingTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-123"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_success(self):
        with mock.patch.object(ai, "_call_model", return_value="  Hello!  "):
            self.assertEqual(ai.generate_text("hi"), "Hello!")

    def test_empty_response(self):
        with mock.patch.object(ai, "_call_model", return_value="   "):
            with self.assertRaises(ai.AIError) as ctx:
                ai.generate_text("hi")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_error_codes_become_friendly_messages(self):
        expectations = {401: "API key", 403: "API key", 429: "rate limit", 404: "model",
                        400: "could not process", 503: "temporary problem"}
        for code, expected in expectations.items():
            with mock.patch.object(ai, "_call_model", side_effect=FakeAPIError(code)):
                with self.assertRaises(ai.AIError) as ctx:
                    ai.generate_text("hi")
            self.assertIn(expected.lower(), str(ctx.exception).lower(), f"code {code}")

    def test_network_error(self):
        with mock.patch.object(ai, "_call_model", side_effect=ConnectionError("boom")):
            with self.assertRaises(ai.AIError) as ctx:
                ai.generate_text("hi")
        self.assertIn("internet", str(ctx.exception).lower())

    def test_raw_error_text_and_key_never_leak(self):
        with mock.patch.object(ai, "_call_model", side_effect=FakeAPIError(500, "key=fake-test-key-123")):
            with self.assertRaises(ai.AIError) as ctx:
                ai.generate_text("hi")
        self.assertNotIn("fake-test-key-123", str(ctx.exception))
        self.assertNotIn("secret-details", str(ctx.exception))

    def test_unknown_error(self):
        with mock.patch.object(ai, "_call_model", side_effect=RuntimeError("weird")):
            with self.assertRaises(ai.AIError):
                ai.generate_text("hi")


class PlanParsingTests(unittest.TestCase):
    GOOD = ('{"summary": "S", "steps": ["a", "b"], "timeline": "4 weeks", '
            '"weekly_milestones": ["Week 1: x"], "checklist": ["one", "two"], "encouragement": "You can!"}')

    def test_plain_and_fenced_json(self):
        self.assertEqual(ai.normalize_plan(ai._extract_json(self.GOOD))["summary"], "S")
        fenced = "```json\n" + self.GOOD + "\n```"
        self.assertEqual(ai.normalize_plan(ai._extract_json(fenced))["steps"], ["a", "b"])
        chatty = "Here you go: " + self.GOOD + " Hope it helps!"
        self.assertEqual(ai._extract_json(chatty)["timeline"], "4 weeks")

    def test_bad_json_raises_ai_error(self):
        with self.assertRaises(ai.AIError):
            ai._extract_json("not json at all")

    def test_missing_keys_are_filled(self):
        plan = ai.normalize_plan({"summary": "Only a summary", "steps": "single step"})
        self.assertEqual(plan["steps"], ["single step"])
        self.assertEqual(plan["checklist"], [])

    def test_empty_plan_rejected(self):
        with self.assertRaises(ai.AIError):
            ai.normalize_plan({})

    def test_goal_plan_end_to_end_with_mock(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}), \
             mock.patch.object(ai, "_call_model", return_value=self.GOOD) as fake:
            plan = ai.goal_plan("Learn", "desc", 10, "30 min", "2026-12-01", "")
        self.assertEqual(plan["checklist"], ["one", "two"])
        self.assertTrue(fake.call_args[0][2])  # JSON mode was requested

    def test_new_affirmation_strips_quotes(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}), \
             mock.patch.object(ai, "_call_model", return_value='"I am enough."'):
            self.assertEqual(ai.new_affirmation(), "I am enough.")

    def test_chat_history_is_trimmed_and_roles_mapped(self):
        history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(30)]
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}), \
             mock.patch.object(ai, "_call_model", return_value="ok") as fake:
            ai.chat_reply(history, "latest")
        sent = fake.call_args[0][0]
        self.assertEqual(len(sent), ai.MAX_CHAT_MESSAGES + 1)
        self.assertEqual(sent[-1], {"role": "user", "text": "latest"})
        self.assertTrue(all(item["role"] in ("user", "model") for item in sent))


if __name__ == "__main__":
    unittest.main()
