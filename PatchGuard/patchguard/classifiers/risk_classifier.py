"""Risk classifier for evaluating findings against Safe-to-Fix policy."""
from typing import List
from patchguard.models.finding import Finding
from patchguard.config.risk_policy import SafeToFixPolicy


class RiskClassifier:
    """Classifier that evaluates findings and assigns risk levels.

    Uses a SafeToFixPolicy to determine if a finding is safe to auto-fix (LOW risk)
    or requires manual review (HIGH risk).
    """

    def __init__(self, policy: SafeToFixPolicy = None):
        """Initialize classifier with a policy.

        Args:
            policy: SafeToFixPolicy instance. If None, uses default policy.
        """
        self.policy = policy if policy is not None else SafeToFixPolicy.default()

    def classify(self, finding: Finding) -> Finding:
        """Evaluate a finding and set its risk_level field.

        Args:
            finding: Finding object to classify

        Returns:
            The same Finding object with risk_level and risk_reason fields set
        """
        risk_level, reason = self.policy.evaluate(finding)
        finding.risk_level = risk_level
        finding.risk_reason = reason
        return finding

    def classify_batch(self, findings: List[Finding]) -> List[Finding]:
        """Classify multiple findings.

        Args:
            findings: List of Finding objects to classify

        Returns:
            List of Finding objects with risk_level and risk_reason fields set
        """
        return [self.classify(f) for f in findings]
