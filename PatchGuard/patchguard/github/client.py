"""GitHub client for creating pull requests with security fixes."""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from github import Github, Auth
from github.GithubException import GithubException
from patchguard.models.finding import Finding
from patchguard.models.code_context import CodeContext
from patchguard.models.fix_result import FixResult


class GitHubClient:
    """GitHub API client for creating pull requests with security fixes."""

    def __init__(self, token: Optional[str] = None, repo_name: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token. If None, will try to read from GITHUB_TOKEN env var.
            repo_name: Repository name in format 'owner/repo'. If None, will try to read from GITHUB_REPO env var.
        """
        if token is None:
            token = os.getenv('GITHUB_TOKEN')

        if repo_name is None:
            repo_name = os.getenv('GITHUB_REPO')

        if not token:
            raise ValueError("GitHub token must be provided either as parameter or GITHUB_TOKEN environment variable")

        if not repo_name:
            raise ValueError("Repository name must be provided either as parameter or GITHUB_REPO environment variable")

        self.auth = Auth.Token(token)
        self.github = Github(auth=self.auth)
        self.repo = self.github.get_repo(repo_name)

    def create_branch(self, base_branch: str, branch_name: str) -> str:
        """Create a feature branch from the base branch.

        Args:
            base_branch: The base branch to create from (e.g., 'main')
            branch_name: The name of the new branch to create

        Returns:
            The name of the created branch

        Raises:
            GithubException: If the branch already exists or other GitHub API error occurs
        """
        try:
            # Get the base branch reference
            base_ref = self.repo.get_git_ref(f"heads/{base_branch}")

            # Create new branch
            new_ref = self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_ref.object.sha
            )

            return branch_name
        except GithubException as e:
            if e.status == 422 and "already exists" in str(e.data):
                raise GithubException(422, f"Branch '{branch_name}' already exists")
            raise

    def commit_fix(self, branch: str, file_path: str, content: str, message: str) -> Dict[str, Any]:
        """Commit a fixed file to the specified branch.

        Args:
            branch: The branch to commit to
            file_path: Path to the file in the repository
            content: New content for the file
            message: Commit message

        Returns:
            Dictionary with commit information
        """
        try:
            # Get current file content to get the SHA
            contents = self.repo.get_contents(file_path, ref=branch)

            # Update the file
            result = self.repo.update_file(
                path=file_path,
                message=message,
                content=content,
                sha=contents.sha,
                branch=branch
            )

            return result
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist, create it instead
                result = self.repo.create_file(
                    path=file_path,
                    message=message,
                    content=content,
                    branch=branch
                )
                return result
            raise

    def create_pull_request(self, title: str, body: str, head_branch: str, base_branch: str = "main") -> Any:
        """Create a pull request.

        Args:
            title: PR title
            body: PR description
            head_branch: Source branch (feature branch)
            base_branch: Target branch (default: main)

        Returns:
            PullRequest object
        """
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
                maintainer_can_modify=True
            )
            return pr
        except GithubException as e:
            raise

    def generate_pr_title(self, finding: Finding) -> str:
        """Generate a standardized PR title from finding details.

        Args:
            finding: The security finding to create PR for

        Returns:
            Formatted PR title
        """
        return f"[{finding.severity.value}] Fix {finding.rule_id}: {finding.message[:50]}"

    def generate_pr_description(self, finding: Finding, context: CodeContext, fix_result: Optional[FixResult] = None) -> str:
        """Generate a detailed PR description with finding information.

        Args:
            finding: The security finding
            context: Code context around the finding
            fix_result: Optional fix result with additional details

        Returns:
            Formatted PR description
        """
        description = f"""## Security Finding Details
- **ID**: {finding.finding_id}
- **Source**: {finding.source}
- **Severity**: {finding.severity.value}
- **Category**: {finding.category}
- **File**: {finding.file_path}
- **Rule**: {finding.rule_id or 'N/A'}
- **Message**: {finding.message}

## Fix Applied
"""

        if fix_result and fix_result.diff:
            description += f"""
### Changes Made
```diff
{fix_result.diff}
```
"""
        else:
            description += """
Changes applied based on security recommendation.
"""

        if finding.fix_hint:
            description += f"""
## Recommended Fix
{finding.fix_hint}
"""

        description += f"""
## Original Code Context
```{context.language}
{context.affected_lines}
```

---
*Automated security fix generated by PatchGuard*
"""
        return description

    def add_labels_and_assignees(self, pull_request: Any, labels: List[str], assignees: List[str]) -> None:
        """Add labels and assignees to a pull request.

        Args:
            pull_request: GitHub PullRequest object
            labels: List of label names to add
            assignees: List of GitHub usernames to assign
        """
        try:
            # Add labels
            if labels:
                pull_request.add_to_labels(*labels)

            # Add assignees
            if assignees:
                pull_request.add_to_assignees(*assignees)

        except GithubException as e:
            # Log the error but don't fail the entire operation
            print(f"Warning: Could not add labels/assignees: {e}")

    def close(self):
        """Close the GitHub client connection."""
        self.github.close()