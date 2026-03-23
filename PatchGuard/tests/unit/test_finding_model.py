"""Tests for the Finding model and Severity enum — written BEFORE implementation (TDD RED)."""
import pytest


class TestSeverityEnum:
    """Test the Severity enumeration."""

    def test_severity_critical_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.CRITICAL.value == "CRITICAL"

    def test_severity_high_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.HIGH.value == "HIGH"

    def test_severity_blocker_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.BLOCKER.value == "BLOCKER"

    def test_severity_medium_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.MEDIUM.value == "MEDIUM"

    def test_severity_low_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.LOW.value == "LOW"

    def test_severity_from_string(self):
        from patchguard.models.finding import Severity
        assert Severity("CRITICAL") == Severity.CRITICAL

    def test_severity_invalid_raises(self):
        from patchguard.models.finding import Severity
        with pytest.raises(ValueError):
            Severity("INVALID")


class TestFindingModel:
    """Test the Finding dataclass."""

    def test_create_finding_with_required_fields(self):
        from patchguard.models.finding import Finding, Severity
        f = Finding(
            finding_id="CVE-2024-1234",
            source="trivy",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="Dockerfile",
            message="Update curl to 7.81.0-1ubuntu1.16",
            status="QUEUED",
            raw_data={"VulnerabilityID": "CVE-2024-1234"}
        )
        assert f.finding_id == "CVE-2024-1234"
        assert f.source == "trivy"
        assert f.severity == Severity.CRITICAL

    def test_finding_optional_fields_default_to_none(self):
        from patchguard.models.finding import Finding, Severity
        f = Finding(
            finding_id="TEST-001",
            source="sonarqube",
            severity=Severity.BLOCKER,
            category="BUG",
            file_path="src/main.py",
            message="Null pointer",
            status="QUEUED",
            raw_data={}
        )
        assert f.line_start is None
        assert f.line_end is None
        assert f.fix_hint is None
        assert f.rule_id is None
        assert f.risk_level is None

    def test_finding_with_all_fields(self):
        from patchguard.models.finding import Finding, Severity
        f = Finding(
            finding_id="SONAR-42",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="Controllers/UserController.cs",
            line_start=42,
            line_end=42,
            message="SQL injection risk",
            fix_hint="Use parameterized queries",
            rule_id="csharpsquid:S3649",
            risk_level="LOW",
            status="QUEUED",
            raw_data={"key": "SONAR-42"}
        )
        assert f.line_start == 42
        assert f.fix_hint == "Use parameterized queries"
        assert f.rule_id == "csharpsquid:S3649"
        assert f.risk_level == "LOW"

    def test_finding_to_dict(self):
        from patchguard.models.finding import Finding, Severity
        f = Finding(
            finding_id="CVE-2024-5678",
            source="mend",
            severity=Severity.HIGH,
            category="DEPENDENCY",
            file_path="package.json",
            message="Upgrade lodash",
            status="QUEUED",
            raw_data={}
        )
        d = f.to_dict()
        assert isinstance(d, dict)
        assert d["finding_id"] == "CVE-2024-5678"
        assert d["severity"] == "HIGH"
        assert d["source"] == "mend"

    def test_finding_equality(self):
        from patchguard.models.finding import Finding, Severity
        f1 = Finding(finding_id="X", source="trivy", severity=Severity.LOW,
                     category="VULNERABILITY", file_path="f.py",
                     message="msg", status="QUEUED", raw_data={})
        f2 = Finding(finding_id="X", source="trivy", severity=Severity.LOW,
                     category="VULNERABILITY", file_path="f.py",
                     message="msg", status="QUEUED", raw_data={})
        assert f1 == f2
