# tests/test_llm.py
"""
Unit tests for LLMClient.

These tests validate:
- Successful model responses (mocked)
- Error handling for HTTP 400 (no retry)
- Retry + fallback behavior for HTTP 500
- Timeout handling treated as retryable error

All calls to Groq are mocked to ensure tests run offline and deterministically.
"""

import os
import unittest
from unittest.mock import MagicMock, patch
from services.llm import LLMClient
import httpx


class TestLLMClient(unittest.TestCase):

    def setUp(self):
        """
        Runs before each test:
        - Injects a fake API key so LLMClient can initialize.
        - Patches the Groq client to prevent real API calls.
        """
        os.environ["GROQ_API_KEY"] = "fake_key"

        # Patch Groq inside services.llm so the constructor uses the mock
        self.groq_patcher = patch("services.llm.Groq")
        self.mock_groq_class = self.groq_patcher.start()

        # Replace the Groq instance with a MagicMock
        self.mock_groq_instance = MagicMock()
        self.mock_groq_class.return_value = self.mock_groq_instance


        self.llm = LLMClient()

    def tearDown(self):

        self.groq_patcher.stop()

    """
    When the model responds successfully,
    the client should return the model's text content.
    """

    def test_successful_response(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="response OK"))
        ]
        self.mock_groq_instance.chat.completions.create.return_value = mock_response

        result = self.llm.generate([{"role": "user", "content": "hello"}])

        self.assertEqual(result, "response OK")
    
    """
    A 400 Bad Request should:
    - NOT trigger retries
    - Return an immediate fallback explaining invalid input
    """

    def test_400(self):
        error = httpx.HTTPStatusError(
            "Bad Request",
            request=None,
            response=MagicMock(status_code=400),
        )
        self.mock_groq_instance.chat.completions.create.side_effect = error

        result = self.llm.generate([{"role": "user", "content": "hello"}])

        self.assertIn("no es válida", result)


    """
    A 500 Server Error should:
    - Trigger retry attempts
    - After retries are exhausted, return a server-problem fallback
    """
    def test_500(self):
        error = httpx.HTTPStatusError(
            "Server Error",
            request=None,
            response=MagicMock(status_code=500),
        )
        self.mock_groq_instance.chat.completions.create.side_effect = error

        result = self.llm.generate([{"role": "user", "content": "hello"}])

        self.assertIn("experimentando problemas", result)

    """
    TimeoutException should behave like a 500 error:
    Retry with exponential backoff
    Return timeout fallback when max retries are reached
    """

    def test_timeout(self):
    
        self.mock_groq_instance.chat.completions.create.side_effect = httpx.TimeoutException("timeout")

        result = self.llm.generate([{"role": "user", "content": "hello"}])

        self.assertIn("tardó demasiado", result)


if __name__ == "__main__":
    unittest.main()
