# CodeSentinel — Executable Task Breakdown
### Master Development Checklist (TDD Approach)

**Version:** 1.0  
**Date:** 2026-03-15  
**Total Phases:** 7 (Phase 0–6)  
**Total Duration:** 20 Weeks (Mar 16 – Aug 01, 2026)  
**Source:** Approved Implementation Strategy `07_CodeSentinel_Implementation_Strategy.md`  
**Methodology:** Test-Driven Development (Red → Green → Refactor on every task)

---

## TDD Contract (Applies to Every Task Below)

Before writing *any* implementation code:
1. **RED** — Write a failing test that defines the expected behavior
2. **GREEN** — Write the minimal code to make the test pass
3. **REFACTOR** — Improve code quality without changing behavior; all tests must still pass

---

## Phase 0 — Project Setup & Planning
**Duration:** 2 weeks | **Dates:** Mar 16 – Mar 27, 2026 | **Milestone:** M1

### TASK-0.1 — Requirements Reconciliation
**Priority:** Critical | **Effort:** 2 days | **Owner:** Tech Lead

**Objective:** Produce a single authoritative requirements register from the 5 source documents, resolving all contradictions.

**Sub-tasks:**
- [ ] Resolve LLM provider discrepancy: confirm GPT-4o and Claude 3.5 Sonnet as primary; GitHub Copilot as optional (requires Copilot Enterprise license)
- [ ] Confirm Azure Repos MCP server specification (URL, auth method, SDK version) — if unresolved, document fallback to Azure DevOps REST API
- [ ] Decide on-prem LLM inference requirement: evaluate Ollama (Llama-3) vs Azure OpenAI private endpoint
- [ ] Confirm ingestion scope is finalized:
  - SonarQube: `BUG`, `VULNERABILITY` types; `BLOCKER`, `CRITICAL` severities; JSON format only
  - Mend: `CRITICAL`, `HIGH` severities; JSON format only
  - Trivy: `CRITICAL`, `HIGH` severities; JSON format only
- [ ] Document final approved tech stack in `docs/tech-decisions.md`
- [ ] Obtain stakeholder sign-off on requirements register

**Acceptance Criteria:**
- All contradictions resolved and documented
- Requirements register reviewed and signed off
- Tech stack decision record written

---

### TASK-0.2 — Development Environment Setup
**Priority:** Critical | **Effort:** 2 days | **Owner:** DevOps

**Sub-tasks:**
- [ ] Create Python 3.11+ virtual environment
- [ ] Create `requirements.txt` with pinned core dependencies:
  ```
  langchain>=0.2.0
  openai>=1.0.0
  anthropic>=0.20.0
  httpx>=0.27.0
  gitpython>=3.1.0
  jsonschema>=4.0.0
  pydantic>=2.0.0
  redis>=5.0.0
  structlog>=24.0.0
  click>=8.0.0
  ```
- [ ] Create `requirements-dev.txt`:
  ```
  pytest>=8.0.0
  pytest-asyncio>=0.23.0
  pytest-cov>=5.0.0
  pytest-httpx>=0.30.0
  black>=24.0.0
  isort>=5.13.0
  flake8>=7.0.0
  mypy>=1.9.0
  ```
- [ ] Configure `pyproject.toml` with tool settings (black, isort, mypy, pytest)
- [ ] Set up Docker and Docker Compose for local development
- [ ] Configure HashiCorp Vault in dev mode (Docker)
- [ ] Configure pre-commit hooks: `black`, `isort`, `flake8`, `mypy`
- [ ] Establish monorepo directory structure:
  ```
  codesentinel/
  ├── agents/
  ├── parsers/
  │   ├── sonarqube/
  │   ├── mend/
  │   └── trivy/
  ├── vcs/
  ├── llm/
  │   └── prompts/
  ├── validation/
  ├── config/
  ├── audit/
  ├── utils/
  ├── tests/
  │   ├── unit/
  │   ├── integration/
  │   ├── e2e/
  │   └── fixtures/
  │       ├── sonarqube/
  │       ├── mend/
  │       └── trivy/
  ├── docs/
  └── infra/
  ```
- [ ] Create `Makefile` with targets: `dev-setup`, `test`, `lint`, `build`, `docker-up`
- [ ] Verify `make dev-setup` runs cleanly on a fresh machine

**Acceptance Criteria:**
- `make dev-setup` succeeds end-to-end on a clean environment
- Pre-commit hooks run and pass on a sample commit
- All secrets loaded from Vault; zero hardcoded credentials anywhere

---

### TASK-0.3 — Sandbox Credentials Provisioning
**Priority:** High | **Effort:** 1 day | **Owner:** DevOps + Security

**Sub-tasks:**
- [ ] Provision SonarQube Community Edition (Docker); generate User Token
- [ ] Create Mend sandbox account; obtain User Key and Organization Token
- [ ] Set up Trivy server (Docker) for client-server mode testing
- [ ] Create GitHub App for test organization; capture App ID + private key
- [ ] Create GitLab Bot account with API token on test instance
- [ ] Provision Azure DevOps test project; generate PAT (or MCP session, pending TASK-0.1)
- [ ] Store all credentials in Vault under `secret/codesentinel/`:
  - `sonarqube/token`
  - `mend/user_key`, `mend/org_token`
  - `trivy/api_key`
  - `github/app_id`, `github/private_key`
  - `gitlab/bot_token`
  - `azure/pat`
- [ ] Verify all credentials functional against their respective sandbox APIs
- [ ] Document credential rotation schedule in `docs/secrets.md`

**Acceptance Criteria:**
- All credentials verified working
- Zero credentials in any config file or environment variable on developer machines

---

### TASK-0.4 — Internal Schema & Config Definition
**Priority:** Critical | **Effort:** 1 day | **Owner:** Tech Lead + Backend Dev

**Sub-tasks:**
- [ ] Finalize normalized `Finding` schema in `config/schemas.py` (Pydantic model):
  - Fields: `finding_id`, `source`, `tool_version`, `ingested_at`, `repo`, `file_path`, `line_start`, `line_end`, `severity`, `rule_id`, `message`, `fix_hint`, `category`, `risk_level`, `status`, `fix_diff`, `pr_url`, `retries`, `revision_count`, `code_context`, `manifest_content`, `audit_trail`
  - Status enum: `QUEUED | CLASSIFIED | CONTEXT_READY | FIX_VALIDATED | PR_OPEN | PR_APPROVED | AUTO_FIX_FAILED | SKIPPED_HIGH_RISK | HUMAN_DECLINED | ESCALATED`
