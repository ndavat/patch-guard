"""Context retriever for extracting code context from source files."""
import os
from typing import List, Optional
from patchguard.models.finding import Finding
from patchguard.models.code_context import CodeContext
from patchguard.utils.language_detector import LanguageDetector


class ContextRetriever:
    """Retrieves code context from source files for LLM fix generation."""

    def __init__(self, repo_root: str = "."):
        """Initialize retriever with repository root.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self._file_cache = {}

    def retrieve(self, finding: Finding) -> CodeContext:
        """Retrieve code context for a finding.

        Args:
            finding: Finding object to retrieve context for

        Returns:
            CodeContext object with extracted information
        """
        # For dependency findings, return minimal context
        if finding.category == "DEPENDENCY":
            return self._dependency_context(finding)

        # For code findings, read file and extract context
        return self._code_context(finding)

    def _dependency_context(self, finding: Finding) -> CodeContext:
        """Create minimal context for dependency findings.

        Args:
            finding: Dependency finding

        Returns:
            CodeContext with minimal information
        """
        return CodeContext(
            file_path=finding.file_path,
            language="dependency",
            affected_lines=finding.message,
            surrounding_code=f"Package: {finding.file_path}\nFix: {finding.fix_hint or 'No fix available'}",
            imports=[],
        )

    def _code_context(self, finding: Finding) -> CodeContext:
        """Extract context from source file.

        Args:
            finding: Code finding with file path and line number

        Returns:
            CodeContext with extracted code and metadata
        """
        file_path = os.path.join(self.repo_root, finding.file_path)
        language = LanguageDetector.detect(finding.file_path)

        # Try to read file
        try:
            lines = self._read_file(file_path)
        except FileNotFoundError:
            # Return error context if file not found
            return CodeContext(
                file_path=finding.file_path,
                language=language,
                affected_lines="File not found",
                surrounding_code=f"Error: File '{finding.file_path}' not found",
                imports=[],
            )

        # Extract imports
        imports = self._extract_imports(lines, language)

        # Handle missing line number
        if finding.line_start is None:
            # Return full file for small files, or first 100 lines
            surrounding = "\n".join(lines[:100])
            affected = "No specific line number"
            full_file = "\n".join(lines) if len(lines) < 100 else None
        else:
            # Extract ±50 lines around affected line
            line_num = finding.line_start - 1  # Convert to 0-indexed
            start = max(0, line_num - 50)
            end = min(len(lines), line_num + 51)

            surrounding = "\n".join(lines[start:end])
            affected = lines[line_num] if line_num < len(lines) else "Line out of bounds"

            # Include full file for small files
            full_file = "\n".join(lines) if len(lines) < 100 else None

        return CodeContext(
            file_path=finding.file_path,
            language=language,
            affected_lines=affected,
            surrounding_code=surrounding,
            imports=imports,
            full_file=full_file,
        )

    def _read_file(self, file_path: str) -> List[str]:
        """Read file and return lines, with caching.

        Args:
            file_path: Path to file

        Returns:
            List of lines in the file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        # Check cache first
        if file_path in self._file_cache:
            return self._file_cache[file_path]

        # Read file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()

        # Cache result
        self._file_cache[file_path] = lines
        return lines

    def _extract_imports(self, lines: List[str], language: str) -> List[str]:
        """Extract import statements from code.

        Args:
            lines: Lines of code
            language: Programming language

        Returns:
            List of import statements
        """
        imports = []

        if language == "csharp":
            # Extract using statements
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("using ") and not stripped.startswith("using ("):
                    imports.append(stripped)
        elif language == "python":
            # Extract import and from...import statements
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    imports.append(stripped)
        elif language in ["javascript", "typescript"]:
            # Extract import and require statements
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or "require(" in stripped:
                    imports.append(stripped)
        elif language == "dockerfile":
            # Extract FROM statements
            for line in lines:
                stripped = line.strip()
                if stripped.upper().startswith("FROM "):
                    imports.append(stripped)

        return imports
