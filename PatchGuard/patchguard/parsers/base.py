"""Abstract base class for all tool-specific parsers."""
from abc import ABC, abstractmethod
from typing import List
from patchguard.models.finding import Finding


class ToolParser(ABC):
    """Base parser interface. All tool parsers must implement this."""

    @abstractmethod
    def parse(self, json_data: str | dict) -> List[Finding]:
        """Parse tool-specific JSON and return normalized Finding objects.

        Args:
            json_data: Either a JSON string or already-parsed dict.

        Returns:
            List of normalized Finding objects.

        Raises:
            ValueError: If the input is malformed or missing required fields.
        """
        ...

    @abstractmethod
    def validate_schema(self, data: dict) -> bool:
        """Validate that input data matches expected schema.

        Args:
            data: Parsed JSON dict.

        Returns:
            True if valid, raises ValueError otherwise.
        """
        ...
