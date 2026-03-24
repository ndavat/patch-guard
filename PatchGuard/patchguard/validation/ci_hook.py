"""CI hook integration for PatchGuard agent."""
import subprocess
import requests
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class CIHook:
    """CI hook integration for triggering and monitoring CI builds.

    Features:
    - Language detection from file extension and content
    - Linter runner registry (flake8, eslint, checkstyle, hadolint)
    - Configurable CI providers (GitHub Actions, GitLab CI, Jenkins)
    - Workflow triggering via API
    - Build result polling with timeout
    - Error feedback loop for LLM self-correction
    """

    def __init__(self, ci_provider: str = "github_actions"):
        """Initialize CI hook.

        Args:
            ci_provider: CI provider ("github_actions", "gitlab_ci", "jenkins")
        """
        self.ci_provider = ci_provider
        self.linters = self._initialize_linters()

    def _initialize_linters(self) -> Dict[str, str]:
        """Initialize linter command registry.

        Returns:
            Dictionary mapping language to linter command
        """
        return {
            "python": "flake8",
            "javascript": "eslint",
            "typescript": "eslint",
            "tsx": "eslint",
            "java": "checkstyle",
            "go": "golint",
            "dockerfile": "hadolint",
            "yaml": "yamllint",
            "yml": "yamllint",
        }

    def detect_language(self, filename: str) -> str:
        """Detect language from file extension.

        Args:
            filename: File name or path

        Returns:
            Language identifier or "unknown"
        """
        # Handle special case files without extensions
        filename_lower = filename.lower()
        if filename_lower == "dockerfile":
            return "dockerfile"

        extension = Path(filename).suffix.lower()

        # Map extensions to languages
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".yml": "yaml",
            ".yaml": "yaml",
        }

        return ext_map.get(extension, "unknown")

    def detect_language_from_content(self, filename: str, content: str) -> str:
        """Detect language from file content (fallback when extension missing).

        Args:
            filename: File name (for context)
            content: File content

        Returns:
            Language identifier or "unknown"
        """
        # First try extension-based detection
        lang = self.detect_language(filename)
        if lang != "unknown":
            return lang

        # Content-based heuristics
        content_lower = content.lower().strip()

        # Python indicators
        if any(indicator in content_lower for indicator in [
            "import ", "from ", "def ", "class ", "if __name__", "print("
        ]):
            return "python"

        # JavaScript/TypeScript indicators
        if any(indicator in content_lower for indicator in [
            "var ", "let ", "const ", "function ", "=>", "console.log",
            "document.", "window."
        ]):
            # Distinguish TS from JS
            if any(indicator in content for indicator in [
                ": string", ": number", ": boolean", "interface ",
                "type ", "export "
            ]):
                return "typescript"
            return "javascript"

        # Java indicators
        if any(indicator in content_lower for indicator in [
            "public class", "private ", "protected ", "static final",
            "import java.", "extends ", "implements "
        ]):
            return "java"

        # Go indicators
        if any(indicator in content_lower for indicator in [
            "package ", "func ", "import ", "go mod", "var "
        ]):
            return "go"

        # Dockerfile indicators
        if content_lower.startswith("from ") or "run " in content_lower:
            return "dockerfile"

        # YAML indicators
        if content_lower.startswith(("---", "...", "apiVersion:", "kind:")):
            return "yaml"

        return "unknown"

    def run_linter(self, language: str, file_path: str) -> Dict[str, Any]:
        """Run linter on a file.

        Args:
            language: Language identifier
            file_path: Path to file to lint

        Returns:
            Dictionary with success status, errors, and warnings
        """
        linter_cmd = self.linters.get(language)
        if not linter_cmd:
            return {
                "success": False,
                "errors": [f"No linter configured for language: {language}"],
                "warnings": []
            }

        try:
            # Run linter command
            result = subprocess.run(
                [linter_cmd, file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse output
            errors = []
            warnings = []

            if result.returncode != 0:
                # Treat all output as errors for simplicity
                # In practice, we'd parse specific linter output formats
                errors = result.stdout.strip().split('\n') if result.stdout else []
                if result.stderr:
                    errors.extend(result.stderr.strip().split('\n'))

            return {
                "success": result.returncode == 0,
                "errors": [e for e in errors if e],  # Filter empty strings
                "warnings": warnings
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": ["Linter execution timed out"],
                "warnings": []
            }
        except FileNotFoundError:
            return {
                "success": False,
                "errors": [f"Linter not found: {linter_cmd}"],
                "warnings": []
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [f"Linter execution failed: {str(e)}"],
                "warnings": []
            }

    def trigger_ci_workflow(
        self,
        repo: str,
        workflow: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Trigger GitHub Actions workflow.

        Args:
            repo: Repository in format "owner/repo"
            workflow: Workflow filename
            ref: Git reference (branch, tag, commit)
            inputs: Workflow inputs

        Returns:
            True if triggered successfully
        """
        if self.ci_provider != "github_actions":
            raise ValueError(f"Method only supports github_actions provider")

        url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}"
        }
        data = {
            "ref": ref,
            "inputs": inputs or {}
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            return response.status_code == 201
        except Exception:
            return False

    def trigger_ci_pipeline(
        self,
        project_id: str,
        ref: str = "main",
        variables: Optional[Dict[str, str]] = None
    ) -> bool:
        """Trigger GitLab CI pipeline.

        Args:
            project_id: GitLab project ID or URL-encoded path
            ref: Git reference (branch, tag, commit)
            variables: CI variables

        Returns:
            True if triggered successfully
        """
        if self.ci_provider != "gitlab_ci":
            raise ValueError(f"Method only supports gitlab_ci provider")

        url = f"https://gitlab.com/api/v4/projects/{project_id}/trigger/pipeline"
        headers = {
            "PRIVATE-TOKEN": os.getenv("GITLAB_TOKEN", "")
        }
        data = {
            "ref": ref,
            "variables": variables or {}
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            return response.status_code == 201
        except Exception:
            return False

    def poll_ci_result(self, url: str, timeout: int = 300) -> Dict[str, Any]:
        """Poll for CI build result.

        Args:
            url: API endpoint to poll for results
            timeout: Maximum time to wait in seconds

        Returns:
            Dictionary with status and success flag
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Handle different CI provider response formats
                    if "conclusion" in data:  # GitHub Actions
                        return {
                            "status": data.get("status", "unknown"),
                            "success": data.get("conclusion") == "success"
                        }
                    elif "status" in data:  # Generic
                        return {
                            "status": data.get("status", "unknown"),
                            "success": data.get("status") == "success"
                        }
            except Exception:
                pass

            time.sleep(10)  # Poll every 10 seconds

        return {
            "status": "timeout",
            "success": False,
            "error": "CI polling timed out"
        }

    def format_linter_errors_for_llm(self, errors: List[str]) -> str:
        """Format linter errors for LLM feedback.

        Args:
            errors: List of linter error messages

        Returns:
            Formatted error message for LLM prompt
        """
        if not errors:
            return "No linting errors found."

        formatted = "The previous fix attempt produced the following linting errors:\n\n"
        for i, error in enumerate(errors[:10], 1):  # Limit to first 10 errors
            formatted += f"{i}. {error}\n"

        if len(errors) > 10:
            formatted += f"\n... and {len(errors) - 10} more errors\n"

        formatted += "\nPlease revise the unified diff to resolve these errors while still fixing the original issue.\n"
        formatted += "Output ONLY the corrected unified diff."
        return formatted
