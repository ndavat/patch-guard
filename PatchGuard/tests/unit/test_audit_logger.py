"""Tests for AuditLogger — written BEFORE implementation (TDD RED)."""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open


class TestAuditLogger:
    """Test AuditLogger functionality."""

    def test_audit_logger_creates_log_file(self):
        """Test that audit logger creates log file on initialization."""
        from patchguard.audit.logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            logger = AuditLogger(str(log_path))

            assert log_path.exists()

    def test_log_event_writes_json_line(self):
        """Test that log_event writes a JSON line to the file."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            logger = AuditLogger(str(log_path))

            logger.log_event(
                event_type=AuditEventType.FINDING_INGESTED,
                finding_id="TEST-001",
                repo="test/repo",
                details={"count": 5}
            )

            # Read and verify
            with open(log_path, "r") as f:
                line = f.readline()
                event = json.loads(line)

                assert event["event_type"] == "FINDING_INGESTED"
                assert event["finding_id"] == "TEST-001"
                assert event["repo"] == "test/repo"
                assert event["details"]["count"] == 5

    def test_log_event_includes_timestamp(self):
        """Test that log events include ISO timestamp."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            logger = AuditLogger(str(log_path))

            logger.log_event(
                event_type=AuditEventType.RISK_CLASSIFIED,
                finding_id="TEST-002"
            )

            with open(log_path, "r") as f:
                event = json.loads(f.readline())
                assert "timestamp" in event
                assert "T" in event["timestamp"]  # ISO format

    def test_log_event_includes_correlation_id(self):
        """Test that events include correlation ID for tracking."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            logger = AuditLogger(str(log_path))

            logger.log_event(
                event_type=AuditEventType.FIX_GENERATED,
                finding_id="TEST-003",
                correlation_id="corr-123"
            )

            with open(log_path, "r") as f:
                event = json.loads(f.readline())
                assert event["correlation_id"] == "corr-123"

    def test_log_event_hashes_sensitive_data(self):
        """Test that sensitive data (LLM prompts) are hashed, not stored."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            logger = AuditLogger(str(log_path))

            logger.log_event(
                event_type=AuditEventType.FIX_GENERATED,
                finding_id="TEST-004",
                prompt="This is a sensitive LLM prompt with PII"
            )

            with open(log_path, "r") as f:
                event = json.loads(f.readline())
                # Should have prompt_hash, not prompt
                assert "prompt_hash" in event
                assert "prompt" not in event
                assert len(event["prompt_hash"]) == 64  # SHA-256 hex

    def test_append_only_mode(self):
        """Test that logger only appends, never overwrites."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"

            # First logger writes event
            logger1 = AuditLogger(str(log_path))
            logger1.log_event(
                event_type=AuditEventType.FINDING_INGESTED,
                finding_id="TEST-005"
            )

            # Second logger should append, not overwrite
            logger2 = AuditLogger(str(log_path))
            logger2.log_event(
                event_type=AuditEventType.RISK_CLASSIFIED,
                finding_id="TEST-006"
            )

            # Should have 2 lines
            with open(log_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2

    def test_log_event_with_outcome(self):
        """Test logging events with outcome field."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            logger = AuditLogger(str(log_path))

            logger.log_event(
                event_type=AuditEventType.VALIDATION_PASSED,
                finding_id="TEST-007",
                outcome="success"
            )

            with open(log_path, "r") as f:
                event = json.loads(f.readline())
                assert event["outcome"] == "success"

    def test_log_event_with_agent_loop(self):
        """Test logging events with agent loop identifier."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            logger = AuditLogger(str(log_path))

            logger.log_event(
                event_type=AuditEventType.CONTEXT_RETRIEVED,
                finding_id="TEST-008",
                agent_loop="Loop3-ContextRetriever"
            )

            with open(log_path, "r") as f:
                event = json.loads(f.readline())
                assert event["agent_loop"] == "Loop3-ContextRetriever"

    def test_stdout_output_mode(self):
        """Test that logger can output to stdout instead of file."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with patch("sys.stdout") as mock_stdout:
            logger = AuditLogger(output="stdout")

            logger.log_event(
                event_type=AuditEventType.PR_CREATED,
                finding_id="TEST-009"
            )

            # Should have written to stdout
            assert mock_stdout.write.called

    def test_multiple_events_same_finding(self):
        """Test logging multiple events for the same finding."""
        from patchguard.audit.logger import AuditLogger
        from patchguard.audit.events import AuditEventType

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            logger = AuditLogger(str(log_path))

            # Log multiple events for same finding
            logger.log_event(
                event_type=AuditEventType.FINDING_INGESTED,
                finding_id="TEST-010"
            )
            logger.log_event(
                event_type=AuditEventType.RISK_CLASSIFIED,
                finding_id="TEST-010"
            )
            logger.log_event(
                event_type=AuditEventType.FIX_GENERATED,
                finding_id="TEST-010"
            )

            # Should have 3 events
            with open(log_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 3

                # All should have same finding_id
                for line in lines:
                    event = json.loads(line)
                    assert event["finding_id"] == "TEST-010"
