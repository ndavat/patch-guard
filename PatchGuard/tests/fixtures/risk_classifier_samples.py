"""Test fixtures for risk classifier testing."""
from patchguard.models.finding import Finding, Severity


# Low risk samples - should be classified as safe to auto-fix
LOW_RISK_SAMPLES = [
    # Direct dependency upgrade with fix available
    Finding(
        finding_id="CVE-2024-30105",
        source="mend",
        severity=Severity.HIGH,
        category="DEPENDENCY",
        file_path="system.text.json",
        message="CVE-2024-30105: Update system.text.json (CVSS: 7.5)",
        fix_hint="Upgrade to version System.Text.Json - 8.0.4",
        rule_id="CVE-2024-30105",
        status="QUEUED",
        raw_data={}
    ),

    # Trivy vulnerability with fixed version
    Finding(
        finding_id="CVE-2024-38816",
        source="trivy",
        severity=Severity.CRITICAL,
        category="VULNERABILITY",
        file_path="curl",
        message="CVE-2024-38816: curl: HSTS subdomain overwrites parent cache entry (installed: 7.81.0-1ubuntu1.15)",
        fix_hint="Upgrade to version 7.81.0-1ubuntu1.16",
        rule_id="CVE-2024-38816",
        status="QUEUED",
        raw_data={}
    ),

    # SQL injection with known pattern
    Finding(
        finding_id="AZrN_test001",
        source="sonarqube",
        severity=Severity.CRITICAL,
        category="VULNERABILITY",
        file_path="Controllers/UserController.cs",
        line_start=42,
        line_end=42,
        message="Make sure this SQL injection is safe here.",
        rule_id="csharpsquid:S3649",
        status="QUEUED",
        raw_data={}
    ),

    # Single file simple fix with line number and hint
    Finding(
        finding_id="AZrN_test004",
        source="sonarqube",
        severity=Severity.MAJOR,
        category="CODE_SMELL",
        file_path="Helpers/StringHelper.cs",
        line_start=67,
        line_end=67,
        message="Remove this commented out code.",
        fix_hint="Delete commented code",
        rule_id="csharpsquid:S125",
        status="QUEUED",
        raw_data={}
    ),
]


# High risk samples - should be flagged for manual review
HIGH_RISK_SAMPLES = [
    # No fixed version available
    Finding(
        finding_id="CVE-2024-45678",
        source="trivy",
        severity=Severity.CRITICAL,
        category="VULNERABILITY",
        file_path="libc6",
        message="CVE-2024-45678: libc6: Remote code execution vulnerability (installed: 2.35-0ubuntu3.4)",
        fix_hint=None,
        rule_id="CVE-2024-45678",
        status="QUEUED",
        raw_data={}
    ),

    # Authentication-related file
    Finding(
        finding_id="AZrN_auth001",
        source="sonarqube",
        severity=Severity.CRITICAL,
        category="VULNERABILITY",
        file_path="Middleware/AuthMiddleware.cs",
        line_start=28,
        message="Make sure creating this cookie without the \"secure\" flag is safe.",
        rule_id="csharpsquid:S2092",
        status="QUEUED",
        raw_data={}
    ),

    # Login controller
    Finding(
        finding_id="AZrN_login001",
        source="sonarqube",
        severity=Severity.BLOCKER,
        category="BUG",
        file_path="Controllers/LoginController.cs",
        line_start=105,
        message="Null pointer exception in login flow",
        status="QUEUED",
        raw_data={}
    ),

    # Session management
    Finding(
        finding_id="AZrN_session001",
        source="sonarqube",
        severity=Severity.CRITICAL,
        category="VULNERABILITY",
        file_path="Services/SessionService.cs",
        message="Session fixation vulnerability",
        status="QUEUED",
        raw_data={}
    ),

    # Transitive dependency without fix
    Finding(
        finding_id="CVE-2024-99999",
        source="mend",
        severity=Severity.HIGH,
        category="DEPENDENCY",
        file_path="transitive.package",
        message="CVE-2024-99999: Transitive dependency vulnerability",
        fix_hint=None,
        rule_id="CVE-2024-99999",
        status="QUEUED",
        raw_data={}
    ),
]
