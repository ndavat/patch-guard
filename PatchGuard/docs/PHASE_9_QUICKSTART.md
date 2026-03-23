# Phase 9: PR Automation - Quick Start Guide

**Status**: Ready to begin
**Estimated Duration**: 3-4 hours
**Dependencies**: Phase 8 (COMPLETE ✅)

## Overview

Phase 9 automates the creation of pull requests with generated fixes. The pipeline will:
1. Take FixResult from Phase 8
2. Create a feature branch
3. Commit the fix with structured message
4. Create a pull request with finding details
5. Link to the original security finding

## Architecture

```
FixResult (from Phase 8)
    ↓
GitHubClient (new)
    ├── create_branch()
    ├── commit_fix()
    └── create_pull_request()
    ↓
Pull Request with:
- Finding details in description
- Link to security tool
- Suggested reviewers
- Labels (security, auto-generated)
```

## Tasks for Phase 9

### Task 9.1: GitHub Client Tests (RED)
**File**: `tests/unit/test_github_client.py`

Test cases needed:
```python
def test_create_branch_from_main()
def test_commit_with_structured_message()
def test_create_pull_request_with_finding()
def test_handle_branch_already_exists()
def test_handle_github_api_error()
def test_generate_pr_title_from_finding()
def test_generate_pr_description_with_context()
def test_add_labels_and_assignees()
```

### Task 9.2: GitHub Client Implementation (GREEN)
**File**: `patchguard/github/client.py`

Components:
- GitHubClient class with PyGithub integration
- Branch creation with naming convention: `fix/finding-{id}-{timestamp}`
- Commit message format: `Fix {rule_id}: {message}\n\nFinding: {finding_id}\nSeverity: {severity}`
- PR creation with finding details in description
- Error handling for rate limits, auth failures

### Task 9.3: PR Generator Tests (RED)
**File**: `tests/unit/test_pr_generator.py`

Test cases:
```python
def test_generate_pr_from_fix_result()
def test_pr_title_generation()
def test_pr_description_with_finding_details()
def test_handle_multiple_files_in_fix()
def test_skip_pr_for_failed_fixes()
def test_pr_with_suggested_reviewers()
```

### Task 9.4: PR Generator Implementation (GREEN)
**File**: `patchguard/github/pr_generator.py`

Components:
- PRGenerator class orchestrating the flow
- Title generation: `[{severity}] Fix {rule_id}: {message}`
- Description template with finding details, context, and fix explanation
- Reviewer suggestion based on file ownership
- Label assignment (security, auto-generated, {severity})

### Task 9.5: Integration Tests (RED/GREEN)
**File**: `tests/integration/test_phase9_pr_automation.py`

Test cases:
```python
def test_end_to_end_fix_to_pr()
def test_multiple_findings_multiple_prs()
def test_pr_with_code_review_comments()
def test_handle_merge_conflicts()
def test_pr_status_tracking()
```

## Implementation Strategy

### Step 1: Setup GitHub Integration
```python
# patchguard/github/__init__.py
from .client import GitHubClient
from .pr_generator import PRGenerator

# patchguard/github/client.py
class GitHubClient:
    def __init__(self, token: str, repo: str):
        self.repo = Github(token).get_repo(repo)

    def create_branch(self, base: str, branch_name: str) -> str:
        """Create feature branch from base"""

    def commit_fix(self, branch: str, file_path: str, content: str, message: str):
        """Commit fix to branch"""

    def create_pull_request(self, title: str, body: str, head: str, base: str = "main"):
        """Create PR with details"""
```

### Step 2: PR Generation
```python
# patchguard/github/pr_generator.py
class PRGenerator:
    def __init__(self, github_client: GitHubClient):
        self.client = github_client

    def generate_pr(self, fix_result: FixResult, finding: Finding, context: CodeContext) -> dict:
        """Generate PR from fix result"""
        # 1. Create branch
        # 2. Commit fix
        # 3. Create PR
        # 4. Return PR details
```

### Step 3: Testing Strategy
- Mock GitHub API responses
- Test branch naming conventions
- Test commit message formatting
- Test PR description generation
- Test error handling (rate limits, auth)

## Dependencies

### New External Library
```
PyGithub>=1.55
```

Add to `requirements.txt`:
```
PyGithub>=1.55
```

### Environment Variables
```
GITHUB_TOKEN=<personal access token>
GITHUB_REPO=<owner/repo>
```

## Success Criteria

- [ ] All 8 unit tests passing
- [ ] All 5 integration tests passing
- [ ] PR creation works end-to-end
- [ ] Proper error handling for GitHub API failures
- [ ] Branch naming follows convention
- [ ] Commit messages are well-formatted
- [ ] PR descriptions include finding details
- [ ] Labels and assignees are set correctly

## Known Considerations

1. **Rate Limiting**: GitHub API has rate limits (60 req/hr unauthenticated, 5000 req/hr authenticated)
2. **Branch Naming**: Use timestamp to avoid conflicts
3. **Merge Conflicts**: Handle gracefully (don't create PR if conflicts detected)
4. **Permissions**: Ensure token has repo write access
5. **Reviewers**: Suggest based on file history or CODEOWNERS

## Next Phase (Phase 10)

After Phase 9 completes, Phase 10 will:
- Monitor PR comments
- Classify reviewer feedback
- Regenerate fixes based on feedback
- Escalate after 3 failed cycles

---

**Ready to begin Phase 9?** Run: `pytest tests/unit/test_github_client.py -v` (will fail - RED phase)
