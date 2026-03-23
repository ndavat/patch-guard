"""Trivy parser implementation."""
import json
from typing import List
from patchguard.parsers.base import ToolParser
from patchguard.models.finding import Finding, Severity


class TrivyParser(ToolParser):
    """Parser for Trivy container vulnerability scan results."""

    def parse(self, json_data: str | dict) -> List[Finding]:
        """Parse Trivy JSON and return normalized Finding objects.

        Filters for:
        - Severity: CRITICAL, HIGH, MEDIUM only (excludes LOW)

        Args:
            json_data: Either a JSON string or already-parsed dict.

        Returns:
            List of normalized Finding objects.

        Raises:
            ValueError: If the input is malformed or missing required fields.
        """
        # Parse JSON string if needed
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        else:
            data = json_data

        # Validate schema
        self.validate_schema(data)

        findings = []
        for result in data["Results"]:
            vulnerabilities = result.get("Vulnerabilities")
            if not vulnerabilities:
                continue

            for vuln in vulnerabilities:
                # Filter by severity: CRITICAL, HIGH, MEDIUM only
                severity_str = vuln.get("Severity", "").upper()
                if severity_str not in ["CRITICAL", "HIGH", "MEDIUM"]:
                    continue

                # Map severity
                severity_map = {
                    "CRITICAL": Severity.CRITICAL,
                    "HIGH": Severity.HIGH,
                    "MEDIUM": Severity.MEDIUM
                }
                severity = severity_map.get(severity_str, Severity.MEDIUM)

                # Extract package name
                pkg_name = vuln.get("PkgName", "")

                # Extract fix hint from FixedVersion
                fixed_version = vuln.get("FixedVersion", "")
                fix_hint = None
                if fixed_version:
                    fix_hint = f"Upgrade to version {fixed_version}"

                # Build message
                vuln_id = vuln.get("VulnerabilityID", "")
                title = vuln.get("Title", vuln.get("Description", ""))
                installed_version = vuln.get("InstalledVersion", "")
                message = f"{vuln_id}: {title}"
                if installed_version:
                    message += f" (installed: {installed_version})"

                # Create Finding object
                finding = Finding(
                    finding_id=vuln_id,
                    source="trivy",
                    severity=severity,
                    category="VULNERABILITY",
                    file_path=pkg_name,
                    message=message,
                    fix_hint=fix_hint,
                    rule_id=vuln_id,
                    status="QUEUED",
                    raw_data=vuln
                )
                findings.append(finding)

        return findings

    def validate_schema(self, data: dict) -> bool:
        """Validate that input data matches expected Trivy schema.

        Args:
            data: Parsed JSON dict.

        Returns:
            True if valid, raises ValueError otherwise.
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")

        if "Results" not in data:
            raise ValueError("Missing required 'Results' key in Trivy JSON")

        if not isinstance(data["Results"], list):
            raise ValueError("'Results' must be a list")

        return True
