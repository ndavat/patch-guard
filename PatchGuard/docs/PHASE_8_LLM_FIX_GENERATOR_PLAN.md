# Phase 8: LLM Fix Generator Implementation Plan

## Overview

**Goal**: Implement Loop 4 (LLM Fix Generator) that builds prompts with security context, generates unified diffs using LLMs, validates fixes with linters, and performs self-correction on failures.

**Status**: Planning Phase
**Prerequisites**: ✅ Phases 1-7 Complete (Parsers + Models + Risk Classifier + Context Retriever)

## Architecture

```
Finding + CodeContext → LLM Fix Generator → Unified Diff → Linter Validation
                              ↓                    ↓              ↓
                        Prompt Builder      Diff Parser    Self-Correction
                        (with context)      (apply patch)   (retry on fail)
```

## Components

### 1. Prompt Builder
Constructs prompts with:
- Finding details (vulnerability, severity, location)
- Code context (surrounding code, imports)
- Fix instructions (specific to vulnerability type)
- Output format (unified diff)

### 2. LLM Client
- Pluggable LLM providers (GPT-4o, Claude 3.5 Sonnet)
- Streaming support
- Token management
- Error handling and retries

### 3. Diff Parser
- Parse unified diff from LLM response
- Apply diff to source file
- Validate diff format
- Handle edge cases

### 4. Linter Validator
- Language-specific linters (flake8, eslint, checkstyle, hadolint)
- Run linter on modified code
- Parse linter output
- Return validation results

### 5. Self-Correction Loop
- Max 3 attempts
- On linter failure: append error to prompt and retry
- Track attempt history
- Escalate after max attempts

## Implementation Tasks (TDD)

### Task 8.1: Create FixResult Model
**Action**: Create `patchguard/models/fix_result.py`

```python
@dataclass
class FixResult:
    finding_id: str
    success: bool
    diff: str | None
    modified_code: str | None
    linter_output: str | None
    attempts: int
    error_message: str | None
```

---

### Task 8.2: 🔴 RED - Write `test_prompt_builder.py`
**Action**: Create `PatchGuard/tests/unit/test_prompt_builder.py`

**Test cases**:
- `test_build_prompt_with_context` - Include code context in prompt
- `test_build_prompt_with_imports` - Include import statements
- `test_build_prompt_sql_injection` - SQL injection specific instructions
- `test_build_prompt_dependency_upgrade` - Dependency upgrade instructions
- `test_build_prompt_output_format` - Request unified diff format
- `test_build_prompt_with_fix_hint` - Include fix hint from finding
- `test_build_prompt_with_line_numbers` - Include line numbers
- `test_build_retry_prompt_with_error` - Append linter error for retry

**Verify**: All tests FAIL

---

### Task 8.3: Create Prompt Templates
**Action**: Create `PatchGuard/patchguard/prompts/templates.py`

**Templates**:
- `SQL_INJECTION_TEMPLATE` - Parameterized query instructions
- `DEPENDENCY_UPGRADE_TEMPLATE` - Package version update
- `COOKIE_SECURITY_TEMPLATE` - HttpOnly, Secure, SameSite flags
- `GENERIC_TEMPLATE` - General fix instructions
- `RETRY_TEMPLATE` - Self-correction with linter errors

---

### Task 8.4: 🟢 GREEN - Implement PromptBuilder
**Action**: Create `PatchGuard/patchguard/generators/prompt_builder.py`

```python
class PromptBuilder:
    def build(self, finding: Finding, context: CodeContext) -> str:
        """Build LLM prompt with context."""
        template = self._select_template(finding)
        return template.format(
            finding=finding,
            context=context,
            instructions=self._get_instructions(finding)
        )

    def build_retry(self, original_prompt: str, linter_error: str) -> str:
        """Build retry prompt with linter error."""
```

**Verify**: All tests PASS

---

### Task 8.5: 🔴 RED - Write `test_llm_client.py`
**Action**: Create `PatchGuard/tests/unit/test_llm_client.py`

**Test cases**:
- `test_generate_fix_returns_diff` - LLM returns unified diff
- `test_generate_fix_with_mock_llm` - Mock LLM response
- `test_handle_llm_timeout` - Timeout handling
- `test_handle_llm_error` - Error handling
- `test_token_limit_handling` - Truncate context if needed
- `test_streaming_response` - Stream LLM output

**Verify**: All tests FAIL

---

### Task 8.6: 🟢 GREEN - Implement LLMClient
**Action**: Create `PatchGuard/patchguard/generators/llm_client.py`

```python
class LLMClient:
    def __init__(self, provider: str = "openai", model: str = "gpt-4o"):
        self.provider = provider
        self.model = model

    def generate(self, prompt: str) -> str:
        """Generate fix using LLM."""
        # Call LLM API
        # Parse response
        # Extract diff
        return diff
```

**Verify**: All tests PASS

---

### Task 8.7: 🔴 RED - Write `test_diff_parser.py`
**Action**: Create `PatchGuard/tests/unit/test_diff_parser.py`

**Test cases**:
- `test_parse_unified_diff` - Parse valid unified diff
- `test_apply_diff_to_file` - Apply diff and return modified code
- `test_handle_malformed_diff` - Invalid diff format
- `test_extract_diff_from_markdown` - Extract diff from ```diff blocks
- `test_handle_multiple_files` - Multiple files in diff

**Verify**: All tests FAIL

---

### Task 8.8: 🟢 GREEN - Implement DiffParser
**Action**: Create `PatchGuard/patchguard/generators/diff_parser.py`

```python
class DiffParser:
    def parse(self, diff_text: str) -> dict:
        """Parse unified diff."""

    def apply(self, original_code: str, diff: str) -> str:
        """Apply diff to code."""

    def extract_from_markdown(self, response: str) -> str:
        """Extract diff from markdown code blocks."""
