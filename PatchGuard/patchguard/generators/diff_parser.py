"""Diff parser for handling unified diffs from LLM responses."""
import re
from typing import Dict, List


class DiffError(Exception):
    """Exception raised when diff parsing fails."""
    pass


class DiffParser:
    """Parser for unified diff format and application to source code."""

    def parse(self, diff_text: str) -> Dict:
        """Parse unified diff text.

        Args:
            diff_text: Unified diff as string

        Returns:
            Dictionary with parsed diff information

        Raises:
            DiffError: If diff format is invalid
        """
        if not diff_text.strip():
            raise DiffError("Empty diff text")

        # Basic validation - should contain diff markers
        if "---" not in diff_text or "+++" not in diff_text:
            raise DiffError("Invalid diff format: missing --- or +++ markers")

        # Extract file path from diff header
        file_path = self._extract_file_path(diff_text)

        return {
            "file_path": file_path,
            "changes": diff_text,
            "raw_diff": diff_text
        }

    def apply(self, original_code: str, diff_text: str) -> str:
        """Apply unified diff to original code.

        Args:
            original_code: Original source code
            diff_text: Unified diff to apply

        Returns:
            Modified code after applying diff

        Raises:
            DiffError: If diff cannot be applied
        """
        try:
            # Simple diff application - replace old lines with new lines
            lines = original_code.splitlines()

            # Extract changes from diff
            changes = self._extract_changes(diff_text)

            # Apply changes (simple implementation)
            for old_line, new_line in changes:
                if old_line in original_code:
                    original_code = original_code.replace(old_line, new_line)

            return original_code
        except Exception as e:
            raise DiffError(f"Failed to apply diff: {e}")

    def extract_from_markdown(self, response: str) -> str:
        """Extract diff from markdown code blocks.

        Args:
            response: LLM response containing diff in markdown

        Returns:
            Extracted diff text

        Raises:
            DiffError: If no diff found in response
        """
        # Look for ```diff blocks
        diff_pattern = r'```diff\n(.*?)\n```'
        match = re.search(diff_pattern, response, re.DOTALL)

        if match:
            return match.group(1)

        # Look for generic ``` blocks that contain diff markers
        code_pattern = r'```[a-z]*\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)

        for code_block in matches:
            if "---" in code_block and "+++" in code_block:
                return code_block

        # If no code blocks, look for diff markers directly
        if "---" in response and "+++" in response:
            # Extract everything from first --- to end of diff
            lines = response.splitlines()
            diff_start = -1
            for i, line in enumerate(lines):
                if line.startswith("---"):
                    diff_start = i
                    break

            if diff_start >= 0:
                # Find end of diff (empty line or non-diff content)
                diff_lines = []
                for i in range(diff_start, len(lines)):
                    line = lines[i]
                    if line.startswith(("---", "+++", "@@", "+", "-", " ")) or line == "":
                        diff_lines.append(line)
                    else:
                        break
                return "\n".join(diff_lines)

        raise DiffError("No diff found in response")

    def _extract_file_path(self, diff_text: str) -> str:
        """Extract file path from diff header.

        Args:
            diff_text: Unified diff text

        Returns:
            File path extracted from diff header
        """
        # Look for +++ b/filename pattern
        plus_match = re.search(r'\+\+\+ b/(.+)', diff_text)
        if plus_match:
            return plus_match.group(1)

        # Look for --- a/filename pattern
        minus_match = re.search(r'--- a/(.+)', diff_text)
        if minus_match:
            return minus_match.group(1)

        return "unknown_file"

    def _extract_changes(self, diff_text: str) -> List[tuple]:
        """Extract line changes from diff.

        Args:
            diff_text: Unified diff text

        Returns:
            List of (old_line, new_line) tuples
        """
        changes = []
        lines = diff_text.splitlines()

        current_old = []
        current_new = []

        for line in lines:
            if line.startswith("-") and not line.startswith("---"):
                current_old.append(line[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                current_new.append(line[1:])
            elif line.startswith("@@"):
                if current_old or current_new:
                    changes.extend(zip(current_old, current_new))
                    current_old = []
                    current_new = []

        if current_old or current_new:
            changes.extend(zip(current_old, current_new))

        return changes