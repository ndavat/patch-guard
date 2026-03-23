"""Tests for SeverityFilter — written BEFORE implementation (TDD RED)."""
import pytest


class TestSeverityFilter:
    """Test the SeverityFilter utility."""

    def test_filter_sonarqube_allows_blocker_critical(self):
        from patchguard.utils.severity import SeverityFilter
        from patchguard.models.finding import Finding, Severity

        filter_obj = SeverityFilter()
        findings = [
            Finding(finding_id="1", source="sonarqube", severity=Severity.BLOCKER,
                   category="BUG", file_path="test.cs", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="2", source="sonarqube", severity=Severity.CRITICAL,
                   category="VULNERABILITY", file_path="test.cs", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="3", source="sonarqube", severity=Severity.MAJOR,
                   category="BUG", file_path="test.cs", message="test",
                   status="QUEUED", raw_data={}),
        ]

        filtered = filter_obj.filter(findings, "sonarqube")
        assert len(filtered) == 2
        assert all(f.severity in [Severity.BLOCKER, Severity.CRITICAL] for f in filtered)

    def test_filter_mend_allows_all_levels(self):
        from patchguard.utils.severity import SeverityFilter
        from patchguard.models.finding import Finding, Severity

        filter_obj = SeverityFilter()
        findings = [
            Finding(finding_id="1", source="mend", severity=Severity.CRITICAL,
                   category="DEPENDENCY", file_path="pkg", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="2", source="mend", severity=Severity.HIGH,
                   category="DEPENDENCY", file_path="pkg", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="3", source="mend", severity=Severity.MEDIUM,
                   category="DEPENDENCY", file_path="pkg", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="4", source="mend", severity=Severity.LOW,
                   category="DEPENDENCY", file_path="pkg", message="test",
                   status="QUEUED", raw_data={}),
        ]

        filtered = filter_obj.filter(findings, "mend")
        assert len(filtered) == 4  # All severity levels included

    def test_filter_trivy_allows_critical_high_medium(self):
        from patchguard.utils.severity import SeverityFilter
        from patchguard.models.finding import Finding, Severity

        filter_obj = SeverityFilter()
        findings = [
            Finding(finding_id="1", source="trivy", severity=Severity.CRITICAL,
                   category="VULNERABILITY", file_path="curl", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="2", source="trivy", severity=Severity.HIGH,
                   category="VULNERABILITY", file_path="openssl", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="3", source="trivy", severity=Severity.MEDIUM,
                   category="VULNERABILITY", file_path="libssl", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="4", source="trivy", severity=Severity.LOW,
                   category="VULNERABILITY", file_path="zlib", message="test",
                   status="QUEUED", raw_data={}),
        ]

        filtered = filter_obj.filter(findings, "trivy")
        assert len(filtered) == 3
        assert all(f.severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM] for f in filtered)

    def test_filter_with_custom_thresholds(self):
        from patchguard.utils.severity import SeverityFilter
        from patchguard.models.finding import Finding, Severity

        filter_obj = SeverityFilter()
        findings = [
            Finding(finding_id="1", source="sonarqube", severity=Severity.CRITICAL,
                   category="VULNERABILITY", file_path="test.cs", message="test",
                   status="QUEUED", raw_data={}),
            Finding(finding_id="2", source="sonarqube", severity=Severity.MAJOR,
                   category="BUG", file_path="test.cs", message="test",
                   status="QUEUED", raw_data={}),
        ]

        # Custom threshold: allow CRITICAL and MAJOR
        custom_severities = [Severity.CRITICAL, Severity.MAJOR]
        filtered = filter_obj.filter(findings, "sonarqube", custom_severities)
        assert len(filtered) == 2

    def test_filter_empty_list_returns_empty(self):
        from patchguard.utils.severity import SeverityFilter

        filter_obj = SeverityFilter()
        filtered = filter_obj.filter([], "sonarqube")
        assert filtered == []
