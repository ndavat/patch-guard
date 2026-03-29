# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Testing:**
- Run all tests: `pytest`
- Run tests with coverage: `pytest --cov=patchguard`
- Run specific test file: `pytest tests/unit/test_sonarqube_parser.py`
- Run specific test function: `pytest tests/unit/test_sonarqube_parser.py::test_parse_sonarqube_findings`

**Code Quality:**
- Check formatting: `flake8 patchguard`
- Run type checking: `mypy patchguard` (if configured)

**Project Setup:**
- Install dev dependencies: `pip install -e ".[dev]"`
- Activate virtual environment: `source spec-kit/venv/bin/activate` (Linux/Mac) or `spec-kit\venv\Scripts\activate` (Windows)

## Architecture Overview

PatchGuard follows a six-loop agentic architecture for autonomous security remediation:

1. **Loop 1 - Ingestion Agent**: Polls SonarQube/Mend/Trivy APIs or accepts file uploads
2. **Loop 2 - Risk Classifier**: Evaluates findings against Safe-to-Fix policy
3. **Loop 3 - Context Retriever**: Fetches ±50 lines of source code context from VCS
4. **Loop 4 - LLM Fix Generator**: Generates unified diff via LLM with lint validation
5. **Loop 5 - PR Automation Agent**: Creates branch, commits fix, opens PR with documentation
6. **Loop 6 - Feedback Monitor**: Watches PR comments and amends fixes based on reviewer feedback

Key architectural components:
- **Normalized Finding Schema**: Converts all scan data to a canonical format for tool-agnostic processing
- **Safe-to-Fix Policy**: Determines which findings are low-risk (auto-fixable) vs high-risk (flag-only)
- **Test-Driven Development**: All components built with RED→GREEN→REFACTOR cycle, ≥80% coverage enforced
- **Human-in-the-Loop**: Every PR requires human approval; agent monitors and responds to reviewer comments

## Key Directories

- `patchguard/`: Main source code
  - `parsers/`: Tool-specific parsers (sonarqube, mend, trivy)
  - `classifiers/`: Risk classification logic
  - `retrievers/`: Context retrieval from VCS
  - `generators/`: LLM-based fix generation
  - `validators/`: Linting and validation
  - `prompts/`: LLM prompt templates
  - `models/`: Data models (Finding, FixResult, CodeContext)
  - `utils/`: Utility functions (severity normalization, language detection)
- `tests/`: Test suite organized by unit/integration levels
- `docs/`: Documentation including implementation plans and status reports
- `spec-kit/`: Virtual environment and dependencies

## Working with the Codebase

**Adding New Scanner Support:**
1. Create a new parser in `patchguard/parsers/<toolname>/`
2. Implement the base parser interface from `patchguard/parsers/base.py`
3. Add corresponding unit tests in `tests/unit/`
4. Update the ingestion loop to route findings to the new parser

**Modifying Risk Classification:**
1. Edit logic in `patchguard/classifiers/risk_classifier.py`
2. Refer to `risk_classifier_samples.py` test fixtures for examples
3. Update unit tests in `tests/unit/test_severity_filter.py`

**Understanding Data Flow:**
Findings flow: Ingestion → Risk Classification → Context Retrieval → LLM Fix Generation → PR Automation → Feedback Monitoring
Each loop communicates via normalized Finding objects passed through queues or direct function calls.

## Important Notes

- The project uses Python 3.11+ with LangChain/CrewAI agent framework
- All auto-generated PRs require mandatory human review - no auto-merging
- LLM providers supported: GPT-4o, Claude 3.5 Sonnet (pluggable)
- Validation tools: flake8 (Python), eslint (JS/TS), checkstyle (Java), hadolint (Dockerfile)
- Enterprise security features: HashiCorp Vault for secrets, audit logging, ephemeral workspaces