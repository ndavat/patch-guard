"""Severity filter utility for filtering findings by severity level."""
from typing import List, Optional
from patchguard.models.finding import Finding, Severity


class SeverityFilter:
    """Filter findings based on tool-specific severity thresholds."""

    # Default severity configurations per tool (matching severity.txt files)
    DEFAULT_SEVERITIES = {
        "sonarqube": [Severity.BLOCKER, Severity.CRITICAL],
        "mend": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW],
        "trivy": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM],
    }

    def filter(
        self,
        findings: List[Finding],
        tool: str,
        custom_severities: Optional[List[Severity]] = None
    ) -> List[Finding]:
        """Filter findings by allowed severity levels for the given tool.

        Args:
            findings: List of Finding objects to filter.
            tool: Tool name (sonarqube, mend, trivy).
            custom_severities: Optional custom severity list to override defaults.

        Returns:
            Filtered list of Finding objects.
        """
        if not findings:
            return []

        # Use custom severities if provided, otherwise use defaults
        allowed_severities = custom_severities or self.DEFAULT_SEVERITIES.get(tool, [])

        # Filter findings by severity
        filtered = [f for f in findings if f.severity in allowed_severities]

        return filtered