- [ ] Write JSON Schema validation file `config/finding.schema.json`
- [ ] Define `AuditEvent` Pydantic model: `event_type`, `timestamp`, `finding_id`, `agent_loop`, `repo`, `outcome`, `details`, `prompt_hash`
- [ ] Define audit event type enum: `FINDING_INGESTED | RISK_CLASSIFIED | CONTEXT_RETRIEVED | FIX_GENERATED | VALIDATION_PASSED | VALIDATION_FAILED | PR_CREATED | PR_COMMENT_RECEIVED | FIX_AMENDED | FIX_SKIPPED | FIX_FAILED`
- [ ] Define `PRDescription` template schema
- [ ] Create `config/safe_rules.yaml` with initial SonarQube Bug/Vulnerability safe-rule list
- [ ] Create `config/severity_filters.yaml` per tool
- [ ] **TDD:** Write unit tests for schema validation (`tests/unit/test_schemas.py`):
  - Valid `Finding` object passes validation
  - Missing required field raises `ValidationError`
  - Invalid status value raises `ValidationError`
  - Invalid severity value raises `ValidationError`

**Acceptance Criteria:**
- All schema validation tests pass
- `Finding` model, `AuditEvent` model, and template schemas importable with no errors

---

### TASK-0.5 — M1 Milestone Review
**Priority:** Critical | **Effort:** 0.5 days | **Owner:** Project Manager

- [ ] Conduct milestone review meeting; demo that `make dev-setup` runs cleanly
- [ ] Obtain formal sign-off on requirements register and tech stack
- [ ] Confirm team resourcing for Phase 1

---

## Phase 1 — Core Agent & VCS Integration
**Duration:** 4 weeks | **Dates:** Mar 30 – Apr 24, 2026 | **Milestone:** M2

### TASK-1.1 — Agent Core Framework
**Priority:** Critical | **Effort:** 3 days | **File:** `codesentinel/agents/core.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_core.py`):
  - Config loads correctly from environment variables
  - Config raises error on missing required key
  - Queue accepts and returns a `Finding` object
  - Graceful shutdown flushes queue before exit
  - Structured log output is valid JSON
- [ ] Initialize LangChain agent base class with configurable LLM backend (selectable via `CODESENTINEL_LLM_PROVIDER` env var)
- [ ] Implement structured logging using `structlog`: JSON-formatted, configurable log level, correlation ID per finding
- [ ] Implement configuration loader: reads `CODESENTINEL_*` environment variables + Vault at runtime, validates via Pydantic
- [ ] Build central findings queue: accepts normalized `Finding` objects, dispatches to agent loops
- [ ] Implement graceful shutdown: drain queue, close connections, write final audit entry

**Acceptance Criteria:**
- All unit tests pass
- Running `python -m codesentinel` starts without error and logs valid JSON to stdout

---

### TASK-1.2 — VCS Authentication Module
**Priority:** Critical | **Effort:** 2 days | **File:** `codesentinel/vcs/auth.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_vcs_auth.py`):
  - GitHub App JWT generation produces a valid JWT structure
  - Token refresh triggers before expiry (mock clock)
  - Invalid credentials raise `AuthenticationError`
  - VCS client factory returns correct client type for GitHub/GitLab/Azure URLs
- [ ] Implement GitHub App installation token flow (JWT → installation token refresh cycle)
- [ ] Implement GitLab Bot Token authentication with token validation
- [ ] Implement Azure DevOps PAT authentication
- [ ] Build `VCSClientFactory`: returns correct authenticated client based on repo URL
- [ ] Implement token refresh logic with expiry tracking (refresh 60s before expiry)

**Acceptance Criteria:**
- All unit tests pass (mocked HTTP responses)
- No tokens stored in memory longer than their TTL

---

### TASK-1.3 — MCP Integration for Azure Repos & GitHub
**Priority:** High | **Effort:** 3 days | **File:** `codesentinel/vcs/mcp_client.py`

> **Dependency:** Requires Azure Repos MCP server spec (TASK-0.1). If spec not finalized, implement Azure DevOps REST API fallback first and add MCP layer in Phase 5.

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_mcp_client.py`):
  - MCP session initialization succeeds with valid auth
  - `checkout_branch` operation maps correctly to MCP call
  - `create_pr` operation maps correctly to MCP call with all required fields
  - Fallback to REST API when MCP is unavailable
- [ ] Research and document Azure Repos MCP server endpoint and auth handshake
- [ ] Implement MCP session initialization and keep-alive
- [ ] Map MCP operations: `checkout_branch`, `commit_files`, `push_branch`, `create_pr`, `get_comments`
- [ ] Implement GitHub MCP operations (if MCP preferred over GitHub App REST)
- [ ] Implement REST API fallback for both platforms (factory pattern)

**Acceptance Criteria:**
- All unit tests pass (mocked MCP server)
- VCS factory transparently falls back to REST API when MCP unavailable

---

### TASK-1.4 — Git Operations Module
**Priority:** Critical | **Effort:** 3 days | **File:** `codesentinel/vcs/git_ops.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_git_ops.py`):
  - Ephemeral clone creates temp directory and registers cleanup
  - Branch name follows `fix/<source>-<finding_id>` pattern
  - Patch application succeeds for a valid unified diff
  - Commit message matches required structured format
  - Temp directory is deleted after `cleanup()` is called
- [ ] Implement ephemeral repo clone: clone to `tempfile.mkdtemp()`, register `atexit` cleanup
- [ ] Implement branch creation: `fix/<source>-<finding_id>` naming convention
- [ ] Implement file patch application: accept unified diff, apply using `git apply`
- [ ] Implement staged commit with structured commit message:
  ```
  fix(<source>): <short description> [<finding_id>]

  Tool: <sonarqube|mend|trivy>
  Finding ID: <id>
  Rule: <rule_id>
  Severity: <severity>
  Risk Level: LOW
  Auto-generated by CodeSentinel
  ```
- [ ] Implement push to remote branch
- [ ] Implement branch cleanup on PR merge/rejection

**Acceptance Criteria:**
- All unit tests pass (in-memory git fixture or temp repo)
- No temp directories left on disk after test run

---

### TASK-1.5 — Pull Request Creation & Management
**Priority:** Critical | **Effort:** 3 days | **File:** `codesentinel/vcs/pr_manager.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_pr_manager.py`):
  - PR description generated with all required sections
  - Labels applied: `auto-fix`, `<source-tool>`, `<severity>`, `requires-security-review`
  - Reviewer assignment reads from repo `.codesentinel.yml`
  - PR status polling returns correct state from mocked API
- [ ] Implement PR creation via GitHub REST API and GitLab API
- [ ] Build PR description generator using approved template:
  ```markdown
  ## [Auto-Fix] <Short Summary>

  > ⚠️ **This PR was generated by CodeSentinel. Mandatory human review required before merge.**

  **Source Tool:** SonarQube / Mend / Trivy
  **Finding ID:** <id>
  **Rule / CVE:** <rule_id or CVE>
  **Severity:** <severity>
  **File:** `<file_path>` (line <line>)

  ### What was changed
  <LLM-generated explanation of the fix>

  ### Risk Assessment
  **Risk Level:** LOW
  <Justification: why this specific pattern is safe to auto-fix>

  ### Validation Results
  - [x] Linter: PASSED (<linter_name> v<version>)
  - [ ] Build verification: Not configured / PASSED

  ---
  *Generated by CodeSentinel. Review carefully before merging.*
  *Comment to request changes — the PRMonitor will detect and refine automatically.*
  ```
- [ ] Implement label application: `auto-fix`, `<source-tool>`, `<severity>`, `requires-security-review`
- [ ] Implement reviewer assignment from repo config `.codesentinel.yml`
- [ ] Implement PR status polling

**Acceptance Criteria:**
- All unit tests pass (mocked GitHub/GitLab API)
- PR description contains all required sections

---

### TASK-1.6 — PRMonitor — Human-in-the-Loop Feedback Loop
**Priority:** High | **Effort:** 3 days | **File:** `codesentinel/agents/pr_monitor.py`

**Objective:** Implement Loop 6. The PRMonitor runs in the background, polls open auto-fix PRs for new reviewer comments, classifies intent, and refines fixes automatically.

**User-facing behavior:**
> You can comment directly on the PR. If you ask for changes (e.g., *"Change this to a list comprehension"*), the PRMonitor will detect your comment and attempt to refine the fix automatically.

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_pr_monitor.py`):
  - "LGTM" comment classifies as `APPROVE`
  - "This is wrong" comment classifies as `REJECT`
  - "Change this to a list comprehension" classifies as `CHANGE_REQUEST`
  - On `CHANGE_REQUEST`: finding is re-queued to Loop 4 with instruction injected
  - On `REJECT`: PR branch is closed and status set to `HUMAN_DECLINED`
  - After 3 revision cycles: status set to `ESCALATED`, no further fix attempts
  - PRMonitor posts comment "Max revisions reached. Please resolve manually." on escalation
