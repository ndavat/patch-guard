"""Tests for VCS Factory — written BEFORE implementation (TDD RED)."""
import pytest
from unittest.mock import Mock, patch


class TestVCSFactory:
    """Test VCS factory functionality."""

    def test_factory_returns_github_client_for_github_url(self):
        """Test that factory returns GitHubClient for GitHub URLs."""
        from patchguard.vcs.factory import VCSFactory

        factory = VCSFactory()

        # Test various GitHub URL formats
        github_urls = [
            "https://github.com/owner/repo",
            "git@github.com:owner/repo.git",
            "https://github.com/owner/repo.git"
        ]

        with patch('patchguard.github.client.GitHubClient') as mock_github_class:
            mock_client = Mock()
            mock_github_class.return_value = mock_client

            for url in github_urls:
                client = factory.create_client(url, token="fake_token")
                assert client == mock_client

    def test_factory_returns_azure_client_for_azure_url(self):
        """Test that factory returns AzureClient for Azure DevOps URLs."""
        from patchguard.vcs.factory import VCSFactory

        factory = VCSFactory()

        # Test various Azure DevOps URL formats
        azure_urls = [
            "https://dev.azure.com/org/project/_git/repo",
            "https://org.visualstudio.com/project/_git/repo"
        ]

        for url in azure_urls:
            client = factory.create_client(url, token="fake_token")
            assert client.__class__.__name__ == "AzureClient"

    def test_factory_raises_error_for_unsupported_url(self):
        """Test that factory raises error for unsupported VCS URLs."""
        from patchguard.vcs.factory import VCSFactory, UnsupportedVCSError

        factory = VCSFactory()

        with pytest.raises(UnsupportedVCSError):
            factory.create_client("https://bitbucket.org/owner/repo", token="fake_token")

    def test_factory_detects_vcs_type_from_url(self):
        """Test that factory correctly detects VCS type from URL."""
        from patchguard.vcs.factory import VCSFactory

        factory = VCSFactory()

        assert factory.detect_vcs_type("https://github.com/owner/repo") == "github"
        assert factory.detect_vcs_type("https://dev.azure.com/org/project/_git/repo") == "azure"
        assert factory.detect_vcs_type("https://gitlab.com/owner/repo") == "gitlab"

    def test_factory_with_mcp_preference(self):
        """Test that factory prefers MCP client when available."""
        from patchguard.vcs.factory import VCSFactory

        factory = VCSFactory(prefer_mcp=True)

        # When MCP is available, should return MCP client
        with patch('patchguard.vcs.factory.is_mcp_available', return_value=True):
            client = factory.create_client("https://github.com/owner/repo", token="fake_token")
            # Should be MCP client wrapper
            assert hasattr(client, 'mcp_session')

    def test_factory_falls_back_to_rest_when_mcp_unavailable(self):
        """Test that factory falls back to REST API when MCP unavailable."""
        from patchguard.vcs.factory import VCSFactory

        factory = VCSFactory(prefer_mcp=True)

        # When MCP is not available, should fall back to REST
        with patch('patchguard.vcs.factory.is_mcp_available', return_value=False), \
             patch('patchguard.github.client.GitHubClient') as mock_github_class:
            mock_client = Mock()
            mock_github_class.return_value = mock_client

            client = factory.create_client("https://github.com/owner/repo", token="fake_token")
            assert client == mock_client

    def test_factory_caches_clients_per_repo(self):
        """Test that factory caches clients for the same repository."""
        from patchguard.vcs.factory import VCSFactory

        factory = VCSFactory()

        url = "https://github.com/owner/repo"

        with patch('patchguard.github.client.GitHubClient') as mock_github_class:
            mock_client = Mock()
            mock_github_class.return_value = mock_client

            client1 = factory.create_client(url, token="fake_token")
            client2 = factory.create_client(url, token="fake_token")

            # Should return the same instance
            assert client1 is client2
            # Should only create client once
            assert mock_github_class.call_count == 1

    def test_factory_creates_new_client_for_different_repo(self):
        """Test that factory creates new clients for different repositories."""
        from patchguard.vcs.factory import VCSFactory

        factory = VCSFactory()

        with patch('patchguard.github.client.GitHubClient') as mock_github_class:
            mock_client1 = Mock()
            mock_client2 = Mock()
            mock_github_class.side_effect = [mock_client1, mock_client2]

            client1 = factory.create_client("https://github.com/owner/repo1", token="fake_token")
            client2 = factory.create_client("https://github.com/owner/repo2", token="fake_token")

            # Should be different instances
            assert client1 is not client2
            # Should create two clients
            assert mock_github_class.call_count == 2

    def test_factory_supports_gitlab_urls(self):
        """Test that factory recognizes GitLab URLs."""
        from patchguard.vcs.factory import VCSFactory

        factory = VCSFactory()

        gitlab_urls = [
            "https://gitlab.com/owner/repo",
            "https://gitlab.example.com/owner/repo"
        ]

        for url in gitlab_urls:
            vcs_type = factory.detect_vcs_type(url)
            assert vcs_type == "gitlab"
