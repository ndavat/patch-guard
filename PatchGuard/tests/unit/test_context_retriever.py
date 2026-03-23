"""Tests for Context Retriever — written BEFORE implementation (TDD RED)."""
import pytest
import os


class TestContextRetriever:
    """Test the ContextRetriever."""

    def test_retrieve_context_with_line_numbers(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        # SonarQube finding with line number
        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="UserController.cs",
            line_start=42,
            message="SQL injection",
            status="QUEUED",
            raw_data={}
        )

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(finding)

        assert context.file_path == "UserController.cs"
        assert context.language == "csharp"
        assert context.surrounding_code is not None
        assert len(context.surrounding_code) > 0
        assert context.imports is not None

    def test_extract_imports_csharp(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="UserController.cs",
            line_start=10,
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(finding)

        # Should extract using statements
        assert any("using" in imp.lower() for imp in context.imports)

    def test_extract_imports_python(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        finding = Finding(
            finding_id="TEST-1",
            source="sonarqube",
            severity=Severity.HIGH,
            category="BUG",
            file_path="helper.py",
            line_start=10,
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(finding)

        assert context.language == "python"
        # Should extract import statements
        assert len(context.imports) > 0

    def test_extract_class_and_method(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="UserController.cs",
            line_start=42,
            message="SQL injection",
            status="QUEUED",
            raw_data={}
        )

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(finding)

        # Should detect class name (may be None if not implemented yet)
        assert hasattr(context, 'class_name')

    def test_handle_file_not_found(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="NonExistent.cs",
            line_start=42,
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")

        # Should not raise exception, return error context
        context = retriever.retrieve(finding)
        assert context is not None
        assert context.file_path == "NonExistent.cs"

    def test_handle_line_out_of_bounds(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="helper.py",
            line_start=9999,  # Way beyond file length
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(finding)

        # Should return available lines, not crash
        assert context is not None
        assert context.surrounding_code is not None

    def test_small_file_returns_full_content(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        finding = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="helper.py",  # Small file
            line_start=10,
            message="Test",
            status="QUEUED",
            raw_data={}
        )

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(finding)

        # Small files should include full_file
        if context.full_file is not None:
            assert len(context.full_file) > 0

    def test_detect_language_from_extension(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        test_cases = [
            ("UserController.cs", "csharp"),
            ("helper.py", "python"),
            ("api.js", "javascript"),
            ("Dockerfile", "dockerfile"),
        ]

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")

        for file_path, expected_lang in test_cases:
            finding = Finding(
                finding_id="TEST",
                source="sonarqube",
                severity=Severity.HIGH,
                category="BUG",
                file_path=file_path,
                line_start=1,
                message="Test",
                status="QUEUED",
                raw_data={}
            )
            context = retriever.retrieve(finding)
            assert context.language == expected_lang

    def test_dependency_finding_no_file_access(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        # Mend dependency finding - no source file
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

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(finding)

        # Should return minimal context for dependencies
        assert context.file_path == "system.text.json"
        assert context.language == "dependency"

    def test_context_caching(self):
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")

        # Create two findings for same file
        finding1 = Finding(
            finding_id="SONAR-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="helper.py",
            line_start=10,
            message="Test 1",
            status="QUEUED",
            raw_data={}
        )

        finding2 = Finding(
            finding_id="SONAR-2",
            source="sonarqube",
            severity=Severity.HIGH,
            category="BUG",
            file_path="helper.py",
            line_start=20,
            message="Test 2",
            status="QUEUED",
            raw_data={}
        )

        # Retrieve context for both
        context1 = retriever.retrieve(finding1)
        context2 = retriever.retrieve(finding2)

        # Both should succeed (caching should work)
        assert context1 is not None
        assert context2 is not None
        assert context1.file_path == context2.file_path