- [ ] Implement PR comment poller: fetch new comments on open auto-fix PRs every N minutes (configurable via `CODESENTINEL_PRMONITOR_POLL_INTERVAL`, default 5 min)
- [ ] Implement comment intent classifier using LLM:
  - `APPROVE` → log `PR_APPROVED`, stop monitoring
  - `REJECT` → close branch, log `HUMAN_DECLINED`, stop monitoring
  - `CHANGE_REQUEST` → extract instruction, re-trigger Loop 4 (inject reviewer instruction into next prompt), push amended commit, reply to comment
- [ ] Implement `revision_count` tracking; after 3 cycles → post escalation comment, set `ESCALATED`
- [ ] Implement `last_checked` timestamp tracking to avoid re-processing old comments

**Acceptance Criteria:**
- All unit tests pass (mocked LLM intent classification, mocked VCS API)
- PRMonitor correctly identifies and handles all three intent types

---

### TASK-1.7 — Audit Logging System
**Priority:** Critical | **Effort:** 2 days | **File:** `codesentinel/audit/logger.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_audit_logger.py`):
  - Each event type produces a valid `AuditEvent` JSON object
  - Log file is append-only (write fails if file is tampered / truncated)
  - `prompt_hash` is stored, not the raw prompt text
  - All required fields present in each event
- [ ] Implement append-only JSON Lines writer (`audit.jsonl`)
- [ ] Implement configurable output backends: local file (default), S3, database
- [ ] Implement all event type emitters:
  `FINDING_INGESTED`, `RISK_CLASSIFIED`, `CONTEXT_RETRIEVED`, `FIX_GENERATED`, `VALIDATION_PASSED`, `VALIDATION_FAILED`, `PR_CREATED`, `PR_COMMENT_RECEIVED`, `FIX_AMENDED`, `FIX_SKIPPED`, `FIX_FAILED`
- [ ] Store `sha256(prompt)` as `prompt_hash`, never raw prompt
- [ ] Ensure every event contains: `event_type`, `timestamp`, `finding_id`, `repo`, `agent_loop`, `outcome`, `details`

**Acceptance Criteria:**
- All unit tests pass
- Audit log is valid JSON Lines (each line parseable independently)
- No raw LLM prompts appear in the log

---

### TASK-1.8 — M2 Milestone Integration Test
**Priority:** Critical | **Effort:** 1 day | **File:** `tests/e2e/test_phase1_smoke.py`

**Sub-tasks:**
- [ ] **TDD:** Write the E2E smoke test first, then verify it passes:
  - Manually inject a dummy `Finding` object with status `QUEUED`
  - Assert: agent creates branch `fix/test-DUMMY-001` on test repo
  - Assert: placeholder file committed with correctly structured commit message
  - Assert: PR opened on GitHub/GitLab test repo and visible in UI
  - Assert: audit log contains `FINDING_INGESTED`, `PR_CREATED` events
  - Assert: no credentials appear in logs, commit messages, or PR description
- [ ] Conduct M2 milestone demo — record screen capture

**Acceptance Criteria (M2):**
- Agent can create branch, commit, and open a documented PR on the test repo
- Audit log complete; zero credential leakage

---

## Phase 2 — SonarQube Integration
**Duration:** 3 weeks | **Dates:** Apr 27 – May 15, 2026 | **Milestone:** M3

**Ingestion scope:**
- Types: `BUG`, `VULNERABILITY` only
- Severities: `BLOCKER`, `CRITICAL` only
- Format: JSON (API response + manual JSON file input)

### TASK-2.1 — SonarQube API Client
**Priority:** Critical | **Effort:** 2 days | **File:** `codesentinel/parsers/sonarqube/api_client.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_sonarqube_api.py`):
  - Authentication header is correctly constructed from token
  - Query parameters include `types=BUG,VULNERABILITY` and `severities=BLOCKER,CRITICAL`
  - Pagination fetches all pages until `p * ps >= total`
  - Rate limiting waits the correct backoff duration on 429 response
  - `httpx.HTTPStatusError` is caught and wrapped in `SonarAPIError`
- [ ] Implement `httpx` async client for SonarQube Web API
- [ ] Implement Bearer token authentication
- [ ] Implement `api/issues/search` query with filters:
  - `types=BUG,VULNERABILITY`
  - `severities=BLOCKER,CRITICAL`
  - `componentKeys=<project_key>`
  - `resolved=false`
- [ ] Implement full pagination (`p` and `ps` parameters)
- [ ] Implement exponential backoff + jitter on rate limit (429) responses

**Acceptance Criteria:**
- All unit tests pass (mocked HTTP responses via `pytest-httpx`)
- Client fetches all pages of results correctly

---

