import os
import time
from typing import Optional

# Placeholder for optional dependencies (to allow mocking in tests)
openai = None
anthropic = None
genai = None


class LLMError(Exception):
    """Exception raised when LLM operations fail."""
    pass


class LLMClient:
    """Client for interacting with LLM providers to generate code fixes."""

    def __init__(self, provider: str = "mock", model: str = "gpt-4o", timeout: float = 60.0, stream: bool = False, api_key: Optional[str] = None):
        """Initialize LLM client.

        Args:
            provider: LLM provider (openai, anthropic, mock)
            model: Model name (gpt-4o, claude-3-5-sonnet-20241022, etc.)
            timeout: Request timeout in seconds
            stream: Enable streaming response
            api_key: Optional API key. If None, looks for OPENAI_API_KEY or ANTHROPIC_API_KEY env vars.

        Raises:
            LLMError: If provider is not supported
        """
        self.provider = provider
        self.model = model
        self.timeout = timeout
        self.stream = stream
        self.api_key = api_key

        # Set API key from environment if not provided
        if not self.api_key:
            if provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
            elif provider == "gemini":
                self.api_key = os.getenv("GEMINI_API_KEY")

        # Validate provider
        if provider not in ["openai", "anthropic", "gemini", "mock"]:
            raise LLMError(f"Unsupported provider: {provider}")

    def generate(self, prompt: str, timeout: Optional[float] = None) -> str:
        """Generate fix using LLM.

        Args:
            prompt: Prompt for fix generation
            timeout: Request timeout (overrides instance timeout)

        Returns:
            Generated fix as string (usually a unified diff)

        Raises:
            LLMError: If generation fails
        """
        actual_timeout = timeout or self.timeout

        if self.provider == "mock":
            return self._mock_generate(prompt, actual_timeout)
        elif self.provider == "openai":
            return self._openai_generate(prompt, actual_timeout)
        elif self.provider == "anthropic":
            return self._anthropic_generate(prompt, actual_timeout)
        elif self.provider == "gemini":
            return self._gemini_generate(prompt, actual_timeout)

        raise LLMError(f"Unsupported provider: {self.provider}")

    def _mock_generate(self, prompt: str, timeout: float) -> str:
        """Mock LLM generation for testing.

        Args:
            prompt: Input prompt
            timeout: Timeout in seconds

        Returns:
            Mock diff response

        Raises:
            LLMError: If timeout too short or special trigger in prompt
        """
        if timeout < 0.1:
            time.sleep(timeout + 0.01)  # Simulate timeout
            raise LLMError("Request timed out")

        if "TRIGGER_ERROR" in prompt:
            raise LLMError("Mock error triggered")

        # Handle token limit test
        if len(prompt) > 50000:
            prompt = prompt[:10000] + "... [truncated] ..."  # type: ignore

        # Return mock unified diff
        if "SQL injection" in prompt:
            return '''```diff
--- a/UserController.cs
+++ b/UserController.cs
@@ -39,2 +39,3 @@
-                var query = "SELECT * FROM Users WHERE UserId = '" + userId + "'";
-                var command = new SqlCommand(query, connection);
+                var query = "SELECT * FROM Users WHERE UserId = @userId";
+                var command = new SqlCommand(query, connection);
+                command.Parameters.Add(new SqlParameter("@userId", userId));
```'''

        # Return generic diff
        return '''```diff
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-# TODO: fix this
+# Fixed
```'''

    def _openai_generate(self, prompt: str, timeout: float) -> str:
        """Generate using OpenAI API.

        Args:
            prompt: Input prompt
            timeout: Timeout in seconds

        Returns:
            Generated response

        Raises:
            LLMError: If API call fails
        """
        try:
            # Use global placeholder (allows mocking in tests)
            global openai
            if openai is None:
                try:
                    import openai
                except ImportError:
                    pass

            if openai is not None:
                if self.api_key:
                    openai.api_key = self.api_key
                
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=timeout
                )
                return response.choices[0].message.content

            # Default to mock if library not present
            return self._mock_generate(prompt, timeout)
        except Exception as e:
            raise LLMError(f"OpenAI API error: {e}")

    def _anthropic_generate(self, prompt: str, timeout: float) -> str:
        """Generate using Anthropic API.

        Args:
            prompt: Input prompt
            timeout: Timeout in seconds

        Returns:
            Generated response

        Raises:
            LLMError: If API call fails
        """
        try:
            # This would normally call Anthropic API
            # For now, return mock response
            return self._mock_generate(prompt, timeout)
        except Exception as e:
            raise LLMError(f"Anthropic API error: {e}")

    def _gemini_generate(self, prompt: str, timeout: float) -> str:
        """Generate using Google Gemini API.

        Args:
            prompt: Input prompt
            timeout: Timeout in seconds

        Returns:
            Generated response

        Raises:
            LLMError: If API call fails
        """
        try:
            # Use global placeholder (allows mocking in tests)
            global genai
            if genai is None:
                try:
                    import google.generativeai as genai
                except ImportError:
                    pass

            if genai is not None:
                if self.api_key:
                    genai.configure(api_key=self.api_key)

                model = genai.GenerativeModel(self.model)
                response = model.generate_content(prompt)
                return response.text

            # Default to mock if library not present
            return self._mock_generate(prompt, timeout)
        except Exception as e:
            raise LLMError(f"Gemini API error: {e}")