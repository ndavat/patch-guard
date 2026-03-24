"""Audit event type definitions."""
from enum import Enum


class AuditEventType(Enum):
    """Audit event types for tracking agent actions."""

    # Ingestion events
    FINDING_INGESTED = "FINDING_INGESTED"
    INGESTION_FAILED = "INGESTION_FAILED"

    # Risk classification events
    RISK_CLASSIFIED = "RISK_CLASSIFIED"
    RISK_CLASSIFICATION_FAILED = "RISK_CLASSIFICATION_FAILED"

    # Context retrieval events
    CONTEXT_RETRIEVED = "CONTEXT_RETRIEVED"
    CONTEXT_RETRIEVAL_FAILED = "CONTEXT_RETRIEVAL_FAILED"

    # Fix generation events
    FIX_GENERATED = "FIX_GENERATED"
    FIX_GENERATION_FAILED = "FIX_GENERATION_FAILED"

    # Validation events
    VALIDATION_PASSED = "VALIDATION_PASSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"

    # PR automation events
    PR_CREATED = "PR_CREATED"
    PR_CREATION_FAILED = "PR_CREATION_FAILED"
    PR_COMMENT_RECEIVED = "PR_COMMENT_RECEIVED"

    # Feedback events
    FIX_AMENDED = "FIX_AMENDED"
    FIX_SKIPPED = "FIX_SKIPPED"
    FIX_FAILED = "FIX_FAILED"
    FIX_ESCALATED = "FIX_ESCALATED"
