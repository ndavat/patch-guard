"""VCS client factory for creating appropriate VCS clients based on repository URL."""
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class UnsupportedVCSError(Exception):
    """Raised when VCS type is not supported."""
    pass


def is_mcp_available() -> bool:
    """Check if MCP client is available.

    Returns:
        True if MCP is available, False otherwise
    """
    try:
        # Try to import MCP client
        from patchguard.vcs.mcp_client import MCPClient
        return True
    except ImportError:
        return False


class VCSFactory:
    """Factory for creating VCS clients based on repository URL.

    Supports:
    - GitHub (via PyGithub or MCP)
    - Azure DevOps (via REST API or MCP)
    - GitLab (via REST API)

    Features:
    - Automatic VCS type detection from URL
    - Client caching per repository
    - MCP preference with REST API fallback
    """

    def __init__(self, prefer_mcp: bool = False):
        """Initialize VCS factory.

        Args:
            prefer_mcp: Prefer MCP client over REST API when available
        """
        self.prefer_mcp = prefer_mcp
        self._client_cache: Dict[str, Any] = {}

    def detect_vcs_type(self, repo_url: str) -> str:
        """Detect VCS type from repository URL.

        Args:
            repo_url: Repository URL

        Returns:
            VCS type: "github", "azure", or "gitlab"

        Raises:
            UnsupportedVCSError: If VCS type cannot be determined
        """
        # Handle SSH-style Git URLs
        if repo_url.startswith("git@"):
            # Extract host from git@host:path format
            host_part = repo_url.split("@")[1].split(":")[0]
            host = host_part.lower()
        else:
            # Handle HTTP/HTTPS URLs
            parsed = urlparse(repo_url)
            host = parsed.netloc.lower()

        # GitHub detection
        if "github.com" in host:
            return "github"

        # Azure DevOps detection
        if "dev.azure.com" in host or "visualstudio.com" in host:
            return "azure"

        # GitLab detection
        if "gitlab.com" in host or "gitlab" in host:
            return "gitlab"

        raise UnsupportedVCSError(f"Unsupported VCS URL: {repo_url}")

    def create_client(self, repo_url: str, token: str, **kwargs) -> Any:
        """Create appropriate VCS client for the repository.

        Args:
            repo_url: Repository URL
            token: Authentication token
            **kwargs: Additional client-specific arguments

        Returns:
            VCS client instance

        Raises:
            UnsupportedVCSError: If VCS type is not supported
        """
        # Check cache first
        cache_key = f"{repo_url}:{token[:8]}"
        if cache_key in self._client_cache:
            return self._client_cache[cache_key]

        # Detect VCS type
        vcs_type = self.detect_vcs_type(repo_url)

        # Create client based on type and MCP preference
        if self.prefer_mcp and is_mcp_available():
            client = self._create_mcp_client(vcs_type, repo_url, token, **kwargs)
        else:
            client = self._create_rest_client(vcs_type, repo_url, token, **kwargs)

        # Cache the client
        self._client_cache[cache_key] = client

        return client

    def _create_mcp_client(self, vcs_type: str, repo_url: str, token: str, **kwargs) -> Any:
        """Create MCP client wrapper.

        Args:
            vcs_type: VCS type
            repo_url: Repository URL
            token: Authentication token
            **kwargs: Additional arguments

        Returns:
            MCP client instance
        """
        from patchguard.vcs.mcp_client import MCPClient

        return MCPClient(vcs_type=vcs_type, repo_url=repo_url, token=token, **kwargs)

    def _create_rest_client(self, vcs_type: str, repo_url: str, token: str, **kwargs) -> Any:
        """Create REST API client.

        Args:
            vcs_type: VCS type
            repo_url: Repository URL
            token: Authentication token
            **kwargs: Additional arguments

        Returns:
            REST API client instance

        Raises:
            UnsupportedVCSError: If VCS type is not supported
        """
        if vcs_type == "github":
            from patchguard.github.client import GitHubClient

            # Extract owner/repo from URL
            repo_name = self._extract_github_repo(repo_url)
            return GitHubClient(token=token, repo_name=repo_name)

        elif vcs_type == "azure":
            from patchguard.vcs.azure_client import AzureClient

            return AzureClient(token=token, repo_url=repo_url)

        elif vcs_type == "gitlab":
            # GitLab client not implemented yet
            raise UnsupportedVCSError(f"GitLab support not implemented yet")

        else:
            raise UnsupportedVCSError(f"Unsupported VCS type: {vcs_type}")

    def _extract_github_repo(self, repo_url: str) -> str:
        """Extract owner/repo from GitHub URL.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Repository name in format "owner/repo"
        """
        # Handle SSH-style Git URLs
        if repo_url.startswith("git@"):
            # Format: git@github.com:owner/repo
            match = re.search(r"github\.com:([^/]+)/([^/\.]+)", repo_url)
            if match:
                owner, repo = match.groups()
                return f"{owner}/{repo}"
        else:
            # Handle HTTP/HTTPS URLs
            patterns = [
                r"github\.com[:/]([^/]+)/([^/\.]+)",  # https://github.com/owner/repo
            ]

            for pattern in patterns:
                match = re.search(pattern, repo_url)
                if match:
                    owner, repo = match.groups()
                    return f"{owner}/{repo}"

        raise ValueError(f"Could not extract repository name from URL: {repo_url}")
