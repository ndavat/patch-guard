"""Integration tests for parser to classifier pipeline."""
import pytest


class TestParserToClassifier:
    """Test end-to-end flow from parser to classifier."""

    def test_sonarqube_to_classifier(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Parse SonarQube JSON
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)

        # Classify findings
        classifier = RiskClassifier()
        classified = classifier.classify_batch(findings)

        # Verify all findings have risk levels
        assert len(classified) > 0
        assert all(hasattr(f, 'risk_level') for f in classified)
        assert all(f.risk_level in ["LOW", "HIGH"] for f in classified)
        assert all(hasattr(f, 'risk_reason') for f in classified)
        assert all(f.risk_reason is not None for f in classified)

    def test_mend_to_classifier(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Parse Mend JSON
        parser = MendParser()
        findings = parser.parse(mend_sample)

        # Classify findings
        classifier = RiskClassifier()
        classified = classifier.classify_batch(findings)

        # Verify all findings have risk levels
        assert len(classified) > 0
        assert all(hasattr(f, 'risk_level') for f in classified)
        assert all(f.risk_level in ["LOW", "HIGH"] for f in classified)

        # Mend findings with fix_hint should be LOW risk
        low_risk = [f for f in classified if f.fix_hint is not None]
        assert all(f.risk_level == "LOW" for f in low_risk)

    def test_trivy_to_classifier(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Parse Trivy JSON
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)

        # Classify findings
        classifier = RiskClassifier()
        classified = classifier.classify_batch(findings)

        # Verify all findings have risk levels
        assert len(classified) > 0
        assert all(hasattr(f, 'risk_level') for f in classified)
        assert all(f.risk_level in ["LOW", "HIGH"] for f in classified)

        # Trivy findings with FixedVersion should be LOW risk
        low_risk = [f for f in classified if f.fix_hint is not None]
        assert all(f.risk_level == "LOW" for f in low_risk)

        # Trivy findings without FixedVersion should be HIGH risk
        high_risk = [f for f in classified if f.fix_hint is None]
        assert all(f.risk_level == "HIGH" for f in high_risk)

    def test_full_pipeline_preserves_finding_data(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Parse
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        original_count = len(findings)

        # Classify
        classifier = RiskClassifier()
        classified = classifier.classify_batch(findings)

        # Verify no findings lost
        assert len(classified) == original_count

        # Verify original data preserved
        for finding in classified:
            assert finding.finding_id is not None
            assert finding.source == "sonarqube"
            assert finding.severity is not None
            assert finding.category is not None
            assert finding.file_path is not None
            assert finding.message is not None
            assert finding.status == "QUEUED"

    def test_mixed_sources_classification(self):
        from patchguard.models.finding import Finding, Severity
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Create findings from different sources
        findings = [
            # SonarQube SQL injection - should be LOW
            Finding(
                finding_id="SONAR-1",
                source="sonarqube",
                severity=Severity.CRITICAL,
                category="VULNERABILITY",
                file_path="Controllers/UserController.cs",
                message="SQL injection",
                rule_id="csharpsquid:S3649",
                status="QUEUED",
                raw_data={}
            ),
            # Mend with fix - should be LOW
            Finding(
                finding_id="CVE-2024-1",
                source="mend",
                severity=Severity.HIGH,
                category="DEPENDENCY",
                file_path="package.name",
                message="Update package",
                fix_hint="Upgrade to version 2.0",
                status="QUEUED",
                raw_data={}
            ),
            # Trivy without fix - should be HIGH
            Finding(
                finding_id="CVE-2024-2",
                source="trivy",
                severity=Severity.CRITICAL,
                category="VULNERABILITY",
                file_path="libc6",
                message="No fix available",
                fix_hint=None,
                status="QUEUED",
                raw_data={}
            ),
        ]

        classifier = RiskClassifier()
        classified = classifier.classify_batch(findings)

        assert classified[0].risk_level == "LOW"  # SQL injection
        assert classified[1].risk_level == "LOW"  # Mend with fix
        assert classified[2].risk_level == "HIGH"  # No fix available
