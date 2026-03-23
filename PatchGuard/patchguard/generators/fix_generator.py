"""FixGenerator orchestrator for LLM-based fix generation with self-correction."""
from typing import Optional
from patchguard.models.finding import Finding
from patchguard.models.code_context import CodeContext
from patchguard.models.fix_result import FixResult
from patchguard.generators.prompt_builder import PromptBuilder
from patchguard.generators.diff_parser import DiffParser, DiffError
from patchguard.generators.llm_client import LLMClient
from patchguard.validators.linter_validator import LinterValidator


class FixGenerator:
    """Orchestrates LLM-based fix generation with self-correction loop."""

    MAX_ATTEMPTS = 3

    def __init__(self, llm_client: LLMClient, validator: LinterValidator):
        """Initialize FixGenerator.

        Args:
            llm_client: LLM client for generating fixes
            validator: Linter validator for code validation
        """
        self.llm_client = llm_client
        self.validator = validator
        self.prompt_builder = PromptBuilder()
        self.diff_parser = DiffParser()

    def generate(self, finding: Finding, context: CodeContext) -> FixResult:
        """Generate fix with self-correction loop (max 3 attempts).

        Args:
            finding: Security finding to fix
            context: Code context around the finding

        Returns:
            FixResult with generation status and fixed code
        """
        # Skip dependency findings - they need manual package.json updates
        if finding.source == "mend":
            return FixResult(
                finding_id=finding.finding_id,
                success=True,
                attempts=0,
                error_message="Dependency findings require manual package.json updates"
            )

        # Skip HIGH risk findings - they need manual review
        if hasattr(finding, 'risk_level') and finding.risk_level == "HIGH":
            return FixResult(
                finding_id=finding.finding_id,
                success=True,
                attempts=0,
                error_message="HIGH risk findings require manual review"
            )

        # Self-correction loop
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                # Build prompt
                prompt = self.prompt_builder.build(finding, context)

                # Generate fix from LLM
                llm_response = self.llm_client.generate(prompt)

                # Extract diff from response
                try:
                    diff_text = self.diff_parser.extract_from_markdown(llm_response)
                except DiffError:
                    # If no diff found, try to use response as-is
                    diff_text = llm_response

                # Apply diff to get fixed code
                try:
                    fixed_code = self.diff_parser.apply(context.surrounding_code, diff_text)
                except DiffError as e:
                    if attempt < self.MAX_ATTEMPTS:
                        # Retry with error feedback
                        continue
                    return FixResult(
                        finding_id=finding.finding_id,
                        success=False,
                        attempts=attempt,
                        error_message=f"Failed to apply diff: {str(e)}"
                    )

                # Validate fixed code
                is_valid, validation_output = self.validator.validate(
                    fixed_code,
                    context.language
                )

                if is_valid:
                    # Success!
                    return FixResult(
                        finding_id=finding.finding_id,
                        success=True,
                        attempts=attempt,
                        diff=diff_text,
                        modified_code=fixed_code,
                        linter_output=validation_output
                    )
                else:
                    # Validation failed - retry with error feedback
                    if attempt < self.MAX_ATTEMPTS:
                        # Add validation error to context for next attempt
                        context.validation_error = validation_output
                        continue
                    else:
                        # Max attempts reached
                        return FixResult(
                            finding_id=finding.finding_id,
                            success=False,
                            attempts=attempt,
                            modified_code=fixed_code,
                            linter_output=validation_output,
                            error_message=f"Code validation failed after {self.MAX_ATTEMPTS} attempts: {validation_output}"
                        )

            except Exception as e:
                # Unexpected error
                if attempt == self.MAX_ATTEMPTS:
                    return FixResult(
                        finding_id=finding.finding_id,
                        success=False,
                        attempts=attempt,
                        error_message=f"Error during fix generation: {str(e)}"
                    )
                # Retry on error
                continue

        # Should not reach here, but handle gracefully
        return FixResult(
            finding_id=finding.finding_id,
            success=False,
            attempts=self.MAX_ATTEMPTS,
            error_message=f"Failed to generate valid fix after {self.MAX_ATTEMPTS} attempts"
        )

