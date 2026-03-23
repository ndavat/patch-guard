"""Language-specific import extractors."""
from typing import List
from abc import ABC, abstractmethod


class ImportExtractor(ABC):
    """Base class for language-specific import extraction."""

    @abstractmethod
    def extract(self, lines: List[str]) -> List[str]:
        """Extract import statements from code lines.

        Args:
            lines: Lines of code

        Returns:
            List of import statements
        """
        pass


class CSharpImportExtractor(ImportExtractor):
    """Extract using statements from C# code."""

    def extract(self, lines: List[str]) -> List[str]:
        """Extract using statements.

        Args:
            lines: Lines of C# code

        Returns:
            List of using statements
        """
        imports = []
        for line in lines:
            stripped = line.strip()
            # Extract using statements, but not using blocks
            if stripped.startswith("using ") and not stripped.startswith("using ("):
                imports.append(stripped)
        return imports


class PythonImportExtractor(ImportExtractor):
    """Extract import statements from Python code."""

    def extract(self, lines: List[str]) -> List[str]:
        """Extract import and from...import statements.

        Args:
            lines: Lines of Python code

        Returns:
            List of import statements
        """
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)
        return imports


class JavaScriptImportExtractor(ImportExtractor):
    """Extract import and require statements from JavaScript/TypeScript code."""

    def extract(self, lines: List[str]) -> List[str]:
        """Extract import and require statements.

        Args:
            lines: Lines of JavaScript/TypeScript code

        Returns:
            List of import/require statements
        """
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import ") or "require(" in stripped:
                imports.append(stripped)
        return imports


class DockerfileImportExtractor(ImportExtractor):
    """Extract FROM statements from Dockerfile."""

    def extract(self, lines: List[str]) -> List[str]:
        """Extract FROM statements.

        Args:
            lines: Lines of Dockerfile

        Returns:
            List of FROM statements
        """
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("FROM "):
                imports.append(stripped)
        return imports


class ImportExtractorFactory:
    """Factory for creating language-specific import extractors."""

    _extractors = {
        "csharp": CSharpImportExtractor,
        "python": PythonImportExtractor,
        "javascript": JavaScriptImportExtractor,
        "typescript": JavaScriptImportExtractor,
        "dockerfile": DockerfileImportExtractor,
    }

    @staticmethod
    def get_extractor(language: str) -> ImportExtractor:
        """Get import extractor for a language.

        Args:
            language: Programming language

        Returns:
            ImportExtractor instance

        Raises:
            ValueError: If language is not supported
        """
        extractor_class = ImportExtractorFactory._extractors.get(language)
        if extractor_class is None:
            # Return a default extractor that returns empty list
            return ImportExtractor.__new__(ImportExtractor)

        return extractor_class()
