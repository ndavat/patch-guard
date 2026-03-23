"""SonarQube parser implementation."""
import json
from typing import List
from patchguard.parsers.base import ToolParser
from patchguard.models.finding import Finding, Severity


class SonarQubeParser(ToolParser):
    """Parser for SonarQube scan results."""

    def parse(self, json_data: str | dict) -> List[Finding]:
        """Parse SonarQube JSON and return normalized Finding objects.

        Filters for:
        - type: BUG or VULNERABILITY only
        - severity: BLOCKER or CRITICAL only

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
        for issue in data["issues"]:
            # Filter by type: only BUG and VULNERABILITY
            if issue.get("type") not in ["BUG", "VULNERABILITY"]:
                continue

            # Filter by severity: only BLOCKER and CRITICAL
            if issue.get("severity") not in ["BLOCKER", "CRITICAL"]:
                continue

            # Map severity
            severity_str = issue["severity"]
            severity = Severity.BLOCKER if severity_str == "BLOCKER" else Severity.CRITICAL

            # Extract file path from component (strip project prefix)
            component = issue.get("component", "")
            file_path = self._extract_file_path(component)

            # Create Finding object
            finding = Finding(
                finding_id=issue["key"],
                source="sonarqube",
                severity=severity,
                category=issue["type"],
                file_path=file_path,
                line_start=issue.get("line"),
                line_end=issue.get("line"),
                message=issue.get("message", ""),
                rule_id=issue.get("rule"),
                status="QUEUED",
                raw_data=issue
            )
            findings.append(finding)

        return findings

    def validate_schema(self, data: dict) -> bool:
        """Validate that input data matches expected SonarQube schema.

        Args:
            data: Parsed JSON dict.

        Returns:
            True if valid, raises ValueError otherwise.
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")

        if "issues" not in data:
            raise ValueError("Missing required 'issues' key in SonarQube JSON")

        if not isinstance(data["issues"], list):
            raise ValueError("'issues' must be a list")

        return True

    def _extract_file_path(self, component: str) -> str:
        """Extract file path from component string.

        Component format: "ProjectName:Path/To/File.cs"
        Returns: "Path/To/File.cs"

        Args:
            component: Component string from SonarQube issue.

        Returns:
            File path with project prefix stripped.
        """
        if ":" in component:
            return component.split(":", 1)[1]
        return component
