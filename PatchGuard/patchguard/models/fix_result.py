"""Fix result model for LLM-generated fixes."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class FixResult:
    """Result of LLM fix generation attempt.

    Attributes:
        finding_id: ID of the finding that was fixed
        success: Whether the fix was successfully generated and validated
        diff: Unified diff of the changes (if successful)
        modified_code: Full modified code after applying diff
        linter_output: Output from linter validation
        attempts: Number of attempts made (for self-correction tracking)
        error_message: Error message if fix generation failed
    """
    finding_id: str
    success: bool
    diff: Optional[str] = None
    modified_code: Optional[str] = None
    linter_output: Optional[str] = None
    attempts: int = 1
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert FixResult to dictionary."""
        return {
            "finding_id": self.finding_id,
            "success": self.success,
            "diff": self.diff,
            "modified_code": self.modified_code,
            "linter_output": self.linter_output,
            "attempts": self.attempts,
            "error_message": self.error_message,
        }
