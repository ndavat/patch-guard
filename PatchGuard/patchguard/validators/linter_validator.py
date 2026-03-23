"""Linter validator for validating generated fixes."""
import subprocess
import tempfile
import os
from typing import Tuple


class LinterValidator:
    """Validates code using language-specific linters."""

    LINTERS = {
        "python": ["flake8", "--max-line-length=120"],
        "javascript": ["eslint", "--format=compact"],
        "typescript": ["eslint", "--format=compact"],
        "csharp": ["dotnet", "format", "--verify-no-changes"],
        "dockerfile": ["hadolint"],
    }

    def validate(self, code: str, language: str) -> Tuple[bool, str]:
        """Validate code using appropriate linter.

        Args:
            code: Code to validate
            language: Programming language

        Returns:
            Tuple of (is_valid, output_message)
        """
        if not code.strip():
            return True, "Empty code - validation skipped"

        if language not in self.LINTERS:
            return True, f"No linter configured for {language}"

        try:
            return self._run_linter(code, language)
        except Exception as e:
            # If linter fails to run, assume it's not installed
            return True, f"Linter not available for {language}: {e}"

    def _run_linter(self, code: str, language: str) -> Tuple[bool, str]:
        """Run linter on code.

        Args:
            code: Code to lint
            language: Programming language

        Returns:
            Tuple of (is_valid, linter_output)
        """
        linter_cmd = self.LINTERS[language]

        # Write code to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=self._get_file_extension(language),
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            tmp_file.write(code)
            tmp_path = tmp_file.name

        try:
            # Run linter
            result = subprocess.run(
                linter_cmd + [tmp_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse linter output
            is_valid = result.returncode == 0
            output = result.stdout + result.stderr

            return is_valid, output.strip()

        except subprocess.TimeoutExpired:
            return False, "Linter timeout"
        except FileNotFoundError:
            return True, f"Linter {linter_cmd[0]} not installed"
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language.

        Args:
            language: Programming language

        Returns:
            File extension
        """
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "csharp": ".cs",
            "dockerfile": ".dockerfile",
        }
        return extensions.get(language, ".txt")