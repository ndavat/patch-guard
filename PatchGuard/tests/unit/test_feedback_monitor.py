"""Tests for Feedback Monitor — written BEFORE implementation (TDD RED)."""
import pytest
import time
from unittest.mock import Mock, patch


class TestFeedbackMonitor:
    """Test Feedback Monitor functionality."""

    def test_feedback_monitor_initialization(self):
        """Test that feedback monitor initializes correctly."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor(poll_interval=30)

        assert monitor.poll_interval == 30
        assert monitor.max_revisions == 3
        assert monitor._monitored_prs == {}

    def test_feedback_monitor_classifies_approve_intent(self):
        """Test that feedback monitor classifies APPROVE intent."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor()

        approve_comments = [
            "Looks good to me!",
            "Approved",
            "LGTM",
            "This looks ready to merge",
            "Ship it!",
            "Looks great, thanks!"
        ]

        for comment in approve_comments:
            intent = monitor.classify_intent(comment)
            assert intent == "APPROVE", f"Failed for comment: {comment}"

    def test_feedback_monitor_classifies_reject_intent(self):
        """Test that feedback monitor classifies REJECT intent."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor()

        reject_comments = [
            "I don't think this is ready",
            "Please don't merge this yet",
            "This needs more work",
            "Reject",
            "Not ready for production",
            "Please revert this change"
        ]

        for comment in reject_comments:
            intent = monitor.classify_intent(comment)
            assert intent == "REJECT", f"Failed for comment: {comment}"

    def test_feedback_monitor_classifies_change_request_intent(self):
        """Test that feedback monitor classifies CHANGE_REQUEST intent."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor()

        change_comments = [
            "Please use a different variable name",
            "Can you add error handling here?",
            "This should use the factory pattern instead",
            "Consider using a more efficient algorithm",
            "Please follow the PEP 8 style guide",
            "The fix is in the wrong location",
            "Need to update the tests as well",
            "Please add documentation for this change"
        ]

        for comment in change_comments:
            intent = monitor.classify_intent(comment)
            assert intent == "CHANGE_REQUEST", f"Failed for comment: {comment}"

    def test_feedback_monitor_handles_ambiguous_comments(self):
        """Test that feedback monitor handles ambiguous comments."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor()

        ambiguous_comments = [
            "Thanks!",
            "Interesting approach",
            "Let me think about this",
            "I'll get back to you",
            "",
            "Maybe"
        ]

        for comment in ambiguous_comments:
            intent = monitor.classify_intent(comment)
            # Should default to CHANGE_REQUEST for ambiguous feedback
            assert intent in ["CHANGE_REQUEST", "APPROVE"], f"Failed for comment: {comment}"

    def test_feedback_monitor_tracks_pr_revisions(self):
        """Test that feedback monitor tracks PR revision counts."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor(max_revisions=2)

        pr_url = "https://github.com/owner/repo/pull/123"

        # Initial state
        assert monitor.get_revision_count(pr_url) == 0

        # After first change request
        monitor.record_change_request(pr_url)
        assert monitor.get_revision_count(pr_url) == 1

        # After second change request
        monitor.record_change_request(pr_url)
        assert monitor.get_revision_count(pr_url) == 2

        # Should be at max revisions
        assert monitor.is_at_max_revisions(pr_url) is True

    def test_feedback_monitor_resets_revision_on_approve(self):
        """Test that feedback monitor resets revision count on approval."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor(max_revisions=3)

        pr_url = "https://github.com/owner/repo/pull/123"

        # Record some change requests
        monitor.record_change_request(pr_url)
        monitor.record_change_request(pr_url)
        assert monitor.get_revision_count(pr_url) == 2

        # Record approval
        monitor.record_approval(pr_url)
        assert monitor.get_revision_count(pr_url) == 0  # Reset on approval

    def test_feedback_monitor_removes_pr_after_max_revisions(self):
        """Test that feedback monitor removes PR after max revisions."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor(max_revisions=2)

        pr_url = "https://github.com/owner/repo/pull/123"

        # Reach max revisions
        monitor.record_change_request(pr_url)
        monitor.record_change_request(pr_url)
        assert monitor.is_at_max_revisions(pr_url) is True

        # Should be marked for removal
        assert monitor.should_remove_pr(pr_url) is True

    def test_feedback_monitor_extracts_reviewer_instructions(self):
        """Test that feedback monitor extracts reviewer instructions."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor()

        comment = "Please change the variable name from 'x' to 'count' and add error handling"
        instruction = monitor.extract_instruction(comment)

        assert "variable name" in instruction
        assert "error handling" in instruction

    def test_feedback_monitor_handles_empty_comments(self):
        """Test that feedback monitor handles empty or whitespace-only comments."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor = FeedbackMonitor()

        empty_comments = ["", "   ", "\n\t", None]

        for comment in empty_comments:
            if comment is None:
                continue  # Skip None as it would cause different error
            intent = monitor.classify_intent(comment or "")
            assert intent == "CHANGE_REQUEST"  # Default for empty feedback

    def test_feedback_monitor_poll_interval_configuration(self):
        """Test that feedback monitor accepts custom poll interval."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor_1min = FeedbackMonitor(poll_interval=60)
        monitor_5min = FeedbackMonitor(poll_interval=300)
        monitor_15min = FeedbackMonitor(poll_interval=900)

        assert monitor_1min.poll_interval == 60
        assert monitor_5min.poll_interval == 300
        assert monitor_15min.poll_interval == 900

    def test_feedback_monitor_max_revisions_configuration(self):
        """Test that feedback monitor accepts custom max revisions."""
        from patchguard.agents.feedback_monitor import FeedbackMonitor

        monitor_default = FeedbackMonitor()
        monitor_custom = FeedbackMonitor(max_revisions=5)

        assert monitor_default.max_revisions == 3
        assert monitor_custom.max_revisions == 5