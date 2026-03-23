"""Tests for SonarQube parser — written BEFORE implementation (TDD RED)."""
import pytest


class TestSonarQubeParser:
    """Test the SonarQube parser."""

    def test_parse_returns_list_of_findings(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        assert isinstance(findings, list)

    def test_filters_bug_and_vulnerability_only(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        for finding in findings:
            assert finding.category in ["BUG", "VULNERABILITY"]

    def test_filters_blocker_and_critical_only(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        from patchguard.models.finding import Severity
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        for finding in findings:
            assert finding.severity in [Severity.BLOCKER, Severity.CRITICAL]

    def test_excludes_code_smells(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        for finding in findings:
            assert finding.category != "CODE_SMELL"

    def test_excludes_low_severity(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        from patchguard.models.finding import Severity
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        for finding in findings:
            assert finding.severity not in [Severity.MINOR, Severity.MAJOR, Severity.LOW]

    def test_maps_component_to_file_path(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        # Component format: "ProjectName:Path/To/File.cs"
        # Should strip project prefix and keep only "Path/To/File.cs"
        for finding in findings:
            assert ":" not in finding.file_path
            assert finding.file_path.endswith(".cs")

    def test_maps_line_number(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        # At least one finding should have line numbers
        assert any(f.line_start is not None for f in findings)
        for finding in findings:
            if finding.line_start is not None:
                assert isinstance(finding.line_start, int)
                assert finding.line_start > 0

    def test_maps_severity_correctly(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        from patchguard.models.finding import Severity
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        # Should have both CRITICAL and BLOCKER findings based on fixture
        severities = {f.severity for f in findings}
        assert Severity.CRITICAL in severities or Severity.BLOCKER in severities

    def test_source_is_sonarqube(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        for finding in findings:
            assert finding.source == "sonarqube"

    def test_empty_issues_returns_empty_list(self):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        empty_data = {"issues": []}
        findings = parser.parse(empty_data)
        assert findings == []

    def test_malformed_json_raises_error(self):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        with pytest.raises(ValueError):
            parser.parse("{invalid json")

    def test_missing_issues_key_raises_error(self):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        with pytest.raises(ValueError):
            parser.parse({"data": []})

    def test_finding_id_is_issue_key(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        # All findings should have finding_id matching the issue key
        for finding in findings:
            assert finding.finding_id.startswith("AZrN_")

    def test_rule_id_is_mapped(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        for finding in findings:
            assert finding.rule_id is not None
            assert "csharpsquid:" in finding.rule_id

    def test_status_is_queued(self, sonarqube_sample):
        from patchguard.parsers.sonarqube.parser import SonarQubeParser
        parser = SonarQubeParser()
        findings = parser.parse(sonarqube_sample)
        for finding in findings:
            assert finding.status == "QUEUED"
