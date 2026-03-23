"""Tests for Trivy parser — written BEFORE implementation (TDD RED)."""
import pytest


class TestTrivyParser:
    """Test the Trivy parser."""

    def test_parse_returns_list_of_findings(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        assert isinstance(findings, list)

    def test_filters_critical_high_medium_only(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        from patchguard.models.finding import Severity
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        # Should include CRITICAL, HIGH, MEDIUM but not LOW
        for finding in findings:
            assert finding.severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM]

    def test_excludes_low_severity(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        from patchguard.models.finding import Severity
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        # CVE-2024-34567 is LOW severity and should be excluded
        finding_ids = [f.finding_id for f in findings]
        assert "CVE-2024-34567" not in finding_ids

    def test_maps_vulnerability_id(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        for finding in findings:
            assert finding.finding_id.startswith("CVE-")
            assert finding.rule_id == finding.finding_id

    def test_maps_package_info(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        # file_path should be PkgName
        for finding in findings:
            assert finding.file_path is not None
            assert len(finding.file_path) > 0

    def test_maps_fixed_version_to_fix_hint(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        # CVE-2024-38816 has FixedVersion
        curl_finding = [f for f in findings if f.finding_id == "CVE-2024-38816"]
        if curl_finding:
            assert curl_finding[0].fix_hint is not None
            assert "7.81.0-1ubuntu1.16" in curl_finding[0].fix_hint

    def test_missing_fixed_version_sets_fix_hint_none(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        # CVE-2024-45678 has empty FixedVersion
        libc_finding = [f for f in findings if f.finding_id == "CVE-2024-45678"]
        if libc_finding:
            assert libc_finding[0].fix_hint is None

    def test_source_is_trivy(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        for finding in findings:
            assert finding.source == "trivy"

    def test_category_is_vulnerability(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        for finding in findings:
            assert finding.category == "VULNERABILITY"

    def test_empty_results_returns_empty_list(self):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        empty_data = {"Results": []}
        findings = parser.parse(empty_data)
        assert findings == []

    def test_null_vulnerabilities_returns_empty_list(self):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        data = {"Results": [{"Target": "test", "Vulnerabilities": None}]}
        findings = parser.parse(data)
        assert findings == []

    def test_malformed_json_raises_error(self):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        with pytest.raises(ValueError):
            parser.parse("{invalid json")

    def test_missing_results_key_raises_error(self):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        with pytest.raises(ValueError):
            parser.parse({"data": []})

    def test_status_is_queued(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        for finding in findings:
            assert finding.status == "QUEUED"

    def test_message_contains_title(self, trivy_sample):
        from patchguard.parsers.trivy.parser import TrivyParser
        parser = TrivyParser()
        findings = parser.parse(trivy_sample)
        for finding in findings:
            assert finding.message is not None
            assert len(finding.message) > 0
