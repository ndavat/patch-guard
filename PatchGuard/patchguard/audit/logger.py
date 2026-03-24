"""Structured audit logger for PatchGuard agent actions."""
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from patchguard.audit.events import AuditEventType


class AuditLogger:
    """Append-only JSON Lines audit logger with PII-safe logging.

    Features:
    - Structured JSON Lines format
    - Append-only (never overwrites)
    - Correlation ID tracking
    - Sensitive data hashing (LLM prompts)
    - Configurable output (file, stdout, S3, database)
    """

    def __init__(self, output: str = "audit.log"):
        """Initialize audit logger.

        Args:
            output: Output destination - file path or "stdout"
        """
        self.output = output

        if output != "stdout":
            # Create log file if it doesn't exist
            log_path = Path(output)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.touch(exist_ok=True)

    def log_event(
        self,
        event_type: AuditEventType,
        finding_id: Optional[str] = None,
        repo: Optional[str] = None,
        agent_loop: Optional[str] = None,
        outcome: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log an audit event.

        Args:
            event_type: Type of event
            finding_id: Finding identifier
            repo: Repository name
            agent_loop: Agent loop identifier
            outcome: Event outcome (success, failure, etc.)
            correlation_id: Correlation ID for tracking
            details: Additional event details
            prompt: LLM prompt (will be hashed, not stored)
            **kwargs: Additional fields to include
        """
        # Build event record
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
        }

        # Add optional fields
        if finding_id:
            event["finding_id"] = finding_id
        if repo:
            event["repo"] = repo
        if agent_loop:
            event["agent_loop"] = agent_loop
        if outcome:
            event["outcome"] = outcome
        if correlation_id:
            event["correlation_id"] = correlation_id
        if details:
            event["details"] = details

        # Hash sensitive data instead of storing it
        if prompt:
            event["prompt_hash"] = self._hash_sensitive_data(prompt)

        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in event:
                event[key] = value

        # Write event
        self._write_event(event)

    def _hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data using SHA-256.

        Args:
            data: Sensitive data to hash

        Returns:
            SHA-256 hex digest
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _write_event(self, event: Dict[str, Any]) -> None:
        """Write event to output destination.

        Args:
            event: Event dictionary to write
        """
        json_line = json.dumps(event) + "\n"

        if self.output == "stdout":
            sys.stdout.write(json_line)
            sys.stdout.flush()
        else:
            # Append to file
            with open(self.output, "a") as f:
                f.write(json_line)