### TASK-2.2 — SonarQube JSON Parser
**Priority:** Critical | **Effort:** 2 days | **File:** `codesentinel/parsers/sonarqube/parser.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_sonarqube_parser.py`) — commit fixture files to `tests/fixtures/sonarqube/`:
  - `api_response_bugs.json` — sample API response with BUG issues
  - `api_response_vulnerabilities.json` — sample with VULNERABILITY issues
  - `api_response_mixed.json` — bugs, vulnerabilities, and (to be filtered) code smells
  - `api_response_empty.json` — no issues
  - `api_response_malformed.json` — missing required fields
  - Tests: parser extracts `key`, `rule`, `severity`, `component` (file path), `line`, `message`, `type`
  - Tests: code smells and INFO/MINOR/MAJOR issues are filtered out
  - Tests: malformed JSON raises `ParseError`
  - Tests: empty result returns empty list
- [ ] Implement parser for SonarQube API JSON response
- [ ] Implement parser for manual JSON file input (same format, file path provided)
- [ ] Normalize all parsed findings to internal `Finding` schema
- [ ] Validate output against `Finding` Pydantic model

**Acceptance Criteria:**
- All unit tests pass with all fixture files
- Output is always a valid list of `Finding` objects

---

### TASK-2.3 — SonarQube Issue Mapping & Risk Classification
**Priority:** High | **Effort:** 1 day | **File:** `codesentinel/parsers/sonarqube/mapper.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_sonarqube_mapper.py`):
  - `VULNERABILITY` + `BLOCKER` → `LOW` risk (if rule in safe list) or `HIGH` risk (if not)
  - `BUG` + `CRITICAL` → `LOW` risk (if rule in safe list) or `HIGH` risk
  - Any finding with `AUTH` or `MULTI_FILE` tag → `HIGH` risk (overrides safe list)
  - Rule added to safe list in `.codesentinel.yml` overrides default → `LOW` risk
  - Rule removed from safe list in `.codesentinel.yml` → `HIGH` risk
- [ ] Implement risk classifier reading from `config/safe_rules.yaml`
- [ ] Implement per-repo override via `.codesentinel.yml` (`safe_rules.add`, `safe_rules.remove`)
- [ ] Seed initial safe rules for known fixable Bug/Vulnerability patterns

**Acceptance Criteria:**
- 100% branch coverage on the classifier
- Per-repo override mechanism tested and working

---

### TASK-2.4 — SonarQube LLM Remediation Prompts
**Priority:** Critical | **Effort:** 3 days | **File:** `codesentinel/llm/prompts/sonarqube.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_sonarqube_prompts.py`):
  - Prompt contains the system role definition (senior security engineer)
  - Prompt contains the finding's `rule_id`, `message`, and `severity`
  - Prompt contains ±50 lines of code context around the finding line
  - Prompt contains all import statements from the file
  - Output contract line present: "Output ONLY a valid unified diff"
  - Safety emphasis line present: "Make the minimal change needed"
  - For reviewer-amended fix: reviewer instruction is injected into prompt
- [ ] Implement system prompt template:
  ```
  You are a senior security engineer performing critical bug and vulnerability fixes.
  You will receive a SonarQube finding and surrounding source code context.
  Your task is to produce a minimal, correct unified diff that resolves the finding.
  Rules:
  - Make only the minimal change needed to fix the reported issue
  - Do not change unrelated code or logic
  - Preserve variable names, comments, and business logic unless they are the issue
  - If the fix would require changing 3+ files or altering business logic, output: CANNOT_FIX_SAFELY
  - Output ONLY a valid unified diff. No explanation, no markdown fences.
  ```
- [ ] Implement prompt builder: injects finding metadata + ±50 lines code context
- [ ] Create per-category prompt variants:
  - **Null pointer / resource leak** — instruct adding null checks, try-finally, with-statement
  - **Hardcoded secrets** — instruct replacing with environment variable reference
  - **Input validation / injection** — instruct adding input sanitization
  - **Insecure defaults** — instruct correcting the insecure setting
- [ ] Implement reviewer instruction injection for PRMonitor-triggered re-runs
- [ ] Test prompts against GPT-4o on 5 sample findings; document first-pass success rate

**Acceptance Criteria:**
- All unit tests pass
- `CANNOT_FIX_SAFELY` output handled gracefully (treated as HIGH risk, no commit)

---

### TASK-2.5 — SonarQube End-to-End Integration Test
**Priority:** Critical | **Effort:** 2 days | **File:** `tests/e2e/test_phase2_sonarqube.py`

**Sub-tasks:**
- [ ] **TDD:** Write E2E tests first, then verify they pass:
  - Scenario A: Feed `api_response_bugs.json` → ingest → classify LOW risk → context retrieve → LLM fix → lint pass → PR opened with correct description
  - Scenario B: Feed `api_response_vulnerabilities.json` → same flow → verify PR labels include `requires-security-review`
  - Scenario C: Feed mixed JSON → verify code smells are filtered and not processed
  - Scenario D: Feed finding with no matching safe rule → verify `SKIPPED_HIGH_RISK` status + audit log entry
  - Scenario E: Manual JSON file input mode → same result as API mode
- [ ] Verify audit log completeness for entire pipeline
- [ ] Conduct M3 milestone demo — record screen capture

**Acceptance Criteria (M3):**
- At least 2 Bug fixes and 1 Vulnerability fix completed end-to-end
- PRs documented with finding reference, severity, and validation results
- Code smells filtered out at ingestion

---

## Phase 3 — Mend (SCA) Integration
**Duration:** 2 weeks | **Dates:** May 18 – May 29, 2026 | **Milestone:** M4

**Ingestion scope:**
- Severities: `CRITICAL`, `HIGH` only
- Format: JSON only

### TASK-3.1 — Mend API Client
**Priority:** Critical | **Effort:** 2 days | **File:** `codesentinel/parsers/mend/api_client.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_mend_api.py`):
  - Auth header constructed correctly from User Key + Org Token
  - Findings endpoint returns paginated results
  - Only `CRITICAL` and `HIGH` severity results are retained after filtering
  - Rate limiting with exponential backoff on 429 responses
- [ ] Implement Mend Platform API 3.0 HTTP client
- [ ] Implement authentication: User Key + Organization Token (header-based)
- [ ] Implement `GET /api/v3.0/findings/applications` endpoint
  - Filter server-side or client-side for `CRITICAL` and `HIGH` severity only
- [ ] Handle pagination and response envelope unwrapping

**Acceptance Criteria:**
- All unit tests pass (mocked server responses)
- Only Critical/High severity findings reach the queue

---

