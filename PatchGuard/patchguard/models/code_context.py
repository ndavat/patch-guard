"""Code context model for LLM fix generation."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CodeContext:
    """Code context extracted from source files for LLM fix generation.

    Attributes:
        file_path: Path to the source file
        language: Programming language (csharp, python, javascript, dockerfile)
        affected_lines: The specific lines with the issue
        surrounding_code: ±50 lines around the affected area
        imports: List of import/using statements
        class_name: Name of containing class (if applicable)
        method_name: Name of containing method (if applicable)
        full_file: Full file content for small files (<100 lines)
    """
    file_path: str
    language: str
    affected_lines: str
    surrounding_code: str
    imports: List[str]
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    full_file: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert CodeContext to dictionary."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "affected_lines": self.affected_lines,
            "surrounding_code": self.surrounding_code,
            "imports": self.imports,
            "class_name": self.class_name,
            "method_name": self.method_name,
            "full_file": self.full_file,
        }
