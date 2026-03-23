"""Finding model and Severity enum for normalized security findings."""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Severity levels for security findings."""
    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    MINOR = "MINOR"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Finding:
    """Normalized security finding from any scanning tool.

    All parsers (SonarQube, Mend, Trivy) convert their tool-specific
    JSON into this canonical format for downstream processing.

    Attributes:
        finding_id: Unique identifier (CVE ID, SonarQube key, etc.)
        source: Originating tool (sonarqube, mend, trivy)
        severity: Normalized severity level
        category: Finding type (BUG, VULNERABILITY, DEPENDENCY)
        file_path: Affected file or package name
        message: Description of the issue
        status: Pipeline state (QUEUED, FIX_VALIDATED, PR_OPEN, etc.)
        raw_data: Original tool-specific JSON record
        line_start: Starting line number (if applicable)
        line_end: Ending line number (if applicable)
        fix_hint: Suggested fix or fixed version
        rule_id: Rule or CVE identifier
        risk_level: Classification (LOW, HIGH) set by risk classifier
        risk_reason: Explanation for risk classification
    """
    finding_id: str
    source: str
    severity: Severity
    category: str
    file_path: str
    message: str
    status: str
    raw_data: dict
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    fix_hint: Optional[str] = None
    rule_id: Optional[str] = None
    risk_level: Optional[str] = None
    risk_reason: Optional[str] = None

    def __post_init__(self):
        """Validate field values after initialization."""
        valid_sources = {"sonarqube", "mend", "trivy"}
        if self.source not in valid_sources:
            raise ValueError(
                f"Invalid source '{self.source}'. Must be one of: {valid_sources}"
            )

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"Finding(id={self.finding_id}, source={self.source}, "
            f"severity={self.severity.value}, category={self.category}, "
            f"file={self.file_path})"
        )

    def to_dict(self) -> dict:
        """Convert Finding to dictionary with severity as string value."""
        result = asdict(self)
        result["severity"] = self.severity.value
        return result