### TASK-3.2 — Mend JSON Parser
**Priority:** High | **Effort:** 1 day | **File:** `codesentinel/parsers/mend/json_parser.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first — commit fixture files to `tests/fixtures/mend/`:
  - `api_response_critical.json` — sample with CRITICAL findings
  - `api_response_mixed_severity.json` — CRITICAL, HIGH, MEDIUM, LOW — verify MEDIUM/LOW filtered
  - `manual_input.json` — sample manual JSON file input
  - Tests: fields extracted correctly (`Library`, `CVE`, `InstalledVersion`, `FixedVersion`, `Severity`)
  - Tests: MEDIUM and LOW severity filtered out
  - Tests: findings without `FixedVersion` normalized with `fix_hint=None`
- [ ] Implement JSON parser for API response format
- [ ] Implement manual JSON file input mode (accepts file path)
- [ ] Apply severity filter: only `CRITICAL`, `HIGH` pass through
- [ ] Normalize to internal `Finding` schema

**Acceptance Criteria:**
- All unit tests pass with all fixture files
- MEDIUM and LOW severity findings are never added to the queue

---

### TASK-3.3 — Mend Vulnerability Risk Mapping
**Priority:** High | **Effort:** 1 day | **File:** `codesentinel/parsers/mend/mapper.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_mend_mapper.py`):
  - `FixedVersion` present + direct dependency → `LOW` risk
  - `FixedVersion` absent → `HIGH` risk (flag only, no fix)
  - Transitive dependency (detected via manifest depth) → `HIGH` risk
  - `CRITICAL` severity with `FixedVersion` → `LOW` risk (highest priority for fix)
- [ ] Implement risk classifier for Mend findings
- [ ] Implement manifest type detector: identify `requirements.txt`, `package.json`, `pom.xml`, `build.gradle`, `go.mod`, `Gemfile`, `Cargo.toml`
- [ ] Classify transitive vs direct dependency from manifest analysis

**Acceptance Criteria:**
- 100% branch coverage on the classifier
- Transitive dependency detection covers all supported manifest types

---

### TASK-3.4 — Mend LLM Remediation Prompts
**Priority:** Critical | **Effort:** 3 days | **File:** `codesentinel/llm/prompts/mend.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_mend_prompts.py`):
  - Prompt contains library name, `InstalledVersion`, `FixedVersion`, and CVE ID
  - Prompt uses the correct manifest template per file type
  - `requirements.txt` prompt produces correct version pin change
  - `package.json` prompt preserves semver prefix (`^`, `~`)
  - `pom.xml` prompt targets the correct `<version>` within the correct `<dependency>` block
  - `go.mod` prompt updates the correct `require` directive
- [ ] Implement manifest file detector + full manifest content retrieval
- [ ] Implement per-manifest prompt templates:
  - **`requirements.txt`:** `Change <library>==<current> to <library>==<fixed>`
  - **`package.json`:** Update `"<library>": "<current>"` preserving semver prefix
  - **`pom.xml`:** Update `<version>` within correct `<dependency>` block
  - **`go.mod`:** Update `require` directive for the module
- [ ] Implement version constraint preservation (detect and preserve `^`, `~`, `>=` prefixes)
- [ ] Test prompts manually against GPT-4o for `requirements.txt` and `package.json`

**Acceptance Criteria:**
- All unit tests pass
- Version constraint prefix always preserved in output diff

---

### TASK-3.5 — Mend End-to-End Integration Test
**Priority:** Critical | **Effort:** 1 day | **File:** `tests/e2e/test_phase3_mend.py`

**Sub-tasks:**
- [ ] **TDD:** Write E2E tests first, then verify they pass:
  - Scenario A: Mend JSON → `requirements.txt` version bump → lint pass → PR opened
  - Scenario B: Mend JSON → `package.json` version bump → PR opened with correct semver prefix preserved
  - Scenario C: Finding without `FixedVersion` → `SKIPPED_HIGH_RISK` + audit log entry
  - Scenario D: Manual JSON file input → same result as API mode
- [ ] Conduct M4 milestone demo — record screen capture

**Acceptance Criteria (M4):**
- At least 2 manifest types fixed from JSON input
- `FixedVersion`-absent findings never result in a commit

---

## Phase 4 — Trivy Integration
**Duration:** 2 weeks | **Dates:** Jun 01 – Jun 12, 2026 | **Milestone:** M5

**Ingestion scope:**
- Severities: `CRITICAL`, `HIGH` only
- Format: JSON only

### TASK-4.1 — Trivy API Client
**Priority:** Critical | **Effort:** 2 days | **File:** `codesentinel/parsers/trivy/api_client.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_trivy_api.py`):
  - Scan submission to Trivy server succeeds with mocked response
  - Scan result polling waits for `COMPLETED` status
  - Webhook receiver correctly parses a Trivy Operator CRD event payload
  - Rate limiting applied correctly
- [ ] Deploy Trivy in client-server mode (Docker) for test environment
- [ ] Implement Trivy server REST API client: authenticate, submit scan target, fetch results
- [ ] Implement scan status polling (async, configurable timeout)
- [ ] Implement Trivy Operator webhook receiver as alternative input

**Acceptance Criteria:**
- All unit tests pass (mocked Trivy server)
- Webhook receiver correctly parses CRD events

---

### TASK-4.2 — Trivy JSON Parser
**Priority:** Critical | **Effort:** 1 day | **File:** `codesentinel/parsers/trivy/json_parser.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first — commit fixture files to `tests/fixtures/trivy/`:
  - `scan_result_critical.json` — result with CRITICAL CVEs
  - `scan_result_mixed.json` — CRITICAL, HIGH, MEDIUM — verify MEDIUM filtered
  - `scan_result_no_fix.json` — vulnerabilities without `FixedVersion`
  - Tests: `PkgName`, `InstalledVersion`, `FixedVersion`, `VulnerabilityID`, `Severity`, `PrimaryURL` extracted correctly
  - Tests: Findings across all `Results` entries collected
  - Tests: `Severity` filter: MEDIUM/LOW not added to queue
- [ ] Implement parser for Trivy JSON output structure (`Results[].Vulnerabilities[]`)
- [ ] Apply severity filter: `CRITICAL` and `HIGH` only
- [ ] Implement manual JSON file input mode
- [ ] Normalize to internal `Finding` schema with `category=DEPENDENCY` and `target_type` preserved

**Acceptance Criteria:**
- All unit tests pass with all fixture files
- MEDIUM/LOW vulnerabilities are never queued

---

### TASK-4.3 — Trivy Risk Classification
**Priority:** High | **Effort:** 1 day | **File:** `codesentinel/parsers/trivy/mapper.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_trivy_mapper.py`):
  - `FixedVersion` present + `target_type: container` → `LOW` risk → Dockerfile fix prompt
  - `FixedVersion` present + `target_type: os-pkgs` → `LOW` risk → package pin prompt
  - `FixedVersion` present + `target_type: code` → route to SonarQube-style fix logic
  - `FixedVersion` absent → `HIGH` risk (flag only)
