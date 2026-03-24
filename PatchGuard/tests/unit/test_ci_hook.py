"""Tests for CI Hook — written BEFORE implementation (TDD RED)."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch


class TestCIHook:
    """Test CI hook functionality."""

    def test_ci_hook_language_detector(self):
        """Test that CI hook can detect language from file extension."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook()

        # Test various file extensions
        test_cases = [
            ("test.py", "python"),
            ("app.js", "javascript"),
            ("component.tsx", "typescript"),
            ("Main.java", "java"),
            ("main.go", "go"),
            ("Dockerfile", "dockerfile"),
            ("docker-compose.yml", "yaml"),
        ]

        for filename, expected_lang in test_cases:
            assert hook.detect_language(filename) == expected_lang

    def test_ci_hook_detects_language_from_content(self):
        """Test that CI hook can detect language from file content."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook()

        # Test language detection from content
        python_content = "#!/usr/bin/env python\nimport os\nprint('hello')"
        assert hook.detect_language_from_content("script", python_content) == "python"

        js_content = "console.log('hello');\nconst x = 5;"
        assert hook.detect_language_from_content("script.js", js_content) == "javascript"

    def test_ci_hook_linter_runner_registry(self):
        """Test that CI hook has linter runner registry."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook()

        # Should have registered linters
        assert "python" in hook.linters
        assert "javascript" in hook.linters
        assert "typescript" in hook.linters
        assert "java" in hook.linters
        assert "go" in hook.linters
        assert "dockerfile" in hook.linters
        assert "yaml" in hook.linters

    def test_ci_hook_run_linter_success(self):
        """Test that CI hook runs linter successfully."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook()

        # Mock successful linter run
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = hook.run_linter("python", "test.py")

            assert result["success"] is True
            assert result["errors"] == []
            assert result["warnings"] == []

    def test_ci_hook_run_linter_failure(self):
        """Test that CI hook runs linter and detects failures."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook()

        # Mock failed linter run
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "test.py:1:1: E1123 Missing comma"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = hook.run_linter("python", "test.py")

            assert result["success"] is False
            assert len(result["errors"]) > 0

    def test_ci_hook_configurable_ci_provider(self):
        """Test that CI hook supports configurable CI providers."""
        from patchguard.validation.ci_hook import CIHook

        # Test with GitHub Actions
        hook = CIHook(ci_provider="github_actions")
        assert hook.ci_provider == "github_actions"

        # Test with GitLab CI
        hook = CIHook(ci_provider="gitlab_ci")
        assert hook.ci_provider == "gitlab_ci"

        # Test with custom provider
        hook = CIHook(ci_provider="jenkins")
        assert hook.ci_provider == "jenkins"

    def test_ci_hook_github_actions_trigger(self):
        """Test that CI hook can trigger GitHub Actions workflow."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook(ci_provider="github_actions")

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_post.return_value = mock_response

            result = hook.trigger_ci_workflow(
                repo="owner/repo",
                workflow="pre-check.yml",
                ref="main",
                inputs={"trigger": "security-scan"}
            )

            assert result is True
            mock_post.assert_called_once()

    def test_ci_hook_gitlab_pipeline_trigger(self):
        """Test that CI hook can trigger GitLab pipeline."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook(ci_provider="gitlab_ci")

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_post.return_value = mock_response

            result = hook.trigger_ci_pipeline(
                project_id="123",
                ref="main",
                variables={"TRIGGER": "security-scan"}
            )

            assert result is True
            mock_post.assert_called_once()

    def test_ci_hook_poll_ci_result_success(self):
        """Test that CI hook can poll for CI results."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook()

        with patch('requests.get') as mock_get:
            # Mock successful CI result
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "conclusion": "success"
            }
            mock_get.return_value = mock_response

            result = hook.poll_ci_result("https://api.github.com/repos/owner/repo/actions/runs/123")

            assert result["status"] == "success"
            assert result["success"] is True

    def test_ci_hook_poll_ci_result_failure(self):
        """Test that CI hook can poll for failed CI results."""
        from patchguard.validation.ci_hook import CIHook

        hook = CIHook()

        with patch('requests.get') as mock_get:
            # Mock failed CI result
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "completed",
                "conclusion": "failure"
            }
            mock_get.return_value = mock_response

            result = hook.poll_ci_result("https://api.github.com/repos/owner/repo/actions/runs/123")

            assert result["status"] == "completed"
            assert result["success"] is False