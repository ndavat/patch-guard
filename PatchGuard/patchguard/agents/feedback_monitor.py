"""Feedback Monitor (Loop 6) for PatchGuard agent.
Monitors PR comments and handles reviewer feedback.
"""
import re
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class PRFeedback:
    """Feedback data for a PR."""
    pr_url: str
    revision_count: int = 0
    last_checked: float = field(default_factory=time.time)
    reviewer_instruction: Optional[str] = None
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, CHANGE_REQUEST, ESCALATED


class FeedbackMonitor:
    """Monitors PR comments for reviewer feedback and handles feedback loop.

    Features:
    - Intent classification (APPROVE, REJECT, CHANGE_REQUEST)
    - PR revision tracking with max revision limit
    - Reviewer instruction extraction
    - Configurable poll interval and max revisions
    - Automatic PR removal after max revisions
    """

    def __init__(self, poll_interval: int = 300, max_revisions: int = 3):
        """Initialize feedback monitor.

        Args:
            poll_interval: Seconds between PR comment polls
            max_revisions: Maximum revision cycles before escalation
        """
        self.poll_interval = poll_interval
        self.max_revisions = max_revisions
        self._monitored_prs: Dict[str, PRFeedback] = {}

        # Intent classification patterns
        self.approve_patterns = [
            r"\b(looks?\s+good|approved?|lgtm|ship\s+it|looks?\s+great|ready\s+to\s+merge)\b",
            r"\b(thanks?|thank\s+you|appreciate it)\b.*\b(good|great|nice|excellent)\b",
            r"\b(looks?\s+fine|works?\s+for\s+me|good\s+to\s+go)\b"
        ]

        self.reject_patterns = [
            r"\b(reject|don't\s+merge|not\s+ready|needs?\s+more\s+work|please\s+revert)\b",
            r"\b(i\s+don't\s+think\s+this|this\s+isn't\s+ready|hold\s+off|wait)\b",
            r"\b(concerns?|issues?|problems?)\b.*\b(serious|major|critical)\b"
        ]

        self.change_request_patterns = [
            r"\b(please\s+|can\s+you\s+|could\s+you\s+|consider\s+|suggest\s+|maybe\s+)",
            r"\b(change|modify|update|fix|improve|enhance|refactor|rename)\b",
            r"\b(add|remove|delete|use\s+instead|should\s+be)\b",
            r"\b(follow|follow\s+the)\b.*\b(guide|standard|style|pattern|convention)\b",
            r"\b(error\s+handling|exception\s+|null\s+check|boundary\s+check)\b",
            r"\b(test|spec|document|comment)\b.*\b(add|update|missing|needed)\b"
        ]

        # Compile regex patterns for performance
        self._approve_re = re.compile("|".join(self.approve_patterns), re.IGNORECASE)
        self._reject_re = re.compile("|".join(self.reject_patterns), re.IGNORECASE)
        self._change_re = re.compile("|".join(self.change_request_patterns), re.IGNORECASE)

    def classify_intent(self, comment: str) -> str:
        """Classify reviewer comment intent.

        Args:
            comment: Reviewer comment text

        Returns:
            Intent: "APPROVE", "REJECT", or "CHANGE_REQUEST"
        """
        if not comment or not comment.strip():
            return "CHANGE_REQUEST"  # Default for empty feedback

        comment_lower = comment.lower().strip()

        # Check for approval patterns
        if self._approve_re.search(comment_lower):
            return "APPROVE"

        # Check for rejection patterns
        if self._reject_re.search(comment_lower):
            return "REJECT"

        # Check for change request patterns
        if self._change_re.search(comment_lower):
            return "CHANGE_REQUEST"

        # Default to change request for ambiguous feedback
        return "CHANGE_REQUEST"

    def get_revision_count(self, pr_url: str) -> int:
        """Get current revision count for a PR.

        Args:
            pr_url: PR URL

        Returns:
            Revision count (0 if PR not being monitored)
        """
        feedback = self._monitored_prs.get(pr_url)
        return feedback.revision_count if feedback else 0

    def record_change_request(self, pr_url: str) -> None:
        """Record a change request for a PR.

        Args:
            pr_url: PR URL
        """
        if pr_url not in self._monitored_prs:
            self._monitored_prs[pr_url] = PRFeedback(pr_url=pr_url)

        self._monitored_prs[pr_url].revision_count += 1
        self._monitored_prs[pr_url].last_checked = time.time()

    def record_approval(self, pr_url: str) -> None:
        """Record approval for a PR.

        Args:
            pr_url: PR URL
        """
        if pr_url in self._monitored_prs:
            self._monitored_prs[pr_url].revision_count = 0  # Reset on approval
            self._monitored_prs[pr_url].status = "APPROVED"
            self._monitored_prs[pr_url].last_checked = time.time()

    def record_rejection(self, pr_url: str) -> None:
        """Record rejection for a PR.

        Args:
            pr_url: PR URL
        """
        if pr_url in self._monitored_prs:
            self._monitored_prs[pr_url].status = "REJECTED"
            self._monitored_prs[pr_url].last_checked = time.time()

    def is_at_max_revisions(self, pr_url: str) -> bool:
        """Check if PR is at maximum revision limit.

        Args:
            pr_url: PR URL

        Returns:
            True if at max revisions, False otherwise
        """
        feedback = self._monitored_prs.get(pr_url)
        if not feedback:
            return False
        return feedback.revision_count >= self.max_revisions

    def should_remove_pr(self, pr_url: str) -> bool:
        """Check if PR should be removed from monitoring.

        Args:
            pr_url: PR URL

        Returns:
            True if PR should be removed, False otherwise
        """
        feedback = self._monitored_prs.get(pr_url)
        if not feedback:
            return False

        # Remove if rejected, approved, or at max revisions
        return (
            feedback.status in ["REJECTED", "APPROVED"] or
            feedback.revision_count >= self.max_revisions
        )

    def extract_instruction(self, comment: str) -> Optional[str]:
        """Extract actionable instruction from reviewer comment.

        Args:
            comment: Reviewer comment text

        Returns:
            Extracted instruction or None if no clear instruction
        """
        if not comment or not comment.strip():
            return None

        # Look for imperative sentences or requests
        instruction_patterns = [
            r"please\s+(.+?)(?:\.|$)",
            r"can\s+you\s+(.+?)(?:\.|$)",
            r"could\s+you\s+(.+?)(?:\.|$)",
            r"(.+?)\s+instead(?:\.|$)",
            r"(.+?)\s+rather\s+than(?:\.|$)",
            r"should\s+be\s+(.+?)(?:\.|$)",
            r"need\s+to\s+(.+?)(?:\.|$)",
            r"must\s+(.+?)(?:\.|$)"
        ]

        for pattern in instruction_patterns:
            match = re.search(pattern, comment, re.IGNORECASE)
            if match:
                instruction = match.group(1).strip()
                if len(instruction) > 5:  # Filter out too-short matches
                    return instruction

        # If no specific pattern found, return first sentence if it's imperative
        sentences = re.split(r'[.!?]+', comment)
        if sentences:
            first_sentence = sentences[0].strip().lower()
            if any(first_sentence.startswith(word) for word in [
                "please", "can you", "could you", "should", "need to", "must"
            ]):
                return sentences[0].strip()

        return None

    def pr_needs_polling(self, pr_url: str) -> bool:
        """Check if PR needs to be polled for new comments.

        Args:
            pr_url: PR URL

        Returns:
            True if PR needs polling, False otherwise
        """
        feedback = self._monitored_prs.get(pr_url)
        if not feedback:
            return False

        # Don't poll if already resolved
        if feedback.status in ["APPROVED", "REJECTED", "ESCALATED"]:
            return False

        # Check if poll interval has elapsed
        return (time.time() - feedback.last_checked) >= self.poll_interval

    def cleanup_resolved_prs(self) -> List[str]:
        """Remove resolved PRs from monitoring.

        Returns:
            List of PR URLs that were removed
        """
        to_remove = []
        for pr_url, feedback in self._monitored_prs.items():
            if self.should_remove_pr(pr_url):
                to_remove.append(pr_url)

        for pr_url in to_remove:
            del self._monitored_prs[pr_url]

        return to_remove

    def get_monitored_prs(self) -> Dict[str, PRFeedback]:
        """Get copy of currently monitored PRs.

        Returns:
            Dictionary of PR URL to PRFeedback
        """
        return self._monitored_prs.copy()
