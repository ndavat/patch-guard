"""Mend parser implementation."""
import json
import re
from typing import List
from patchguard.parsers.base import ToolParser
from patchguard.models.finding import Finding, Severity


class MendParser(ToolParser):
    """Parser for Mend (formerly WhiteSource) scan results."""

    def parse(self, json_data: str | dict) -> List[Finding]:
        """Parse Mend JSON and return normalized Finding objects.

        Filters for:
        - status: ACTIVE only
        - All severity levels: CRITICAL, HIGH, MEDIUM, LOW

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
        for alert in data["alerts"]:
            # Filter by status: only ACTIVE
            if alert.get("status") != "ACTIVE":
                continue

            # Map severity
            severity_str = alert.get("severity", "").upper()
            severity_map = {
                "CRITICAL": Severity.CRITICAL,
                "HIGH": Severity.HIGH,
                "MEDIUM": Severity.MEDIUM,
                "LOW": Severity.LOW
            }
            severity = severity_map.get(severity_str, Severity.LOW)

            # Extract package name from libraryName
            library_name = alert.get("libraryName", "")
            package_name = self._extract_package_name(library_name)

            # Extract fix hint from topFix
            fix_hint = None
            if "topFix" in alert and alert["topFix"]:
                fix_hint = alert["topFix"].get("fixResolution")

            # Build message
            vuln_id = alert.get("vulnerabilityId", "")
            cvss_score = alert.get("cvssScore", "")
            message = f"{vuln_id}: Update {package_name}"
            if cvss_score:
                message += f" (CVSS: {cvss_score})"

            # Create Finding object
            finding = Finding(
                finding_id=vuln_id,
                source="mend",
                severity=severity,
                category="DEPENDENCY",
                file_path=package_name,
                message=message,
                fix_hint=fix_hint,
                rule_id=vuln_id,
                status="QUEUED",
                raw_data=alert
            )
            findings.append(finding)

        return findings

    def validate_schema(self, data: dict) -> bool:
        """Validate that input data matches expected Mend schema.

        Args:
            data: Parsed JSON dict.

        Returns:
            True if valid, raises ValueError otherwise.
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")

        if "alerts" not in data:
            raise ValueError("Missing required 'alerts' key in Mend JSON")

        if not isinstance(data["alerts"], list):
            raise ValueError("'alerts' must be a list")

        return True

    def _extract_package_name(self, library_name: str) -> str:
        """Extract package name from libraryName string.

        libraryName format: "package.name.version.nupkg"
        Returns: "package.name"

        Args:
            library_name: Library name string from Mend alert.

        Returns:
            Package name with version and extension stripped.
        """
        # Remove .nupkg extension
        name = library_name.replace(".nupkg", "")

        # Try to extract package name by removing version pattern
        # Version pattern: ends with numbers and dots (e.g., .4.7.0)
        match = re.match(r"^(.+?)\.(\d+\.)*\d+$", name)
        if match:
            return match.group(1)

        # If no version pattern found, return as-is
        return name
