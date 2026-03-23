"""Integration tests for Phase 8 LLM Fix Generator pipeline."""
import pytest
from unittest.mock import Mock, patch


class TestPhase8Integration:
    """Integration tests for end-to-end fix generation pipeline."""

    def test_end_to_end_fix_generation(self):
        """Test: Parse → Classify → Context → Generate Fix."""
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.generators.prompt_builder import PromptBuilder
        from patchguard.generators.llm_client import LLMClient
        from patchguard.validators.linter_validator import LinterValidator

        # Create real components
        llm_client = LLMClient(provider="mock")
        validator = LinterValidator()
        generator = FixGenerator(llm_client, validator)

        # Create a finding
        finding = Finding(
            finding_id="test-001",
            source="sonarqube",
            severity=Severity.HIGH,
            category="BUG",
            file_path="test.py",
            message="Unused variable",
            status="QUEUED",
            raw_data={},
            line_start=5,
            rule_id="unused-var",
            fix_hint="Remove unused variable"
        )

        # Create code context
        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="x = 1",
            surrounding_code="def foo():\n    x = 1\n    return 2",
            imports=[]
        )

        # Generate fix
        result = generator.generate(finding, context)

        # Verify result structure
        assert result.finding_id == "test-001"
        assert isinstance(result.success, bool)
        assert isinstance(result.attempts, int)
        assert result.attempts >= 0

    def test_pipeline_with_multiple_findings(self):
        """Test processing multiple findings through the pipeline."""
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.generators.llm_client import LLMClient
        from patchguard.validators.linter_validator import LinterValidator

        llm_client = LLMClient(provider="mock")
        validator = LinterValidator()
        generator = FixGenerator(llm_client, validator)

        findings = [
            Finding(
                finding_id="test-001",
                source="sonarqube",
                severity=Severity.MEDIUM,
                category="BUG",
                file_path="app.py",
                message="Issue 1",
                status="QUEUED",
                raw_data={},
                line_start=10
            ),
            Finding(
                finding_id="test-002",
                source="sonarqube",
                severity=Severity.HIGH,
                category="VULNERABILITY",
                file_path="app.py",
                message="Issue 2",
                status="QUEUED",
                raw_data={},
                line_start=20
            ),
            Finding(
                finding_id="test-003",
                source="mend",
                severity=Severity.HIGH,
                category="DEPENDENCY",
                file_path="package.json",
                message="Dependency issue",
                status="QUEUED",
                raw_data={},
                line_start=5
            ),
        ]

        contexts = [
            CodeContext(
                file_path="app.py",
                language="python",
                affected_lines="code1",
                surrounding_code="code1",
                imports=[]
            ),
            CodeContext(
                file_path="app.py",
                language="python",
                affected_lines="code2",
                surrounding_code="code2",
                imports=[]
            ),
            CodeContext(
                file_path="package.json",
                language="json",
                affected_lines='{"dep": "1.0"}',
                surrounding_code='{"dep": "1.0"}',
                imports=[]
            ),
        ]

        results = []
        for finding, context in zip(findings, contexts):
            result = generator.generate(finding, context)
            results.append(result)

        # Verify all results
        assert len(results) == 3
        assert all(hasattr(r, 'finding_id') for r in results)
        assert all(hasattr(r, 'success') for r in results)

        # Dependency finding should be skipped
        assert results[2].success is True
        assert results[2].attempts == 0

    def test_pipeline_error_recovery(self):
        """Test pipeline handles errors gracefully."""
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.generators.llm_client import LLMClient
        from patchguard.validators.linter_validator import LinterValidator

        llm_client = LLMClient(provider="mock")
        validator = LinterValidator()
        generator = FixGenerator(llm_client, validator)

        # Finding with missing optional fields
        finding = Finding(
            finding_id="test-001",
            source="sonarqube",
            severity=Severity.MEDIUM,
            category="BUG",
            file_path="test.py",
            message="Test issue",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="code",
            surrounding_code="code",
            imports=[]
        )

        # Should not crash
        result = generator.generate(finding, context)
        assert result is not None
        assert hasattr(result, 'finding_id')

    def test_pipeline_with_high_risk_findings(self):
        """Test pipeline skips HIGH risk findings."""
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.generators.llm_client import LLMClient
        from patchguard.validators.linter_validator import LinterValidator

        llm_client = LLMClient(provider="mock")
        validator = LinterValidator()
        generator = FixGenerator(llm_client, validator)

        # HIGH risk finding
        finding = Finding(
            finding_id="test-001",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="auth.py",
            message="Auth bypass",
            status="QUEUED",
            raw_data={},
            risk_level="HIGH"
        )

        context = CodeContext(
            file_path="auth.py",
            language="python",
            affected_lines="auth code",
            surrounding_code="auth code",
            imports=[]
        )

        result = generator.generate(finding, context)

        # Should skip HIGH risk
        assert result.success is True
        assert result.attempts == 0
        assert "high risk" in result.error_message.lower()

    def test_pipeline_result_structure(self):
        """Test FixResult contains all expected fields."""
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext
        from patchguard.models.fix_result import FixResult
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.generators.llm_client import LLMClient
        from patchguard.validators.linter_validator import LinterValidator

        llm_client = LLMClient(provider="mock")
        validator = LinterValidator()
        generator = FixGenerator(llm_client, validator)

        finding = Finding(
            finding_id="test-001",
            source="sonarqube",
            severity=Severity.MEDIUM,
            category="BUG",
            file_path="test.py",
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="code",
            surrounding_code="code",
            imports=[]
        )

        result = generator.generate(finding, context)

        # Verify FixResult structure
        assert isinstance(result, FixResult)
        assert hasattr(result, 'finding_id')
        assert hasattr(result, 'success')
        assert hasattr(result, 'diff')
        assert hasattr(result, 'modified_code')
        assert hasattr(result, 'linter_output')
        assert hasattr(result, 'attempts')
        assert hasattr(result, 'error_message')

        # Verify types
        assert isinstance(result.finding_id, str)
        assert isinstance(result.success, bool)
        assert isinstance(result.attempts, int)
        assert result.diff is None or isinstance(result.diff, str)
        assert result.modified_code is None or isinstance(result.modified_code, str)
        assert result.linter_output is None or isinstance(result.linter_output, str)
        assert result.error_message is None or isinstance(result.error_message, str)

    def test_pipeline_to_dict_serialization(self):
        """Test FixResult can be serialized to dict."""
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext
        from patchguard.generators.fix_generator import FixGenerator
        from patchguard.generators.llm_client import LLMClient
        from patchguard.validators.linter_validator import LinterValidator

        llm_client = LLMClient(provider="mock")
        validator = LinterValidator()
        generator = FixGenerator(llm_client, validator)

        finding = Finding(
            finding_id="test-001",
            source="sonarqube",
            severity=Severity.MEDIUM,
            category="BUG",
            file_path="test.py",
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="test.py",
            language="python",
            affected_lines="code",
            surrounding_code="code",
            imports=[]
        )

        result = generator.generate(finding, context)
        result_dict = result.to_dict()

        # Verify dict structure
        assert isinstance(result_dict, dict)
        assert "finding_id" in result_dict
        assert "success" in result_dict
        assert "attempts" in result_dict
        assert result_dict["finding_id"] == "test-001"
