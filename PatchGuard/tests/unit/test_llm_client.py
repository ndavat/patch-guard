"""Tests for LLMClient — written BEFORE implementation (TDD RED)."""
import pytest
from unittest.mock import Mock, patch


class TestLLMClient:
    """Test the LLMClient."""

    def test_generate_fix_returns_diff(self):
        from patchguard.generators.llm_client import LLMClient

        client = LLMClient(provider="mock")
        prompt = "Fix this SQL injection..."

        result = client.generate(prompt)

        assert isinstance(result, str)
        assert len(result) > 0

    @patch('patchguard.generators.llm_client.openai')
    def test_generate_fix_with_mock_llm(self, mock_openai):
        from patchguard.generators.llm_client import LLMClient

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """```diff
--- a/test.cs
+++ b/test.cs
@@ -1,3 +1,3 @@
-var query = "SELECT * FROM Users WHERE Id = '" + id + "'";
+var query = "SELECT * FROM Users WHERE Id = @id";
```"""

        mock_openai.ChatCompletion.create.return_value = mock_response

        client = LLMClient(provider="openai", model="gpt-4o")
        result = client.generate("Fix SQL injection")

        assert "--- a/test.cs" in result
        assert "+++ b/test.cs" in result
        assert "@id" in result

    def test_handle_llm_timeout(self):
        from patchguard.generators.llm_client import LLMClient, LLMError

        client = LLMClient(provider="mock", timeout=0.1)

        with pytest.raises(LLMError):
            client.generate("This should timeout", timeout=0.01)

    def test_handle_llm_error(self):
        from patchguard.generators.llm_client import LLMClient, LLMError

        client = LLMClient(provider="mock")

        with pytest.raises(LLMError):
            client.generate("TRIGGER_ERROR")

    def test_token_limit_handling(self):
        from patchguard.generators.llm_client import LLMClient

        client = LLMClient(provider="mock", model="gpt-4o")

        # Very long prompt that exceeds token limit
        long_prompt = "Fix this code: " + "x" * 100000

        # Should truncate or handle gracefully, not crash
        result = client.generate(long_prompt)
        assert isinstance(result, str)

    def test_streaming_response(self):
        from patchguard.generators.llm_client import LLMClient

        client = LLMClient(provider="mock", stream=True)
        prompt = "Fix this code..."

        result = client.generate(prompt)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_anthropic_provider(self):
        from patchguard.generators.llm_client import LLMClient

        client = LLMClient(provider="anthropic", model="claude-3-5-sonnet-20241022")

        # Should initialize without error
        assert client.provider == "anthropic"
        assert client.model == "claude-3-5-sonnet-20241022"

    def test_unsupported_provider_raises_error(self):
        from patchguard.generators.llm_client import LLMClient, LLMError

        with pytest.raises(LLMError):
            client = LLMClient(provider="unsupported")

    def test_gemini_provider(self):
        from patchguard.generators.llm_client import LLMClient

        client = LLMClient(provider="gemini", model="gemini-1.5-pro")

        # Should initialize without error
        assert client.provider == "gemini"
        assert client.model == "gemini-1.5-pro"

    @patch('patchguard.generators.llm_client.genai')
    def test_generate_fix_with_mock_gemini(self, mock_genai):
        from patchguard.generators.llm_client import LLMClient

        # Mock Gemini response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = """```diff
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
-password = "hardcoded123"
+password = os.getenv("PASSWORD")
```"""

        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        client = LLMClient(provider="gemini", model="gemini-1.5-pro", api_key="test-key")
        result = client.generate("Fix hardcoded password")

        assert "--- a/test.py" in result
        assert "+++ b/test.py" in result
        assert "os.getenv" in result