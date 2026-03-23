"""Integration tests for classifier to retriever pipeline."""
import pytest


class TestClassifierToRetriever:
    """Test end-to-end flow from classifier to context retriever."""

    def test_end_to_end_with_context(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        from patchguard.classifiers.risk_classifier import RiskClassifier
        from patchguard.retrievers.context_retriever import ContextRetriever

        # Parse SonarQube JSON
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)

        # Classify findings
        classifier = RiskClassifier()
        classified = classifier.classify_batch(findings)

        # Retrieve context for LOW risk findings
        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")

        low_risk_findings = [f for f in classified if f.risk_level == "LOW"]

        if len(low_risk_findings) > 0:
            for finding in low_risk_findings:
                context = retriever.retrieve(finding)
                assert context is not None
                assert context.file_path is not None
                assert context.language is not None

    def test_full_pipeline_preserves_data(self):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        from patchguard.classifiers.risk_classifier import RiskClassifier
        from patchguard.retrievers.context_retriever import ContextRetriever
        from patchguard.models.finding import Finding, Severity

        # Create a test finding
        finding = Finding(
            finding_id="TEST-1",
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

        # Classify
        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        # Retrieve context
        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(classified)

        # Verify original finding data preserved
        assert classified.finding_id == "TEST-1"
        assert classified.source == "sonarqube"
        assert classified.severity == Severity.CRITICAL
        assert classified.risk_level is not None

        # Verify context extracted
        assert context.file_path == "UserController.cs"
        assert context.language == "csharp"
        assert context.surrounding_code is not None

    def test_mixed_risk_levels_context_retrieval(self):
        from patchguard.models.finding import Finding, Severity
        from patchguard.classifiers.risk_classifier import RiskClassifier
        from patchguard.retrievers.context_retriever import ContextRetriever

        findings = [
            # LOW risk - SQL injection
            Finding(
                finding_id="LOW-1",
                source="sonarqube",
                severity=Severity.CRITICAL,
                category="VULNERABILITY",
                file_path="UserController.cs",
                line_start=42,
                message="SQL injection",
                rule_id="csharpsquid:S3649",
                status="QUEUED",
                raw_data={}
            ),
            # HIGH risk - auth file
            Finding(
                finding_id="HIGH-1",
                source="sonarqube",
                severity=Severity.CRITICAL,
                category="VULNERABILITY",
                file_path="auth/LoginController.cs",
                line_start=10,
                message="Auth issue",
                status="QUEUED",
                raw_data={}
            ),
        ]

        # Classify
        classifier = RiskClassifier()
        classified = classifier.classify_batch(findings)

        # Retrieve context for all
        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")

        for finding in classified:
            context = retriever.retrieve(finding)
            assert context is not None

            # LOW risk should have code context
            if finding.risk_level == "LOW":
                assert context.language == "csharp"

    def test_dependency_findings_skip_file_access(self):
        from patchguard.models.finding import Finding, Severity
        from patchguard.classifiers.risk_classifier import RiskClassifier
        from patchguard.retrievers.context_retriever import ContextRetriever

        # Mend dependency finding
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

        # Classify
        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        # Retrieve context
        retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
        context = retriever.retrieve(classified)

        # Should return minimal context for dependencies
        assert context.language == "dependency"
        assert context.file_path == "system.text.json"

    def test_context_includes_imports(self):
        from patchguard.models.finding import Finding, Severity
        from patchguard.retrievers.context_retriever import ContextRetriever

        finding = Finding(
            finding_id="TEST-1",
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

        # Should extract using statements
        assert len(context.imports) > 0
        assert any("using" in imp for imp in context.imports)
