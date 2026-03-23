"""Risk policy configuration for Safe-to-Fix evaluation."""
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple
from patchguard.models.finding import Finding


@dataclass
class RiskRule:
    """A single risk evaluation rule.

    Attributes:
        name: Human-readable rule name
        condition: Function that evaluates if rule applies to a finding
        risk_level: "LOW" or "HIGH"
        reason: Explanation for why this rule classifies as LOW/HIGH risk
    """
    name: str
    condition: Callable[[Finding], bool]
    risk_level: str
    reason: str


class SafeToFixPolicy:
    """Policy engine for evaluating if a finding is safe to auto-fix.

    Rules are evaluated in order. First matching rule determines risk level.
    If no rules match, defaults to HIGH risk (safe default).
    """

    def __init__(self, rules: Optional[List[RiskRule]] = None):
        """Initialize policy with custom or default rules.

        Args:
            rules: List of RiskRule objects. If None, uses default rules.
        """
        self.rules = rules if rules is not None else self._default_rules()

    def evaluate(self, finding: Finding) -> Tuple[str, str]:
        """Evaluate a finding against all rules.

        Args:
            finding: Finding object to evaluate

        Returns:
            Tuple of (risk_level, reason) where risk_level is "LOW" or "HIGH"
        """
        for rule in self.rules:
            if rule.condition(finding):
                return (rule.risk_level, rule.reason)

        # Default to HIGH risk if no rules match (safe default)
        return ("HIGH", "No matching rule - defaulting to HIGH risk for safety")

    @staticmethod
    def _default_rules() -> List[RiskRule]:
        """Return default Safe-to-Fix policy rules.

        Rules are evaluated in order. First match wins.
        """
        return [
            # Rule 1: Direct dependency upgrade with fix available
            RiskRule(
                name="Direct Dependency Upgrade",
                condition=lambda f: (
                    f.source in ["mend", "trivy"] and
                    f.category in ["DEPENDENCY", "VULNERABILITY"] and
                    f.fix_hint is not None and
                    len(f.fix_hint) > 0
                ),
                risk_level="LOW",
                reason="Direct dependency upgrade with known fixed version"
            ),

            # Rule 2: SQL injection with known pattern (SonarQube S3649)
            RiskRule(
                name="SQL Injection Pattern",
                condition=lambda f: (
                    f.source == "sonarqube" and
                    f.rule_id is not None and
                    "S3649" in f.rule_id
                ),
                risk_level="LOW",
                reason="SQL injection with known fix pattern (parameterized queries)"
            ),

            # Rule 3: Authentication/authorization related files
            RiskRule(
                name="Auth Flow Change",
                condition=lambda f: any(
                    keyword in f.file_path.lower()
                    for keyword in ["auth", "login", "session", "token", "credential"]
                ),
                risk_level="HIGH",
                reason="Changes to authentication/authorization code require manual review"
            ),

            # Rule 4: Single file, simple fix (SonarQube with line numbers)
            RiskRule(
                name="Single File Simple Fix",
                condition=lambda f: (
                    f.source == "sonarqube" and
                    f.line_start is not None and
                    f.fix_hint is not None
                ),
                risk_level="LOW",
                reason="Single file fix with clear location and fix hint"
            ),

            # Rule 5: No fix available (Catch-all for missing hints)
            RiskRule(
                name="No Fix Available",
                condition=lambda f: (
                    f.fix_hint is None or len(f.fix_hint) == 0
                ),
                risk_level="HIGH",
                reason="No fixed version or fix hint available"
            ),
        ]

    @classmethod
    def default(cls) -> "SafeToFixPolicy":
        """Create a policy with default rules."""
        return cls()