```

**Verify**: All tests PASS

---

### Task 8.9: 🔴 RED - Write `test_linter_validator.py`
**Action**: Create `PatchGuard/tests/unit/test_linter_validator.py`

**Test cases**:
- `test_validate_python_with_flake8` - Run flake8 on Python code
- `test_validate_javascript_with_eslint` - Run eslint on JS code
- `test_validate_csharp_with_checkstyle` - Run checkstyle on C# code
- `test_validation_passes` - No linter errors
- `test_validation_fails` - Linter errors returned
- `test_handle_linter_not_installed` - Graceful degradation

**Verify**: All tests FAIL

---

### Task 8.10: 🟢 GREEN - Implement LinterValidator
**Action**: Create `PatchGuard/patchguard/validators/linter_validator.py`

```python
class LinterValidator:
    LINTERS = {
        "python": "flake8",
        "javascript": "eslint",
        "csharp": "dotnet format --verify-no-changes",
    }

    def validate(self, code: str, language: str) -> tuple[bool, str]:
        """Validate code with linter."""
```

**Verify**: All tests PASS

---

### Task 8.11: 🔴 RED - Write `test_fix_generator.py`
**Action**: Create `PatchGuard/tests/unit/test_fix_generator.py`

**Test cases**:
- `test_generate_fix_success` - Full flow: prompt → LLM → diff → validate
- `test_generate_fix_with_retry` - Linter fails, retry with error
- `test_max_attempts_reached` - Stop after 3 attempts
- `test_dependency_finding_no_fix` - Skip LLM for dependencies
- `test_high_risk_finding_no_fix` - Skip LLM for HIGH risk

**Verify**: All tests FAIL

---

### Task 8.12: 🟢 GREEN - Implement FixGenerator
**Action**: Create `PatchGuard/patchguard/generators/fix_generator.py`

```python
class FixGenerator:
    def __init__(self, llm_client: LLMClient, validator: LinterValidator):
        self.llm_client = llm_client
        self.validator = validator
        self.prompt_builder = PromptBuilder()
        self.diff_parser = DiffParser()

    def generate(self, finding: Finding, context: CodeContext) -> FixResult:
        """Generate fix with self-correction loop."""
        max_attempts = 3
        for attempt in range(max_attempts):
            # Build prompt
            # Call LLM
            # Parse diff
            # Validate
            # If valid: return success
            # If invalid: retry with error
        return FixResult(success=False, ...)
```

**Verify**: All tests PASS

---

### Task 8.13: Integration Test
**Action**: Create `tests/integration/test_full_pipeline.py`

**Test flow**:
```python
def test_end_to_end_fix_generation():
    # Parse → Classify → Retrieve Context → Generate Fix
    parser = SonarQubeParser()
    findings = parser.parse(sonarqube_json)

    classifier = RiskClassifier()
    classified = classifier.classify_batch(findings)

    retriever = ContextRetriever()
    generator = FixGenerator()

    for finding in classified:
        if finding.risk_level == "LOW":
            context = retriever.retrieve(finding)
            result = generator.generate(finding, context)
            assert result is not None
```

---

## File Structure

```
PatchGuard/
├── patchguard/
│   ├── models/
│   │   └── fix_result.py             # FixResult dataclass
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── prompt_builder.py         # Prompt construction
│   │   ├── llm_client.py             # LLM API client
│   │   ├── diff_parser.py            # Diff parsing and application
│   │   └── fix_generator.py          # Main fix generation orchestrator
│   ├── validators/
│   │   ├── __init__.py
│   │   └── linter_validator.py       # Linter validation
│   └── prompts/
│       ├── __init__.py
│       └── templates.py               # Prompt templates
├── tests/
│   ├── unit/
│   │   ├── test_prompt_builder.py
│   │   ├── test_llm_client.py
│   │   ├── test_diff_parser.py
│   │   ├── test_linter_validator.py
│   │   └── test_fix_generator.py
│   └── integration/
│       └── test_full_pipeline.py
```

## Success Criteria

- ✅ All tests pass (RED → GREEN → REFACTOR)
- ✅ Coverage ≥ 80% on generator code
- ✅ Self-correction loop works (max 3 attempts)
- ✅ Linter validation integrated
- ✅ Pluggable LLM providers
- ✅ Graceful error handling

## Design Considerations

### 1. LLM Provider Abstraction
- Abstract interface for LLM clients
- Easy to swap providers (OpenAI, Anthropic, local models)
- Consistent error handling

### 2. Prompt Engineering
- Clear, specific instructions
- Include relevant context only
- Request structured output (unified diff)
- Language-specific guidance

### 3. Self-Correction Strategy
- Max 3 attempts to avoid infinite loops
- Append linter errors to prompt
- Track attempt history
- Escalate to human after max attempts

### 4. Validation Strategy
- Run linter on modified code (not original)
- Parse linter output for errors
- Return clear error messages
- Handle linter not installed gracefully

### 5. Performance
- Cache LLM responses (optional)
- Parallel processing for batch fixes
- Token limit management
- Timeout handling

## Next Phase After This

**Phase 9: PR Automation (Loop 5)**
- Create branches
- Commit fixes
- Open Pull Requests
- Link to findings

---

**Status**: Ready to implement
**Estimated Tasks**: 13 (following TDD)
**Dependencies**: Phases 1-7 complete ✅
**Note**: This phase requires LLM API access (OpenAI or Anthropic)