- [ ] Implement risk classifier with target type routing
- [ ] Implement `target_type` field preservation in `Finding` schema for downstream routing

**Acceptance Criteria:**
- 100% branch coverage
- Target type routing correctly segregates Dockerfile fixes from code fixes

---

### TASK-4.4 — Trivy LLM Remediation Prompts
**Priority:** Critical | **Effort:** 2 days | **File:** `codesentinel/llm/prompts/trivy.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_trivy_prompts.py`):
  - Dockerfile base image bump prompt contains old and new image tag
  - `apt-get install` prompt correctly adds version pin `=<fixed>`
  - `yum install` prompt correctly adds version constraint
  - Non-container target → routed to SonarQube prompt builder, not Trivy
- [ ] Implement Dockerfile parser: detect `FROM`, `RUN apt-get install`, `RUN yum install`
- [ ] Implement Dockerfile fix prompts:
  - **Base image bump:** `FROM ubuntu:20.04` → `FROM ubuntu:22.04`
  - **apt-get pin:** `apt-get install libssl1.1` → `apt-get install libssl1.1=<fixed_version>`
  - **yum pin:** Add version constraint to `yum install`
- [ ] Test prompts manually against sample Dockerfiles with GPT-4o

**Acceptance Criteria:**
- All unit tests pass
- Prompt never attempts to modify source code when `target_type` is `container`

---

### TASK-4.5 — Trivy End-to-End Integration Test
**Priority:** Critical | **Effort:** 1 day | **File:** `tests/e2e/test_phase4_trivy.py`

**Sub-tasks:**
- [ ] **TDD:** Write E2E tests first, then verify they pass:
  - Scenario A: Trivy CRITICAL JSON → Dockerfile base image bump → lint pass → PR opened
  - Scenario B: Trivy HIGH JSON → apt-get package pin → PR opened
  - Scenario C: Finding without `FixedVersion` → `SKIPPED_HIGH_RISK` + audit log
  - Scenario D: Manual JSON file input → same result as API mode
- [ ] Conduct M5 milestone demo — record screen capture

**Acceptance Criteria (M5):**
- At least 1 base image bump and 1 package pin PR opened for CRITICAL or HIGH CVEs
- `FixedVersion`-absent findings never result in a commit

---

## Phase 5 — Remediation Engine Enhancement
**Duration:** 4 weeks | **Dates:** Jun 15 – Jul 10, 2026 | **Milestone:** M6

### TASK-5.1 — Enhanced Risk Assessment Module
**Priority:** Critical | **Effort:** 3 days | **File:** `codesentinel/agents/risk_classifier.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first — 100% branch coverage required:
  - Policy evaluates all combinations of `(source, severity, rule_id, has_fix_version, target_type)`
  - Per-repo `.codesentinel.yml` override adds/removes rules correctly
  - Classification decision is logged with the triggering rule name
  - `CANNOT_FIX_SAFELY` LLM response feeds back as `HIGH` risk
- [ ] Replace ad-hoc risk checks with formal policy rules engine
- [ ] Load safe-rule lists from `config/safe_rules.yaml`
- [ ] Implement per-repo override mechanism via `.codesentinel.yml`
- [ ] Log every classification decision with the rule that triggered it

**Acceptance Criteria:**
- 100% branch coverage confirmed by `pytest --cov`

---

### TASK-5.2 — Context Retrieval Enhancement
**Priority:** High | **Effort:** 2 days | **File:** `codesentinel/agents/context_retriever.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_context_retriever.py`):
  - Context window retrieves exactly ±50 lines (configurable)
  - Import statements always included regardless of finding line
  - Dependency findings retrieve full manifest file content
  - Context truncated to LLM token limit — priority: finding lines > imports > surrounding context
  - Cached context hit does not call VCS API again in same session
- [ ] Implement configurable context window (default ±50 lines)
- [ ] Implement full import statement extraction regardless of finding line
- [ ] For `DEPENDENCY` category: retrieve full manifest file content
- [ ] Implement context truncation at LLM token limit
- [ ] Implement session-scoped context cache (per repo + file path)

**Acceptance Criteria:**
- All unit tests pass
- Token-limited context always includes finding lines as highest priority

---

### TASK-5.3 — Advanced Prompt Engineering
**Priority:** Critical | **Effort:** 4 days | **File:** `codesentinel/llm/prompt_builder.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_prompt_builder.py`):
  - Few-shot examples are injected for each fix category
  - Chain-of-thought `<think>` block appears before the diff in enhanced mode
  - Output validation rejects responses that contain markdown fences
  - Per-language coding standard injection is present for Python (PEP 8) / JS (Airbnb)
  - Reviewer instruction from PRMonitor is correctly appended on re-runs
- [ ] Implement structured system prompt with role definition and output format contract
- [ ] Implement few-shot examples per fix category (3 examples each):
  - Null pointer fix
  - Hardcoded secret removal
  - Dependency version bump
  - Dockerfile base image update
- [ ] Implement chain-of-thought elicitation: `<think>` block before diff for complex fixes
- [ ] Implement strict unified diff output validation using `difflib`
- [ ] Implement per-language coding standard injection (PEP 8 for Python, Airbnb for JS)
- [ ] Run A/B comparison: base vs enhanced prompts on 20 sample findings; document results

**Acceptance Criteria:**
- All unit tests pass
- Enhanced prompts show measurable improvement in first-pass success rate vs base prompts

---

### TASK-5.4 — LLM Self-Correction Loop
**Priority:** Critical | **Effort:** 3 days | **File:** `codesentinel/agents/fix_generator.py`

**Objective:** Implement Loop 4's retry mechanism — the core reliability feature.

```
FOR attempt IN [1, 2, 3]:
  prompt = build_prompt(finding, attempt, previous_error)
  diff = llm.call(prompt, temperature = 0.0 + (attempt-1) * 0.1)
  IF diff format invalid → previous_error = "Invalid diff format" → CONTINUE
  apply_diff(repo_clone, diff)
  lint_result = linter.run(file, language)
  IF lint_result.passed → FIX_VALIDATED → STOP
  ELSE → previous_error = lint_result.errors → revert_diff → CONTINUE
finding.status = AUTO_FIX_FAILED  (after 3 failures)
```

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_fix_generator.py`):
  - Mock LLM fails twice then succeeds: verify `retries=2` and `FIX_VALIDATED` status
  - Mock LLM fails 3 times: verify `AUTO_FIX_FAILED` status and no commit
  - Temperature escalates: attempt 1 = 0.0, attempt 2 = 0.1, attempt 3 = 0.2
  - Linter error is appended to next prompt on retry
  - `CANNOT_FIX_SAFELY` response from LLM → treated as failure, no commit
  - `FIX_GENERATED` audit event on each attempt; `FIX_FAILED` event after 3 failures
