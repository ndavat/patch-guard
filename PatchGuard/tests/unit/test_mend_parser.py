"""Tests for Mend parser — written BEFORE implementation (TDD RED)."""
import pytest


class TestMendParser:
    """Test the Mend parser."""

    def test_parse_returns_list_of_findings(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        assert isinstance(findings, list)

    def test_filters_active_alerts_only(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        # Should exclude the INACTIVE alert (CVE-2024-88888)
        finding_ids = [f.finding_id for f in findings]
        assert "CVE-2024-88888" not in finding_ids

    def test_includes_all_severity_levels(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        from patchguard.models.finding import Severity
        parser = MendParser()
        findings = parser.parse(mend_sample)
        # Mend processes all severity levels: CRITICAL, HIGH, MEDIUM, LOW
        severities = {f.severity for f in findings}
        assert Severity.CRITICAL in severities
        assert Severity.HIGH in severities
        assert Severity.MEDIUM in severities
        assert Severity.LOW in severities

    def test_extracts_package_name_from_library(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        # libraryName format: "system.drawing.common.4.7.0.nupkg"
        # Should extract package name: "system.drawing.common"
        for finding in findings:
            assert not finding.file_path.endswith(".nupkg")
            # Package names should not contain version numbers at the end
            assert finding.file_path.count(".") <= 3  # Allow dots in package names

    def test_extracts_fix_hint_from_topfix(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        # Most findings should have fix_hint from topFix.fixResolution
        findings_with_fix = [f for f in findings if f.fix_hint is not None]
        assert len(findings_with_fix) > 0
        for finding in findings_with_fix:
            assert "Upgrade to version" in finding.fix_hint or "version" in finding.fix_hint.lower()

    def test_missing_topfix_sets_fix_hint_none(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        # CVE-2024-77777 has no topFix in the fixture
        finding_without_fix = [f for f in findings if f.finding_id == "CVE-2024-77777"]
        if finding_without_fix:
            assert finding_without_fix[0].fix_hint is None

    def test_source_is_mend(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        for finding in findings:
            assert finding.source == "mend"

    def test_category_is_dependency(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        for finding in findings:
            assert finding.category == "DEPENDENCY"

    def test_finding_id_is_vulnerability_id(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        for finding in findings:
            assert finding.finding_id.startswith("CVE-")

    def test_empty_alerts_returns_empty_list(self):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        empty_data = {"alerts": []}
        findings = parser.parse(empty_data)
        assert findings == []

    def test_malformed_json_raises_error(self):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        with pytest.raises(ValueError):
            parser.parse("{invalid json")

    def test_missing_alerts_key_raises_error(self):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        with pytest.raises(ValueError):
            parser.parse({"data": []})

    def test_rule_id_is_vulnerability_id(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        for finding in findings:
            assert finding.rule_id == finding.finding_id

    def test_status_is_queued(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        for finding in findings:
            assert finding.status == "QUEUED"

    def test_message_contains_library_info(self, mend_sample):
        from patchguard.parsers.mend.parser import MendParser
        parser = MendParser()
        findings = parser.parse(mend_sample)
        for finding in findings:
            assert finding.message is not None
            assert len(finding.message) > 0
