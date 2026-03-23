"""Tests for FixGenerator — written BEFORE implementation (TDD RED)."""
import pytest
from unittest.mock import Mock, MagicMock, patch


class TestFixGenerator:
    """Test the FixGenerator orchestrator."""

    def test_generate_fix_success(self):
        """Test full flow: prompt → LLM → diff → validate → success."""
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext
        from patchguard.models.fix_result import FixResult

        # Create mock dependencies
        mock_llm_client = Mock()
        mock_validator = Mock()

        # Mock LLM response with valid diff
        mock_llm_client.generate.return_value = """
Here's the fix:

```diff
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello, World!")
     return True
```
"""

        # Mock validator - code passes validation
        mock_validator.validate.return_value = (True, "Code is valid")

        # Create FixGenerator
        generator = FixGenerator(mock_llm_client, mock_validator)

        # Create test finding and context
        finding = Finding(
            finding_id="sq-001",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="test.py",
            message="SQL injection vulnerability",
            status="QUEUED",
            raw_data={},
            line_start=10,
            rule_id="sql-injection",
            fix_hint="Use parameterized queries"
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="def hello():\n    print(\"Hello\")",
            surrounding_code="def hello():\n    print(\"Hello\")\n    return True",
            imports=["import sys"]
        )

        # Generate fix
        result = generator.generate(finding, context)

        # Verify result
        assert isinstance(result, FixResult)
        assert result.success is True
        assert result.attempts == 1
        assert result.modified_code is not None
        assert "Hello, World!" in result.modified_code

    def test_generate_fix_with_retry(self):
        """Test self-correction: linter fails, retry with error, success."""
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext

        mock_llm_client = Mock()
        mock_validator = Mock()

        # First attempt: linter fails
        # Second attempt: linter passes
        mock_validator.validate.side_effect = [
            (False, "E501 line too long"),
            (True, "Code is valid")
        ]

        # LLM responses: first attempt, then retry with error feedback
        mock_llm_client.generate.side_effect = [
            """```diff
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-x = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20
+x = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20
```""",
            """```diff
--- a/test.py
+++ b/test.py
@@ -1,1 +1,2 @@
-x = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20
+x = (1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 +
+     11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20)
```"""
        ]

        generator = FixGenerator(mock_llm_client, mock_validator)

        finding = Finding(
            finding_id="sq-002",
            source="sonarqube",
            severity=Severity.MEDIUM,
            category="BUG",
            file_path="test.py",
            message="Line too long",
            status="QUEUED",
            raw_data={},
            line_start=1,
            rule_id="line-too-long",
            fix_hint="Break into multiple lines"
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="x = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20",
            surrounding_code="x = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20",
            imports=[]
        )

        result = generator.generate(finding, context)

        # Should succeed on second attempt
        assert result.success is True
        assert result.attempts == 2

    def test_max_attempts_reached(self):
        """Test escalation: 3 failures → give up."""
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext

        mock_llm_client = Mock()
        mock_validator = Mock()

        # All validation attempts fail
        mock_validator.validate.return_value = (False, "Persistent error")

        # LLM always returns invalid diffs
        mock_llm_client.generate.return_value = """```diff
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-old
+new
```"""

        generator = FixGenerator(mock_llm_client, mock_validator)

        finding = Finding(
            finding_id="sq-003",
            source="sonarqube",
            severity=Severity.HIGH,
            category="BUG",
            file_path="test.py",
            message="Test finding",
            status="QUEUED",
            raw_data={},
            line_start=1,
            rule_id="test-rule",
            fix_hint="Fix it"
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="old",
            surrounding_code="old",
            imports=[]
        )

        result = generator.generate(finding, context)

        # Should fail after 3 attempts
        assert result.success is False
        assert result.attempts == 3
        assert "attempts" in result.error_message.lower()

    def test_dependency_finding_no_fix(self):
        """Test skip: dependency findings don't need LLM."""
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext

        mock_llm_client = Mock()
        mock_validator = Mock()

        generator = FixGenerator(mock_llm_client, mock_validator)

        # Dependency finding (from Mend)
        finding = Finding(
            finding_id="mend-001",
            source="mend",
            severity=Severity.HIGH,
            category="DEPENDENCY",
            file_path="package.json",
            message="Upgrade lodash to 4.17.21",
            status="QUEUED",
            raw_data={},
            line_start=5,
            rule_id="dependency-upgrade",
            fix_hint="Update version in package.json"
        )

        context = CodeContext(
            file_path="package.json",
            language="json",
            affected_lines='{"dependencies": {"lodash": "4.17.20"}}',
            surrounding_code='{"dependencies": {"lodash": "4.17.20"}}',
            imports=[]
        )

        result = generator.generate(finding, context)

        # Should skip LLM generation for dependency findings
        assert result.success is True
        assert result.attempts == 0
        assert "dependency" in result.error_message.lower()
        # LLM should not be called
        mock_llm_client.generate.assert_not_called()

    def test_high_risk_finding_no_fix(self):
        """Test skip: HIGH risk findings go to manual review."""
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext

        mock_llm_client = Mock()
        mock_validator = Mock()

        generator = FixGenerator(mock_llm_client, mock_validator)

        # HIGH risk finding
        finding = Finding(
            finding_id="sq-004",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="auth.py",
            message="Authentication bypass",
            status="QUEUED",
            raw_data={},
            line_start=42,
            rule_id="auth-bypass",
            fix_hint="Implement proper auth check",
            risk_level="HIGH"
        )

        context = CodeContext(
            file_path="auth.py",
            language="python",
            affected_lines="def check_auth():\n    return True",
            surrounding_code="def check_auth():\n    return True",
            imports=[]
        )

        result = generator.generate(finding, context)

        # Should skip HIGH risk findings
        assert result.success is True
        assert result.attempts == 0
        assert "high risk" in result.error_message.lower()
        # LLM should not be called
        mock_llm_client.generate.assert_not_called()

    def test_llm_error_handling(self):
        """Test graceful handling of LLM errors."""
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext

        mock_llm_client = Mock()
        mock_validator = Mock()

        # LLM raises exception
        mock_llm_client.generate.side_effect = Exception("API timeout")

        generator = FixGenerator(mock_llm_client, mock_validator)

        finding = Finding(
            finding_id="sq-005",
            source="sonarqube",
            severity=Severity.MEDIUM,
            category="BUG",
            file_path="test.py",
            message="Test finding",
            status="QUEUED",
            raw_data={},
            line_start=1,
            rule_id="test-rule",
            fix_hint="Fix it"
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="test",
            surrounding_code="test",
            imports=[]
        )

        result = generator.generate(finding, context)

        # Should fail gracefully
        assert result.success is False
        assert "error" in result.error_message.lower()

    def test_diff_parsing_error(self):
        """Test handling of invalid diff from LLM."""
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext

        mock_llm_client = Mock()
        mock_validator = Mock()

        # LLM returns invalid diff
        mock_llm_client.generate.return_value = "This is not a valid diff"

        # Validator will be called but we expect diff parsing to fail first
        mock_validator.validate.return_value = (False, "Invalid code")

        generator = FixGenerator(mock_llm_client, mock_validator)

        finding = Finding(
            finding_id="sq-006",
            source="sonarqube",
            severity=Severity.MEDIUM,
            category="BUG",
            file_path="test.py",
            message="Test finding",
            status="QUEUED",
            raw_data={},
            line_start=1,
            rule_id="test-rule",
            fix_hint="Fix it"
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="test",
            surrounding_code="test",
            imports=[]
        )

        result = generator.generate(finding, context)

        # Should fail due to invalid diff
        assert result.success is False
        assert "attempts" in result.error_message.lower()