- [ ] Implement retry orchestrator (max 3 retries)
- [ ] Implement linter error feedback injection on retry prompt
- [ ] Implement temperature escalation (0.0 → 0.1 → 0.2)
- [ ] On 3 failures: set `AUTO_FIX_FAILED`, write full audit record, no commit

**Acceptance Criteria:**
- All unit tests pass
- Never commits a fix that failed linting on all 3 attempts

---

### TASK-5.5 — Syntax Validation Module
**Priority:** Critical | **Effort:** 3 days | **File:** `codesentinel/validation/linter_runner.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_linter_runner.py`):
  - Python file with syntax error → flake8 returns failure
  - Valid Python file → flake8 returns pass
  - JS file with eslint error → eslint returns failure
  - Dockerfile with hadolint warning → treated as notice (not failure)
  - Linter not installed → warning logged, validation skipped (not failed)
  - Language detected correctly from file extension
- [ ] Implement language detector (file extension + content sniffing)
- [ ] Implement linter runner registry:
  | Language | Linter | Command |
  |----------|--------|---------|
  | Python | flake8 | `flake8 --select=E,W,F <file>` |
  | JavaScript | eslint | `eslint <file>` |
  | TypeScript | eslint | `eslint --ext .ts <file>` |
  | Java | checkstyle | `checkstyle -c /google_checks.xml <file>` |
  | Go | gofmt | `gofmt -l <file>` |
  | Dockerfile | hadolint | `hadolint <file>` |
- [ ] Implement linter availability check: skip if not installed, log warning
- [ ] Parse linter output: errors = failure, warnings = notice only

**Acceptance Criteria:**
- All unit tests pass
- Known-bad Python and JS files correctly identified as failures

---

### TASK-5.6 — Optional CI Build Verification Hook
**Priority:** Medium | **Effort:** 2 days | **File:** `codesentinel/validation/ci_hook.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_ci_hook.py`):
  - GitHub Actions workflow triggered correctly via API
  - Build result polling waits for completion with configurable timeout
  - Build log summarized and injected into retry prompt on failure
  - CI hook disabled when `ci.enabled: false` in `.codesentinel.yml`
- [ ] Implement CI hook interface reading from `.codesentinel.yml`:
  ```yaml
  ci:
    enabled: true
    provider: github_actions
    workflow: pre-check.yml
    timeout_minutes: 10
  ```
- [ ] Implement GitHub Actions `workflow_dispatch` API trigger
- [ ] Implement GitLab pipeline trigger via pipeline API
- [ ] Implement build result polling with timeout
- [ ] On build failure: inject build log summary into LLM retry loop

**Acceptance Criteria:**
- All unit tests pass (mocked CI endpoints)
- Build log summary correctly injected as `previous_error` on retry

---

### TASK-5.7 — Dry-Run / Report-Only Mode
**Priority:** High | **Effort:** 1 day

**Sub-tasks:**
- [ ] **TDD:** Write tests first:
  - In dry-run mode, no branch is created (mock VCS asserts zero calls to `create_branch`)
  - Dry-run report contains all expected sections (findings, risk classifications, diffs, validation)
  - `--dry-run` CLI flag and `DRY_RUN=true` env var both activate dry-run mode
- [ ] Add `--dry-run` CLI flag to `click` CLI entrypoint
- [ ] Add `DRY_RUN` environment variable support
- [ ] Execute full pipeline (ingest → classify → context → generate → validate) but skip branch, commit, and PR creation
- [ ] Output dry-run report as JSON and human-readable Markdown

**Acceptance Criteria:**
- All unit tests pass
- No VCS mutation occurs in dry-run mode under any code path

---

### TASK-5.8 — Rate Limiting & Reliability Hardening
**Priority:** High | **Effort:** 2 days | **File:** `codesentinel/utils/rate_limiter.py`

**Sub-tasks:**
- [ ] **TDD:** Write tests first (`tests/unit/test_rate_limiter.py`):
  - Token bucket correctly blocks when tokens exhausted
  - Backoff formula: `sleep(min(cap, base * 2^attempt) * random())`
  - `X-RateLimit-Remaining: 0` header triggers wait until reset
  - Circuit breaker opens after 5 consecutive failures
  - Circuit breaker pauses API for 5 minutes then half-opens
- [ ] Implement per-API token bucket:
  - SonarQube: configurable (default 10 req/s)
  - Mend: configurable (default 5 req/s)
  - GitHub: respect `X-RateLimit-Remaining` header
  - GitLab: respect `RateLimit-Remaining` header
  - LLM: respect `x-ratelimit-remaining-requests` header
- [ ] Implement exponential backoff with full jitter
- [ ] Implement circuit breaker: 5 consecutive failures → pause 5 minutes

**Acceptance Criteria:**
- All unit tests pass
- No API is called after circuit breaker opens until pause period expires

---

### TASK-5.9 — M6 Milestone Integration Test
**Priority:** Critical | **Effort:** 1 day

- [ ] End-to-end test: LLM fix fails linting on attempt 1 → self-correction succeeds on attempt 2 → PR opened
- [ ] Dry-run mode test: full pipeline runs, report generated, no VCS mutations
- [ ] CI hook integration test (mocked CI)
- [ ] Conduct M6 milestone demo — record screen capture

**Acceptance Criteria (M6):**
- Self-correction loop working, CI hook tested, dry-run mode confirmed

---

## Phase 6 — Testing, Deployment & Documentation
**Duration:** 3 weeks | **Dates:** Jul 13 – Aug 01, 2026 | **Milestone:** M7

### TASK-6.1 — Full Unit Test Suite
**Priority:** Critical | **Effort:** 3 days

**Coverage targets: ≥80% line coverage overall; 100% branch coverage on risk classifier and auth modules**

- [ ] Run `pytest --cov=codesentinel --cov-report=html` and publish coverage report
- [ ] Gap-fill: write missing unit tests to reach ≥80% line coverage
- [ ] Confirm 100% branch coverage on `risk_classifier.py`, `auth.py`, and `pr_monitor.py`
- [ ] Add mutation testing with `mutmut` on risk classifier (optional stretch goal)

---

### TASK-6.2 — Integration Test Suite
**Priority:** Critical | **Effort:** 3 days | **File:** `tests/integration/`

- [ ] Integration test: SonarQube API → parse → normalize (live sandbox)
- [ ] Integration test: Mend API → parse → normalize (live sandbox)
- [ ] Integration test: Trivy server → parse → normalize (Docker Trivy server)
- [ ] Integration test: GitHub App → create branch → commit → open PR → verify (test repo)
- [ ] Integration test: GitLab Bot → full PR flow (test repo)
- [ ] Integration test: PR comment → PRMonitor → intent classify → amended commit

