"""Prompt templates for LLM fix generation."""

SQL_INJECTION_TEMPLATE = """You are a security expert tasked with fixing a SQL injection vulnerability.

## Vulnerability Details
- Finding ID: {finding_id}
- File: {file_path}
- Line: {line_number}
- Severity: {severity}
- Rule: {rule_id}

## Current Code
```{language}
{affected_lines}
```

## Surrounding Context (±50 lines)
```{language}
{surrounding_code}
```

## Imports
{imports}

## Fix Instructions
This code is vulnerable to SQL injection. You must:
1. Replace string concatenation with parameterized queries
2. Use proper parameter binding (SqlParameter for C#, prepared statements for others)
3. Ensure all user input is properly sanitized
4. Maintain the same functionality

## Output Format
Provide ONLY a unified diff in the following format:
```diff
--- a/{file_path}
+++ b/{file_path}
@@ -line,count +line,count @@
-old line
+new line
```

Generate the fix now:"""

DEPENDENCY_UPGRADE_TEMPLATE = """You are a dependency management expert tasked with upgrading a vulnerable package.

## Vulnerability Details
- CVE: {finding_id}
- Package: {package_name}
- Current Version: {current_version}
- Fixed Version: {fixed_version}
- Severity: {severity}

## Fix Instructions
Update the package version in the appropriate manifest file:
- For .csproj: Update <PackageReference> version attribute
- For package.json: Update version in dependencies
- For requirements.txt: Update version specification
- For Dockerfile: Update base image tag

## Output Format
Provide ONLY a unified diff showing the version change.

Generate the fix now:"""

COOKIE_SECURITY_TEMPLATE = """You are a security expert tasked with fixing insecure cookie configuration.

## Vulnerability Details
- Finding ID: {finding_id}
- File: {file_path}
- Line: {line_number}
- Issue: Cookie created without secure flags

## Current Code
```{language}
{affected_lines}
```

## Surrounding Context
```{language}
{surrounding_code}
```

## Fix Instructions
Add the following security flags to the cookie:
1. HttpOnly = true (prevents XSS access)
2. Secure = true (HTTPS only)
3. SameSite = SameSiteMode.Strict (prevents CSRF)

## Output Format
Provide ONLY a unified diff.

Generate the fix now:"""

GENERIC_TEMPLATE = """You are a code quality expert tasked with fixing a security or quality issue.

## Issue Details
- Finding ID: {finding_id}
- File: {file_path}
- Line: {line_number}
- Severity: {severity}
- Category: {category}
- Message: {message}

## Current Code
```{language}
{affected_lines}
```

## Surrounding Context (±50 lines)
```{language}
{surrounding_code}
```

## Imports
{imports}

## Fix Hint
{fix_hint}

## Fix Instructions
1. Analyze the issue described in the message
2. Apply the fix hint if provided
3. Ensure the fix doesn't break existing functionality
4. Follow language-specific best practices
5. Maintain code style and formatting

## Output Format
Provide ONLY a unified diff in the following format:
```diff
--- a/{file_path}
+++ b/{file_path}
@@ -line,count +line,count @@
-old line
+new line
```

Generate the fix now:"""

RETRY_TEMPLATE = """The previous fix attempt failed linter validation. Please fix the issues and try again.

## Original Prompt
{original_prompt}

## Linter Errors
```
{linter_errors}
```

## Instructions
1. Analyze the linter errors
2. Fix the issues in your diff
3. Ensure the code passes linting
4. Maintain the original fix intent

## Output Format
Provide ONLY a unified diff (no explanations).

Generate the corrected fix now:"""


class PromptTemplates:
    """Container for prompt templates."""

    @staticmethod
    def get_template(finding_type: str) -> str:
        """Get appropriate template for finding type.

        Args:
            finding_type: Type of finding (sql_injection, dependency, cookie, generic)

        Returns:
            Prompt template string
        """
        templates = {
            "sql_injection": SQL_INJECTION_TEMPLATE,
            "dependency": DEPENDENCY_UPGRADE_TEMPLATE,
            "cookie_security": COOKIE_SECURITY_TEMPLATE,
            "generic": GENERIC_TEMPLATE,
        }
        return templates.get(finding_type, GENERIC_TEMPLATE)

    @staticmethod
    def get_retry_template() -> str:
        """Get retry template for self-correction."""
        return RETRY_TEMPLATE
