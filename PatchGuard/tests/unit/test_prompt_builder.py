"""Tests for PromptBuilder — written BEFORE implementation (TDD RED)."""
import pytest
from patchguard.models.finding import Finding, Severity
from patchguard.models.code_context import CodeContext


class TestPromptBuilder:
    """Test the PromptBuilder."""

    def test_build_prompt_with_context(self):
        from patchguard.generators.prompt_builder import PromptBuilder

        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="UserController.cs",
            line_start=42,
            message="SQL injection",
            rule_id="csharpsquid:S3649",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="UserController.cs",
            language="csharp",
            affected_lines='var query = "SELECT * FROM Users WHERE UserId = \'" + userId + "\'";',
            surrounding_code="// surrounding code here",
            imports=["using System.Data.SqlClient;"]
        )

        builder = PromptBuilder()
        prompt = builder.build(finding, context)

        # Prompt should include context
        assert "UserController.cs" in prompt
        assert "SQL injection" in prompt
        assert "surrounding code" in prompt

    def test_build_prompt_with_imports(self):
        from patchguard.generators.prompt_builder import PromptBuilder

        finding = Finding(
            finding_id="TEST-1",
            source="sonarqube",
            severity=Severity.HIGH,
            category="BUG",
            file_path="test.py",
            line_start=10,
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="x = 1",
            surrounding_code="# code",
            imports=["import os", "import sys", "from typing import List"]
        )

        builder = PromptBuilder()
        prompt = builder.build(finding, context)

        # Should include imports
        assert "import os" in prompt
        assert "import sys" in prompt

    def test_build_prompt_sql_injection(self):
        from patchguard.generators.prompt_builder import PromptBuilder

        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="UserController.cs",
            line_start=42,
            message="SQL injection",
            rule_id="csharpsquid:S3649",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="UserController.cs",
            language="csharp",
            affected_lines="var query = ...",
            surrounding_code="// code",
            imports=[]
        )

        builder = PromptBuilder()
        prompt = builder.build(finding, context)

        # Should use SQL injection template
        assert "sql injection" in prompt.lower()
        assert "parameterized" in prompt.lower() or "parameter" in prompt.lower()

    def test_build_prompt_dependency_upgrade(self):
        from patchguard.generators.prompt_builder import PromptBuilder

        finding = Finding(
            finding_id="CVE-2024-1234",
            source="mend",
            severity=Severity.HIGH,
            category="DEPENDENCY",
            file_path="system.text.json",
            message="Update package",
            fix_hint="Upgrade to version 8.0.4",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="system.text.json",
            language="dependency",
            affected_lines="Package: system.text.json",
            surrounding_code="",
            imports=[]
        )

        builder = PromptBuilder()
        prompt = builder.build(finding, context)

        # Should use dependency template
        assert "CVE-2024-1234" in prompt
        assert "8.0.4" in prompt or "Upgrade" in prompt

    def test_build_prompt_output_format(self):
        from patchguard.generators.prompt_builder import PromptBuilder

        finding = Finding(
            finding_id="TEST-1",
            source="sonarqube",
            severity=Severity.HIGH,
            category="BUG",
            file_path="test.cs",
            line_start=10,
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="test.cs",
            language="csharp",
            affected_lines="code",
            surrounding_code="more code",
            imports=[]
        )

        builder = PromptBuilder()
        prompt = builder.build(finding, context)

        # Should request unified diff format
        assert "diff" in prompt.lower()
        assert "---" in prompt or "+++" in prompt

    def test_build_prompt_with_fix_hint(self):
        from patchguard.generators.prompt_builder import PromptBuilder

        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.BLOCKER,
            category="BUG",
            file_path="test.cs",
            line_start=10,
            message="Remove unused variable",
            fix_hint="Delete the variable declaration",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="test.cs",
            language="csharp",
            affected_lines="int unused = 5;",
            surrounding_code="// code",
            imports=[]
        )

        builder = PromptBuilder()
        prompt = builder.build(finding, context)

        # Should include fix hint
        assert "Delete the variable declaration" in prompt

    def test_build_prompt_with_line_numbers(self):
        from patchguard.generators.prompt_builder import PromptBuilder

        finding = Finding(
            finding_id="TEST-1",
            source="sonarqube",
            severity=Severity.HIGH,
            category="BUG",
            file_path="test.py",
            line_start=42,
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="x = 1",
            surrounding_code="# code",
            imports=[]
        )

        builder = PromptBuilder()
        prompt = builder.build(finding, context)

        # Should include line number
        assert "42" in prompt or "Line: 42" in prompt

    def test_build_retry_prompt_with_error(self):
        from patchguard.generators.prompt_builder import PromptBuilder

        original_prompt = "Fix this code..."
        linter_error = "E501 line too long (120 > 79 characters)"

        builder = PromptBuilder()
        retry_prompt = builder.build_retry(original_prompt, linter_error)

        # Should include original prompt and error
        assert "Fix this code..." in retry_prompt
        assert "E501" in retry_prompt
        assert "line too long" in retry_prompt