---

### TASK-6.3 — End-to-End Test Suite
**Priority:** Critical | **Effort:** 3 days | **File:** `tests/e2e/test_all_scenarios.py`

8 required E2E scenarios:
- [ ] **S1:** SonarQube CRITICAL Bug (null pointer) → fix → lint pass → PR opened (Python)
- [ ] **S2:** SonarQube BLOCKER Vulnerability (hardcoded secret) → fix → lint pass → PR opened
- [ ] **S3:** Mend CRITICAL dependency (JSON) → bump `requirements.txt` → PR opened
- [ ] **S4:** Trivy HIGH container CVE (JSON) → Dockerfile base image bump → PR opened
- [ ] **S5:** LLM fix fails linting → self-correction succeeds on attempt 2
- [ ] **S6:** Dry-run mode → report generated; zero VCS mutations confirmed
- [ ] **S7:** PR reviewer comments "Change this to a list comprehension" → PRMonitor detects → agent amends and pushes
- [ ] **S8:** HIGH risk finding (no `FixedVersion`) → `SKIPPED_HIGH_RISK` status → audit log entry written; no commit

---

### TASK-6.4 — Security Audit & Penetration Testing
**Priority:** Critical | **Effort:** 5 days | **Owner:** Security Team + External Auditor

- [ ] Credential audit: verify zero secrets in code, logs, PR descriptions, or env vars outside Vault
- [ ] Prompt injection testing: attempt to manipulate agent via malicious finding content
- [ ] Data leakage review: verify source code does not persist beyond ephemeral workspace
- [ ] Dependency vulnerability scan: run Trivy on the agent's own container image
- [ ] OWASP API security review: all HTTP clients (SonarQube, Mend, GitHub)
- [ ] Penetration test: attempt unauthorized PR creation, log tampering, repo access
- [ ] Remediate all findings before M7 sign-off

---

### TASK-6.5 — Docker & Kubernetes Deployment
**Priority:** Critical | **Effort:** 3 days | **Owner:** DevOps | **File:** `infra/`

- [ ] Write multi-stage `Dockerfile` (builder → runtime, non-root user, minimal base image)
- [ ] Write `docker-compose.yml` for local dev (agent + Redis + Vault dev mode)
- [ ] Write Kubernetes manifests:
  - `Deployment` (replicas: configurable)
  - `ConfigMap` (non-secret config)
  - `ExternalSecret` (Vault/AWS Secrets Manager)
  - `CronJob` (scheduled scan polling, configurable interval)
  - `ServiceAccount` with minimal RBAC
- [ ] Write Helm chart with configurable values: LLM provider, VCS provider, tool endpoints, dry-run toggle
- [ ] Implement health check endpoints: `/health/live`, `/health/ready`
- [ ] Write GitHub Actions CI/CD pipeline: test → build → push → deploy to staging

---

### TASK-6.6 — Monitoring & Alerting
**Priority:** High | **Effort:** 2 days | **Owner:** DevOps

- [ ] Expose Prometheus metrics at `/metrics`:
  - `codesentinel_findings_ingested_total` (labels: source, severity)
  - `codesentinel_fixes_generated_total` (labels: source, outcome)
  - `codesentinel_prs_opened_total` (labels: source)
  - `codesentinel_llm_retries_total` (labels: source)
  - `codesentinel_llm_latency_seconds` (histogram)
  - `codesentinel_api_errors_total` (labels: api, error_type)
- [ ] Create Grafana dashboard: fix rate, failure rate, retry rate, latency
- [ ] Configure alerts:
  - LLM error rate > 20% in 5 min
  - API circuit breaker triggered
  - Queue backlog > 100 findings

---

### TASK-6.7 — User Documentation
**Priority:** High | **Effort:** 3 days | **Owner:** Tech Lead | **File:** `docs/`

- [ ] `docs/setup.md` — prerequisites, installation, Vault config, first run
- [ ] `docs/config.md` — all environment variables and `.codesentinel.yml` options
- [ ] `docs/integrations.md` — SonarQube, Mend, Trivy setup and auth
- [ ] `docs/operator.md` — safe-rule list management, severity filters, dry-run, monitoring
- [ ] `docs/troubleshooting.md` — common errors and remediation steps
- [ ] `docs/prmonitor.md` — how reviewers interact with the PRMonitor feedback loop

---

### TASK-6.8 — Training Materials & M7 Sign-off
**Priority:** Medium | **Effort:** 2 days | **Owner:** Tech Lead + PM

- [ ] Developer onboarding deck (10 slides): architecture, 6 agent loops, adding new tool integrations
- [ ] Security team overview (5 slides): what the agent fixes/flags, audit log access, override mechanisms
- [ ] Demo recording: end-to-end fix from SonarQube CRITICAL bug finding to merged PR + PRMonitor feedback cycle
- [ ] FAQ document: top 20 anticipated questions
- [ ] Obtain M7 stakeholder sign-off

**Acceptance Criteria (M7 — Project Complete):**
- [ ] All tasks completed and merged
- [ ] Unit test coverage ≥80% (confirmed via `pytest --cov`)
- [ ] All 8 E2E scenarios (S1–S8) passing
- [ ] Security audit passed — no critical findings
- [ ] Kubernetes deployment running in staging ≥48 hours without incident
- [ ] All documentation published
- [ ] Stakeholder sign-off obtained

---

## Dependency Map

```
TASK-0.1 → TASK-0.2 → TASK-0.3 → TASK-0.4
                                        ↓
                                   TASK-1.1 (Agent Core)
                                   TASK-1.2 (VCS Auth)
                                   TASK-1.7 (Audit Logger)
                                        ↓
                         TASK-1.3, 1.4, 1.5, 1.6 (VCS Ops + PRMonitor)
                                        ↓
                              TASK-1.8 (M2 Smoke Test)
                                        ↓
                    ┌───────────────────┤
                    ↓                   ↓
             TASK-2.x            [parallel with]
         (SonarQube)             TASK-3.x (Mend)
                    ↓                   ↓
                    └───────────────────┤
                                        ↓
                                 TASK-4.x (Trivy)
                                        ↓
                    TASK-5.1 → 5.2 → 5.3 → 5.4 → 5.5 → 5.6 → 5.7 → 5.8
                                        ↓
                               TASK-6.1 through 6.8
```

> **Note:** Phases 2 (SonarQube) and 3 (Mend) can be developed in parallel by separate developers after TASK-1.8, as they share no code dependencies — only the normalized schema from TASK-0.4.

---

*Generated from approved Implementation Strategy `07_CodeSentinel_Implementation_Strategy.md`*  
*Date: 2026-03-15*
