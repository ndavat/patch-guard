"""Language detection from file extensions."""
import os


class LanguageDetector:
    """Detect programming language from file path."""

    EXTENSIONS = {
        ".cs": "csharp",
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".dockerfile": "dockerfile",
    }

    FILENAMES = {
        "Dockerfile": "dockerfile",
        "dockerfile": "dockerfile",
    }

    @staticmethod
    def detect(file_path: str) -> str:
        """Detect language from file extension or filename.

        Args:
            file_path: Path to the file

        Returns:
            Language identifier (e.g., "csharp", "python", "dockerfile")
            Returns "unknown" if language cannot be determined
        """
        # Check filename first (for Dockerfile)
        basename = os.path.basename(file_path)
        if basename in LanguageDetector.FILENAMES:
            return LanguageDetector.FILENAMES[basename]

        # Check extension
        _, ext = os.path.splitext(file_path)
        return LanguageDetector.EXTENSIONS.get(ext.lower(), "unknown")
