"""Tests for GitHubClient — written BEFORE implementation (TDD RED)."""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestGitHubClient:
    """Test GitHubClient functionality."""

    def _create_mocked_client(self):
        """Helper to create a GitHubClient with mocked PyGithub."""
        from patchguard.github.client import GitHubClient

        with patch('patchguard.github.client.Github') as mock_github_class, \
             patch('patchguard.github.client.Auth.Token') as mock_auth_class:
            mock_github = Mock()
            mock_repo = Mock()
            mock_auth = Mock()

            mock_github_class.return_value = mock_github
            mock_auth_class.return_value = mock_auth
            mock_github.get_repo.return_value = mock_repo

            client = GitHubClient("fake_token", "owner/repo")
            return client, mock_repo

    def test_create_branch_from_main(self):
        """Test creating a feature branch from main."""
        client, mock_repo = self._create_mocked_client()

        # Test branch creation
        branch_name = "fix/finding-123-20260323"
        base_sha = "abc123"

        # Mock the base branch reference
        mock_ref = Mock()
        mock_ref.object.sha = base_sha
        mock_repo.get_git_ref.return_value = mock_ref

        # Mock create_git_ref
        new_ref = Mock()
        new_ref.ref = f"refs/heads/{branch_name}"
        mock_repo.create_git_ref.return_value = new_ref

        result = client.create_branch("main", branch_name)

        # Verify the branch was created
        assert result == branch_name
        mock_repo.get_git_ref.assert_called_once_with("heads/main")
        mock_repo.create_git_ref.assert_called_once()

    def test_commit_with_structured_message(self):
        """Test committing fix with structured message."""
        client, mock_repo = self._create_mocked_client()

        # Test data
        branch = "fix/finding-123-20260323"
        file_path = "src/vulnerable.js"
        content = "// Fixed code"
        message = "Fix SQL injection: Use parameterized queries\n\nFinding: SQ-123\nSeverity: CRITICAL"

        # Mock file contents
        mock_contents = Mock()
        mock_contents.sha = "file_sha_123"
        mock_repo.get_contents.return_value = mock_contents

        # Mock commit creation
        mock_repo.update_file.return_value = {
            "commit": Mock(),
            "content": Mock()
        }

        # Call method
        result = client.commit_fix(branch, file_path, content, message)

        # Verify commit was made
        mock_repo.update_file.assert_called_once()
        assert result is not None

    def test_create_pull_request_with_finding(self):
        """Test creating PR with finding details in description."""
        client, mock_repo = self._create_mocked_client()

        mock_pull_request = Mock()
        mock_repo.create_pull.return_value = mock_pull_request

        # Test data
        title = "[CRITICAL] Fix SQL injection: Use parameterized queries"
        body = "Security finding details:\n- ID: SQ-123\n- Severity: CRITICAL\n- File: src/vulnerable.js\n- Description: SQL injection vulnerability"
        head = "fix/finding-123-20260323"
        base = "main"

        # Call method
        result = client.create_pull_request(title, body, head, base)

        # Verify PR was created
        mock_repo.create_pull.assert_called_once_with(
            title=title,
            body=body,
            head=head,
            base=base,
            maintainer_can_modify=True
        )
        assert result == mock_pull_request

    def test_handle_branch_already_exists(self):
        """Test handling branch that already exists."""
        from github import GithubException

        client, mock_repo = self._create_mocked_client()

        # Configure to raise exception when branch already exists
        mock_repo.get_git_ref.side_effect = GithubException(
            status=422,
            data={"message": "Reference already exists"}
        )

        # Test creating branch that already exists
        with pytest.raises(GithubException):
            client.create_branch("main", "existing-branch")

    def test_handle_github_api_error(self):
        """Test handling GitHub API errors."""
        from github import GithubException

        client, mock_repo = self._create_mocked_client()

        # Configure to raise exception
        mock_repo.create_pull.side_effect = GithubException(
            status=403,
            data={"message": "Forbidden"}
        )

        # Test creating PR with API error
        with pytest.raises(GithubException):
            client.create_pull_request("title", "body", "head", "main")

    def test_generate_pr_title_from_finding(self):
        """Test generating PR title from finding details."""
        from patchguard.github.client import GitHubClient
        from patchguard.models.finding import Finding, Severity

        client, _ = self._create_mocked_client()

        # Create test finding
        finding = Finding(
            finding_id="SQ-123",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="src/vulnerable.js",
            message="SQL injection vulnerability",
            status="QUEUED",
            raw_data={}
        )

        # Generate PR title
        title = client.generate_pr_title(finding)

        # Verify title format
        assert "[CRITICAL]" in title
        assert "SQL injection" in title
        assert finding.rule_id is None or finding.rule_id in title or "SQ-123" in title

    def test_generate_pr_description_with_context(self):
        """Test generating PR description with context."""
        from patchguard.github.client import GitHubClient
        from patchguard.models.finding import Finding, Severity
        from patchguard.models.code_context import CodeContext

        client, _ = self._create_mocked_client()

        # Create test finding and context
        finding = Finding(
            finding_id="SQ-123",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="src/vulnerable.js",
            message="SQL injection vulnerability",
            status="QUEUED",
            raw_data={}
        )

        context = CodeContext(
            file_path="src/vulnerable.js",
            language="javascript",
            affected_lines="// Vulnerable code",
            surrounding_code="// Vulnerable code\n// More context",
            imports=[]
        )

        # Generate PR description
        description = client.generate_pr_description(finding, context)

        # Verify description contains key elements
        assert "SQ-123" in description
        assert "sonarqube" in description.lower()
        assert "CRITICAL" in description
        assert "src/vulnerable.js" in description

    def test_add_labels_and_assignees(self):
        """Test adding labels and assignees to PR."""
        client, mock_repo = self._create_mocked_client()

        mock_pull_request = Mock()
        mock_pull_request.add_to_labels = Mock()
        mock_pull_request.add_to_assignees = Mock()

        # Call method
        client.add_labels_and_assignees(
            mock_pull_request,
            ["security", "auto-generated"],
            ["reviewer1"]
        )

        # Verify labels and assignees were added
        mock_pull_request.add_to_labels.assert_called_once_with("security", "auto-generated")
        mock_pull_request.add_to_assignees.assert_called_once_with("reviewer1")