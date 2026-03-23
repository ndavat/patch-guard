"""Tests for Risk Classifier — written BEFORE implementation (TDD RED)."""
import pytest
from patchguard.models.finding import Finding, Severity


class TestRiskClassifier:
    """Test the RiskClassifier."""

    def test_direct_dependency_upgrade_is_low_risk(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Mend finding with FixedVersion
        finding = Finding(
            finding_id="CVE-2024-1234",
            source="mend",
            severity=Severity.HIGH,
            category="DEPENDENCY",
            file_path="system.text.json",
            message="Update to 8.0.4",
            fix_hint="Upgrade to version System.Text.Json - 8.0.4",
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        assert classified.risk_level == "LOW"
        assert "dependency upgrade" in classified.risk_reason.lower()

    def test_no_fixed_version_is_high_risk(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Trivy finding without FixedVersion
        finding = Finding(
            finding_id="CVE-2024-5678",
            source="trivy",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="libc6",
            message="RCE vulnerability",
            fix_hint=None,
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        assert classified.risk_level == "HIGH"
        assert "no fix" in classified.risk_reason.lower() or "not available" in classified.risk_reason.lower()

    def test_sql_injection_with_pattern_is_low_risk(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # SonarQube SQL injection with known pattern
        finding = Finding(
            finding_id="SONAR-42",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="Controllers/UserController.cs",
            line_start=42,
            message="SQL injection risk",
            rule_id="csharpsquid:S3649",
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        assert classified.risk_level == "LOW"
        assert "sql injection" in classified.risk_reason.lower() or "pattern" in classified.risk_reason.lower()

    def test_auth_flow_change_is_high_risk(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Finding in auth-related file
        finding = Finding(
            finding_id="SONAR-99",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="auth/LoginController.cs",
            message="Security issue in login",
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        assert classified.risk_level == "HIGH"
        assert "auth" in classified.risk_reason.lower()

    def test_multi_file_change_is_high_risk(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # This test is a placeholder for future multi-file detection
        # For now, we test that unknown patterns default to HIGH
        finding = Finding(
            finding_id="COMPLEX-1",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="BUG",
            file_path="Services/ComplexService.cs",
            message="Complex refactoring needed",
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        # Should default to HIGH risk
        assert classified.risk_level == "HIGH"

    def test_single_file_simple_fix_is_low_risk(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # SonarQube finding with line number and fix hint
        finding = Finding(
            finding_id="SONAR-123",
            source="sonarqube",
            severity=Severity.BLOCKER,
            category="BUG",
            file_path="Utils/StringHelper.cs",
            line_start=67,
            message="Remove commented code",
            fix_hint="Delete lines 67-70",
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        assert classified.risk_level == "LOW"

    def test_transitive_dependency_is_high_risk(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Dependency without fix hint (transitive or no fix available)
        finding = Finding(
            finding_id="CVE-2024-9999",
            source="mend",
            severity=Severity.HIGH,
            category="DEPENDENCY",
            file_path="transitive.package",
            message="Transitive dependency issue",
            fix_hint=None,
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        assert classified.risk_level == "HIGH"

    def test_unknown_pattern_defaults_to_high_risk(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        # Finding that doesn't match any specific rule
        finding = Finding(
            finding_id="UNKNOWN-1",
            source="sonarqube",
            severity=Severity.MAJOR,
            category="CODE_SMELL",
            file_path="RandomFile.cs",
            message="Unknown issue",
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        assert classified.risk_level == "HIGH"
        assert any(term in classified.risk_reason.lower() for term in ["default", "no matching", "fix hint"])

    def test_classifier_returns_reason(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        finding = Finding(
            finding_id="TEST-1",
            source="mend",
            severity=Severity.HIGH,
            category="DEPENDENCY",
            file_path="package.name",
            message="Test",
            fix_hint="Upgrade to version 2.0",
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier()
        classified = classifier.classify(finding)

        assert hasattr(classified, 'risk_reason')
        assert classified.risk_reason is not None
        assert len(classified.risk_reason) > 0

    def test_custom_policy_overrides_defaults(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier
        from patchguard.config.risk_policy import SafeToFixPolicy, RiskRule

        # Custom policy that marks everything as LOW risk
        custom_rules = [
            RiskRule(
                name="Allow All",
                condition=lambda f: True,
                risk_level="LOW",
                reason="Custom policy: all findings are low risk"
            )
        ]
        custom_policy = SafeToFixPolicy(rules=custom_rules)

        finding = Finding(
            finding_id="TEST-2",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="auth/LoginController.cs",
            message="Should be HIGH but custom policy makes it LOW",
            status="QUEUED",
            raw_data={}
        )

        classifier = RiskClassifier(policy=custom_policy)
        classified = classifier.classify(finding)

        assert classified.risk_level == "LOW"
        assert "custom policy" in classified.risk_reason.lower()

    def test_classify_batch(self):
        from patchguard.classifiers.risk_classifier import RiskClassifier

        findings = [
            Finding(finding_id="1", source="mend", severity=Severity.HIGH,
                   category="DEPENDENCY", file_path="pkg1", message="test",
                   fix_hint="Upgrade", status="QUEUED", raw_data={}),
            Finding(finding_id="2", source="trivy", severity=Severity.CRITICAL,
                   category="VULNERABILITY", file_path="pkg2", message="test",
                   fix_hint=None, status="QUEUED", raw_data={}),
        ]

        classifier = RiskClassifier()
        classified = classifier.classify_batch(findings)

        assert len(classified) == 2
        assert all(hasattr(f, 'risk_level') for f in classified)
        assert all(f.risk_level in ["LOW", "HIGH"] for f in classified)
