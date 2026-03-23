"""Prompt builder for LLM fix generation."""
from patchguard.models.finding import Finding
from patchguard.models.code_context import CodeContext
from patchguard.prompts.templates import PromptTemplates


class PromptBuilder:
    """Builds prompts for LLM fix generation."""

    def build(self, finding: Finding, context: CodeContext) -> str:
        """Build LLM prompt with finding and context.

        Args:
            finding: Finding to fix
            context: Code context around the finding

        Returns:
            Formatted prompt string
        """
        # Determine finding type
        finding_type = self._determine_type(finding)

        # Get appropriate template
        template = PromptTemplates.get_template(finding_type)

        # Format imports
        imports_str = "\n".join(context.imports) if context.imports else "No imports"

        # Build prompt
        prompt = template.format(
            finding_id=finding.finding_id,
            file_path=context.file_path,
            line_number=finding.line_start or "N/A",
            severity=finding.severity.value,
            rule_id=finding.rule_id or "N/A",
            language=context.language,
            affected_lines=context.affected_lines,
            surrounding_code=context.surrounding_code,
            imports=imports_str,
            category=finding.category,
            message=finding.message,
            fix_hint=finding.fix_hint or "No specific hint provided",
            package_name=context.file_path if finding.category == "DEPENDENCY" else "N/A",
            current_version="N/A",
            fixed_version=finding.fix_hint or "N/A",
        )

        return prompt

    def build_retry(self, original_prompt: str, linter_error: str) -> str:
        """Build retry prompt with linter error.

        Args:
            original_prompt: Original prompt that failed
            linter_error: Error message from linter

        Returns:
            Retry prompt with error context
        """
        template = PromptTemplates.get_retry_template()
        return template.format(
            original_prompt=original_prompt,
            linter_errors=linter_error
        )

    def _determine_type(self, finding: Finding) -> str:
        """Determine finding type for template selection.

        Args:
            finding: Finding to classify

        Returns:
            Finding type string
        """
        # Check for SQL injection
        if finding.rule_id and "S3649" in finding.rule_id:
            return "sql_injection"

        # Check for cookie security
        if finding.rule_id and "S2092" in finding.rule_id:
            return "cookie_security"

        # Check for dependency
        if finding.category == "DEPENDENCY":
            return "dependency"

        # Default to generic
        return "generic"
