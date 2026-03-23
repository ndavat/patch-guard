# CodeSentinel — Implementation Plan & Task Breakdown
### Agentic AI Development Guide

**Version:** 1.0  
**Date:** 2026-03-15  
**Project Duration:** 23 Weeks (March 16 – August 21, 2026)  
**Source Documents Validated:** Enterprise-Grade Requirements, SRS, Project Plan, Milestones, Presentation Content

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Agentic Architecture Design](#2-agentic-architecture-design)
3. [Phase 0 — Project Setup & Planning](#3-phase-0--project-setup--planning)
4. [Phase 1 — Core Agent & VCS Integration](#4-phase-1--core-agent--vcs-integration)
5. [Phase 2 — SonarQube Integration](#5-phase-2--sonarqube-integration)
6. [Phase 3 — Mend (SCA) Integration](#6-phase-3--mend-sca-integration)
7. [Phase 4 — Trivy Integration](#7-phase-4--trivy-integration)
8. [Phase 5 — Remediation Engine Enhancement](#8-phase-5--remediation-engine-enhancement)
9. [Phase 6 — Testing, Deployment & Documentation](#9-phase-6--testing-deployment--documentation)
10. [Agentic Loop Specifications](#10-agentic-loop-specifications)
11. [Technology Stack](#11-technology-stack)
12. [Risk Register & Mitigation](#12-risk-register--mitigation)
13. [Definition of Done](#13-definition-of-done)

---

## 1. Project Overview

### 1.1 Purpose

The **CodeSentinel** is an enterprise-grade agentic AI system that automatically remediates low-risk technical debt and security vulnerabilities found by static analysis and security scanning tools. It ingests findings from **SonarQube**, **Mend**, and **Trivy**, generates verified code fixes using LLMs, and submits Pull Requests for human review — with zero manual developer effort for routine issues.

### 1.2 High-Level Goals

- Reduce technical debt backlog by automating low-risk, predictable fixes
- Integrate with existing enterprise security toolchain (SonarQube, Mend, Trivy)
- Generate high-quality, validated PRs with full audit trails
- Support human-in-the-loop feedback and iterative fix refinement
- Deploy as containerized, enterprise-grade infrastructure

### 1.3 Project Timeline Summary

| Phase | Name | Duration | Dates |
|-------|------|----------|-------|
| 0 | Project Setup & Planning | 2 weeks | Mar 16 – Mar 27 |
| 1 | Core Agent & VCS Integration | 4 weeks | Mar 30 – Apr 24 |
| 2 | SonarQube Integration | 3 weeks | Apr 27 – May 15 |
| 3 | Mend (SCA) Integration | 4 weeks | May 18 – Jun 12 |
| 4 | Trivy Integration | 3 weeks | Jun 15 – Jul 03 |
| 5 | Remediation Engine Enhancement | 4 weeks | Jul 06 – Jul 31 |
| 6 | Testing, Deployment & Documentation | 3 weeks | Aug 03 – Aug 21 |
| **Total** | | **23 weeks** | |

### 1.4 Key Milestones

| ID | Milestone | Target Date | Exit Criteria |
|----|-----------|-------------|---------------|
| M1 | Project Plan Approval | Mar 27 | All requirements signed off, environments provisioned |
| M2 | Core Agent & VCS Integration Complete | Apr 24 | Agent can create branch, commit, and open PR on test repo |
| M3 | SonarQube Fixes Operational | May 15 | End-to-end: Sonar JSON → fix → lint pass → PR opened |
| M4 | Mend Dependency Fixes Operational | Jun 12 | CSV/PDF/Excel ingested, dep bump PR opened and validated |
| M5 | Trivy Vulnerability Fixes Operational | Jul 03 | Trivy JSON ingested, container/pkg fix PR opened |
| M6 | Remediation Engine + Validation Complete | Jul 31 | Self-correction loop working, CI hook tested, dry-run mode live |
| M7 | Production Readiness & Docs Complete | Aug 21 | Security audit passed, k8s deployed, docs published |

---

## 2. Agentic Architecture Design

### 2.1 System Overview

The system is structured as **six cooperating agentic loops**, each with a discrete responsibility. Loops communicate via an internal findings queue and a shared state store. All actions are written to a tamper-proof audit log.

```
┌─────────────────────────────────────────────────────────────┐
│                   CodeSentinel                   │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐  │
│  │ Loop 1       │     │ Loop 2       │     │ Loop 3     │  │
│  │ Ingestion    │────▶│ Risk         │────▶│ Context    │  │
│  │ Agent        │     │ Classifier   │     │ Retriever  │  │
│  └──────────────┘     └──────────────┘     └────────────┘  │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐  │
│  │ Loop 6       │     │ Loop 5       │     │ Loop 4     │  │
│  │ Feedback     │◀────│ PR           │◀────│ LLM Fix    │  │
│  │ Monitor      │     │ Automation   │     │ Generator  │  │
│  └──────────────┘     └──────────────┘     └────────────┘  │
│                                                             │
│  ──────────────────────────────────────────────────────     │
│                     Audit Log Store                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Internal Data Schema

Every finding, regardless of source tool, is normalized into this internal schema before entering the agentic pipeline:

```json
{
  "finding_id": "SONAR-12345",
  "source": "sonarqube",
  "tool_version": "10.x",
  "ingested_at": "2026-03-15T10:00:00Z",
  "repo": "org/repo-name",
  "file_path": "src/utils/helper.py",
  "line_start": 42,
  "line_end": 42,
  "severity": "MINOR",
  "rule_id": "python:S1481",
  "message": "Remove this unused import of 'os'.",
  "fix_hint": "Remove unused import",
  "category": "CODE_SMELL",
  "risk_level": null,
  "status": "QUEUED",
  "fix_diff": null,
  "pr_url": null,
  "retries": 0,
  "audit_trail": []
}
```

### 2.3 Agent Orchestration Framework

- **Framework:** LangChain (primary) or CrewAI (alternative)
- **Language:** Python 3.11+
- **Concurrency:** `asyncio` with task queues for parallel repo processing
- **State Store:** Redis or in-memory queue (configurable)
- **Config:** Environment variables + HashiCorp Vault / AWS Secrets Manager at runtime

### 2.4 Safe-to-Fix Policy

Only findings classified as **LOW RISK** proceed to auto-fix. All others are logged and flagged for manual review.

| Category | Examples | Risk Level | Action |
|----------|----------|------------|--------|
| Unused imports | `import os` never used | LOW | Auto-fix |
| Naming conventions | Variable not snake_case | LOW | Auto-fix |
| Deprecated API swap | `collections.Callable` → `collections.abc.Callable` | LOW | Auto-fix |
| Dependency version bump | Direct upgrade path exists in Mend/Trivy | LOW | Auto-fix |
| Container base image bump | FROM ubuntu:20.04 → ubuntu:22.04 | LOW | Auto-fix |
| Complex logic refactors | Business logic changes | HIGH | Manual review |
| Auth/security flows | Authentication logic | HIGH | Manual review |
| No fix version available | CVE with no FixedVersion | HIGH | Manual review |
| Architectural changes | Class restructuring | HIGH | Manual review |

---

## 3. Phase 0 — Project Setup & Planning

**Duration:** 2 weeks | **Dates:** Mar 16 – Mar 27, 2026 | **Milestone:** M1

### Objectives
- Finalize and reconcile all requirements across source documents
- Establish development environment and toolchain
- Provision sandbox credentials for all integrated tools
- Define internal data schemas and agent interface contracts

### Tasks

#### TASK-0.1 — Requirements Reconciliation
**Owner:** Tech Lead | **Effort:** 2 days | **Priority:** Critical

Reconcile the 5 source documents (Enterprise Requirements, SRS, Project Plan, Milestones, Presentation) and produce a single authoritative requirements register.

**Acceptance Criteria:**
- All contradictions resolved (see Risk R-001: Copilot licensing, R-002: Azure Repos MCP spec)
- Requirements register reviewed and signed off by stakeholders
- Any out-of-scope items formally deferred

**Sub-tasks:**
- [ ] Identify and resolve LLM option discrepancies (Copilot added in SRS but not Enterprise Req doc)
- [ ] Clarify Azure Repos MCP server specification — URL, auth method, SDK version
- [ ] Confirm on-prem LLM inference requirement for data sovereignty
- [ ] Document final approved tech stack choices

---

#### TASK-0.2 — Development Environment Setup
**Owner:** DevOps | **Effort:** 2 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Create Python 3.11+ virtual environment with dependency lockfile (`requirements.txt` + `requirements-dev.txt`)
- [ ] Install core dependencies: `langchain`, `openai`, `anthropic`, `requests`, `httpx`, `gitpython`, `pymupdf`, `pandas`, `openpyxl`, `jsonschema`
- [ ] Configure Docker and Docker Compose for local development
- [ ] Set up HashiCorp Vault (dev mode) or AWS Secrets Manager sandbox for credential storage
- [ ] Configure pre-commit hooks: `black`, `isort`, `flake8`, `mypy`
- [ ] Establish Git repo structure (monorepo recommended):
  ```
  codesentinel/
  ├── agents/          # Agent loop implementations
  ├── parsers/         # Tool-specific parsers (sonar, mend, trivy)
  ├── vcs/             # VCS clients (github, gitlab, azure)
  ├── llm/             # LLM clients and prompt templates
  ├── validation/      # Linters and build hooks
  ├── config/          # Config schemas and loaders
  ├── audit/           # Audit log writer
  ├── tests/           # Unit, integration, e2e tests
  └── infra/           # Docker, Helm, k8s manifests
  ```

**Acceptance Criteria:**
- `make dev-setup` runs cleanly on a fresh machine
- All secrets loaded from Vault, zero hardcoded credentials anywhere

---

#### TASK-0.3 — Sandbox Credentials Provisioning
**Owner:** DevOps + Security | **Effort:** 1 day | **Priority:** High

**Sub-tasks:**
- [ ] Provision SonarQube test instance or Community Edition; generate User Token
- [ ] Create Mend sandbox account; obtain User Key and Organization Token
- [ ] Set up Trivy server (Docker) for client-server mode testing
- [ ] Create GitHub App for test organization; capture App ID + private key
- [ ] Create GitLab Bot account with API token on test instance
- [ ] Provision Azure DevOps test project; generate PAT (pending MCP spec decision)
- [ ] Store all credentials in Vault under `codesentinel/secrets/`

**Acceptance Criteria:**
- All credentials verified working against sandbox APIs
- Zero credentials in any config file or environment variable on developer machines

---

#### TASK-0.4 — Internal Schema Definition
**Owner:** Tech Lead + Backend Dev | **Effort:** 1 day | **Priority:** Critical

**Sub-tasks:**
- [ ] Finalize normalized finding schema (see Section 2.2)
- [ ] Define JSON Schema validation file for `finding` objects
- [ ] Define audit log event schema: `{event_type, timestamp, finding_id, agent, details, outcome}`
- [ ] Define PR description template schema
- [ ] Write schema validation utility (`codesentinel/config/schemas.py`)

---

#### TASK-0.5 — M1 Milestone Review
**Owner:** Project Manager | **Effort:** 0.5 days | **Priority:** Critical

- [ ] Conduct milestone review meeting
- [ ] Obtain formal sign-off on requirements register and project plan
- [ ] Confirm team resourcing and availability for Phase 1

---

## 4. Phase 1 — Core Agent & VCS Integration

**Duration:** 4 weeks | **Dates:** Mar 30 – Apr 24, 2026 | **Milestone:** M2

### Objectives
- Build the foundational agent framework used by all subsequent phases
- Implement secure, production-grade VCS integration (GitHub, GitLab, Azure Repos)
- Establish the audit logging backbone
- Implement PR creation, management, and comment feedback loop

### Tasks

#### TASK-1.1 — Agent Core Framework
**Owner:** Backend Dev | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Initialize LangChain agent base class with configurable LLM backend
- [ ] Implement structured logging: JSON-formatted, log level configurable, correlation ID per finding
- [ ] Implement configuration loader: reads from environment variables + Vault at runtime, validates against schema
- [ ] Build central findings queue: accepts normalized findings, dispatches to agent loops
- [ ] Implement graceful shutdown: flush queue, close connections, write final audit entry
- [ ] Write unit tests: config loading, queue operations, logging format

**File:** `codesentinel/agents/core.py`

---

#### TASK-1.2 — VCS Authentication Module
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Critical

Implement secure authentication for all three VCS platforms.

**Sub-tasks:**
- [ ] **GitHub:** Implement GitHub App installation token flow (JWT → installation token refresh cycle)
- [ ] **GitLab:** Implement Bot Token authentication with token validation
- [ ] **Azure DevOps:** Implement PAT authentication (pending MCP spec — may be replaced by MCP session token)
- [ ] Build VCS client factory: returns correct authenticated client based on repo URL
- [ ] Implement token refresh logic with expiry tracking
- [ ] Write unit tests with mocked HTTP responses

**File:** `codesentinel/vcs/auth.py`

---

#### TASK-1.3 — MCP Integration for Azure Repos & GitHub
**Owner:** Backend Dev | **Effort:** 3 days | **Priority:** High

> **Dependency:** Requires Azure Repos MCP server spec (TASK-0.1). If spec is not finalized, implement direct REST API fallback first and add MCP layer in Phase 5.

**Sub-tasks:**
- [ ] Research and document Azure Repos MCP server endpoint and auth handshake
- [ ] Implement MCP session initialization and keep-alive
- [ ] Map MCP operations to agent actions: `checkout_branch`, `commit_files`, `push_branch`, `create_pr`
- [ ] Implement GitHub MCP operations (if MCP preferred over GitHub App REST)
- [ ] Write integration tests against sandbox VCS instances

**File:** `codesentinel/vcs/mcp_client.py`

---

#### TASK-1.4 — Git Operations Module
**Owner:** Backend Dev | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement ephemeral repo clone: clone to temp directory, register cleanup on agent exit
- [ ] Implement branch creation: `fix/<source>-<finding_id>` naming convention
- [ ] Implement file patch application: accept unified diff, apply using `patch` or `git apply`
- [ ] Implement staged commit with structured commit message:
  ```
  fix(<source>): <short description> [<finding_id>]

  Tool: <sonarqube|mend|trivy>
  Finding ID: <id>
  Rule: <rule_id>
  Risk Level: LOW
  Auto-generated by AI CodeSentinel
  ```
- [ ] Implement push to remote branch
- [ ] Implement branch cleanup on PR merge/rejection
- [ ] Write unit tests for all git operations using test repo fixture

**File:** `codesentinel/vcs/git_ops.py`

---

#### TASK-1.5 — Pull Request Creation & Management
**Owner:** Backend Dev | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement PR creation via GitHub REST API and GitLab API
- [ ] Build PR description generator using template:
  ```markdown
  ## Auto-Fix: <Short Summary>

  **Source Tool:** SonarQube / Mend / Trivy
  **Finding ID:** <id>
  **Rule / CVE:** <rule_id or CVE>
  **File:** `<file_path>` (line <line>)

  ### What was changed
  <LLM-generated explanation of fix>

  ### Risk Assessment
  **Risk Level:** LOW
  <Justification: why this is safe to auto-fix>

  ### Validation Results
  - [x] Linter: PASSED (<linter_name> v<version>)
  - [ ] Build verification: Not configured / PASSED

  ---
  *This PR was generated by the CodeSentinel agent.*
  *Review carefully before merging. Reject and comment if changes are needed.*
  ```
- [ ] Implement label application: `auto-fix`, `<source-tool>`, `<severity>`
- [ ] Implement reviewer assignment from repo config file
- [ ] Implement PR status polling (open/merged/closed/review-requested)
- [ ] Write integration tests against GitHub/GitLab sandbox

**File:** `codesentinel/vcs/pr_manager.py`

---

#### TASK-1.6 — PR Comment Feedback Loop (Agent Loop 6)
**Owner:** Backend Dev | **Effort:** 3 days | **Priority:** High

**Sub-tasks:**
- [ ] Implement PR comment poller: fetch new comments on open auto-fix PRs every N minutes (configurable)
- [ ] Implement comment intent classifier using LLM:
  - `APPROVE` → log and stop monitoring
  - `REJECT` → close branch, log reason "human-declined", stop monitoring
  - `CHANGE_REQUEST` → extract instruction, re-trigger fix generation
- [ ] Implement amended commit flow: apply new fix on same branch, push, reply to comment
- [ ] Implement max-revision limit: after 3 change-request cycles, escalate to human with flag
- [ ] Write unit tests for intent classification with sample comments

**File:** `codesentinel/agents/feedback_monitor.py`

---

#### TASK-1.7 — Audit Logging System
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement structured audit log writer: append-only JSON Lines file, configurable output (file, S3, database)
- [ ] Define audit event types: `FINDING_INGESTED`, `RISK_CLASSIFIED`, `CONTEXT_RETRIEVED`, `FIX_GENERATED`, `VALIDATION_PASSED`, `VALIDATION_FAILED`, `PR_CREATED`, `PR_COMMENT_RECEIVED`, `FIX_AMENDED`, `FIX_SKIPPED`, `FIX_FAILED`
- [ ] Ensure every event contains: `event_type`, `timestamp`, `finding_id`, `repo`, `agent_loop`, `outcome`, `details`
- [ ] Store LLM prompt hash (not full prompt) for auditability without PII leakage
- [ ] Write unit tests: event schema validation, append-only enforcement

**File:** `codesentinel/audit/logger.py`

---

#### TASK-1.8 — M2 Milestone Integration Test
**Owner:** QA | **Effort:** 1 day | **Priority:** Critical

- [ ] End-to-end smoke test: manually inject a dummy finding → agent creates branch → commits placeholder file → opens PR on test repo → PR visible in GitHub/GitLab UI
- [ ] Verify audit log contains all expected events
- [ ] Verify no credentials appear in logs or PR description

---

## 5. Phase 2 — SonarQube Integration

**Duration:** 3 weeks | **Dates:** Apr 27 – May 15, 2026 | **Milestone:** M3

### Objectives
- Implement SonarQube API client with token auth and pagination
- Build JSON parser for both API responses and file-based exports
- Develop LLM remediation prompts for common code smells
- Deliver first real end-to-end auto-fix PR from Sonar findings

### Tasks

#### TASK-2.1 — SonarQube API Client
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement HTTP client for SonarQube Web API using `httpx`
- [ ] Implement User Token authentication (Bearer header)
- [ ] Implement `api/issues/search` query with parameters:
  - `types=CODE_SMELL,BUG`
  - `severities=INFO,MINOR,MAJOR`
  - `componentKeys=<project_key>`
  - `resolved=false`
- [ ] Implement pagination: use `p` and `ps` parameters, loop until all pages fetched
- [ ] Implement rate limiting with exponential backoff + jitter
- [ ] Write unit tests with mocked HTTP responses

**File:** `codesentinel/parsers/sonarqube/api_client.py`

---

#### TASK-2.2 — SonarQube JSON Parser
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement parser for SonarQube API JSON response format
- [ ] Extract fields: `key`, `rule`, `severity`, `component` (file path), `line`, `message`, `type`
- [ ] Implement parser for SonarQube GitLab SAST export format (alternative JSON structure)
- [ ] Implement manual JSON file input: accept file path or uploaded JSON content, detect format (API vs export), parse accordingly
- [ ] Normalize all parsed findings to internal schema
- [ ] Validate output against internal schema using `jsonschema`
- [ ] Write unit tests with fixture files for both JSON formats

**File:** `codesentinel/parsers/sonarqube/parser.py`

---

#### TASK-2.3 — SonarQube Issue Mapping & Risk Classification
**Owner:** Backend Dev | **Effort:** 1 day | **Priority:** High

**Sub-tasks:**
- [ ] Implement issue type mapper:
  - `CODE_SMELL` + severity `INFO/MINOR/MAJOR` + rule in safe-list → `LOW` risk
  - `BUG` → `HIGH` risk (flag for manual review, do not auto-fix)
  - Any severity `CRITICAL/BLOCKER` → `HIGH` risk
- [ ] Build initial safe-rule list (seed with common low-risk rules):
  - `python:S1481` — Unused local variable
  - `python:S1128` — Unused import
  - `java:S1134` — Track uses of "FIXME" tags
  - `javascript:S1116` — Empty statements
  - `typescript:S3504` — Variables should be declared with let or const
- [ ] Implement rule-safe-list as external YAML config (operator-extensible)
- [ ] Write unit tests covering all classification branches

**File:** `codesentinel/parsers/sonarqube/mapper.py`

---

#### TASK-2.4 — SonarQube LLM Remediation Prompts
**Owner:** AI/ML Dev | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Design and implement system prompt for SonarQube code smell fixes:
  ```
  You are a senior software engineer performing code quality fixes.
  You will receive a SonarQube finding and the surrounding source code.
  Your task is to produce a minimal, correct unified diff that resolves the finding.
  Rules:
  - Make only the change needed to fix the reported issue
  - Do not change unrelated code
  - Preserve existing logic, variable names (unless naming is the issue), and comments
  - Output ONLY a valid unified diff. No explanation, no markdown fences.
  ```
- [ ] Implement prompt builder: injects finding metadata + ±50 lines code context into prompt
- [ ] Create per-category prompt variants:
  - Unused imports: instruct removal of specific import line
  - Naming conventions: instruct rename with regex pattern hint
  - Deprecated API: provide replacement API in prompt
- [ ] Test prompts against GPT-4o and Claude 3.5 Sonnet; document success rates per rule type
- [ ] Write unit tests: prompt structure validation, diff output parsing

**File:** `codesentinel/llm/prompts/sonarqube.py`

---

#### TASK-2.5 — SonarQube End-to-End Integration Test
**Owner:** QA | **Effort:** 2 days | **Priority:** Critical

- [ ] Seed test repo with known SonarQube violations (unused imports, naming violations)
- [ ] Run full pipeline: SonarQube API → ingest → classify → context retrieve → LLM fix → lint → PR
- [ ] Verify PR description contains correct finding reference, risk level, and lint results
- [ ] Verify audit log completeness for entire pipeline
- [ ] Test manual JSON file input mode with sample Sonar export
- [ ] **M3 sign-off:** at least 3 different rule types fixed successfully end-to-end

---

## 6. Phase 3 — Mend (SCA) Integration

**Duration:** 4 weeks | **Dates:** May 18 – Jun 12, 2026 | **Milestone:** M4

> **Note:** This is the highest-density phase. Allocate a 1-week buffer if PDF extraction complexity is higher than estimated.

### Objectives
- Implement Mend Platform API 3.0 client
- Build parsers for all Mend report formats: PDF, Excel, CSV, JSON
- Develop LLM prompts for dependency version bump remediations
- Deliver automated dependency upgrade PRs

### Tasks

#### TASK-3.1 — Mend API Client
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement Mend Platform API 3.0 HTTP client
- [ ] Implement authentication: User Key + Organization Token (header-based)
- [ ] Implement `GET /api/v3.0/findings/applications` endpoint for Code Application Findings
- [ ] Handle pagination and response envelope unwrapping
- [ ] Implement rate limiting with exponential backoff
- [ ] Write unit tests with mocked responses

**File:** `codesentinel/parsers/mend/api_client.py`

---

#### TASK-3.2 — Mend PDF Parser
**Owner:** Backend Dev | **Effort:** 4 days | **Priority:** High

> This is the most complex parsing task. PDF table extraction requires handling variable layouts.

**Sub-tasks:**
- [ ] Install and configure `PyMuPDF` (`fitz`)
- [ ] Implement PDF table detector: locate vulnerability tables by column header pattern
- [ ] Extract rows: `Vulnerability ID (CVE)`, `Library Name`, `Current Version`, `Fixed Version`, `Severity`
- [ ] Handle multi-page tables and page header/footer noise removal
- [ ] Implement fallback: if table extraction confidence < threshold, flag for manual review
- [ ] Normalize extracted rows to internal finding schema
- [ ] Write unit tests with sample Mend PDF fixtures (redacted)

**File:** `codesentinel/parsers/mend/pdf_parser.py`

---

#### TASK-3.3 — Mend Excel Parser
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** High

**Sub-tasks:**
- [ ] Implement `.xlsx` parser using `pandas` + `openpyxl`
- [ ] Auto-detect header row (search first 10 rows for known column names)
- [ ] Map columns to internal schema: `Library`, `Vulnerability ID`, `Current Version`, `Fixed Version`, `Severity`
- [ ] Handle merged cells and multi-sheet workbooks
- [ ] Normalize to internal finding schema
- [ ] Write unit tests with sample Excel fixtures

**File:** `codesentinel/parsers/mend/excel_parser.py`

---

#### TASK-3.4 — Mend CSV Parser
**Owner:** Backend Dev | **Effort:** 1 day | **Priority:** High

**Sub-tasks:**
- [ ] Implement CSV parser using `pandas`
- [ ] Define column mapping config (YAML, operator-overridable):
  ```yaml
  mend_csv_columns:
    library: ["Library", "Component", "Package"]
    cve: ["Vulnerability ID", "CVE", "CVE ID"]
    top_fix: ["Top Fix", "Remediation", "Fixed Version"]
    severity: ["Severity", "CVSS Score"]
  ```
- [ ] Implement fuzzy column name matching for non-standard exports
- [ ] Normalize to internal finding schema
- [ ] Write unit tests

**File:** `codesentinel/parsers/mend/csv_parser.py`

---

#### TASK-3.5 — Mend JSON Manual Input
**Owner:** Backend Dev | **Effort:** 1 day | **Priority:** Medium

**Sub-tasks:**
- [ ] Define expected Mend JSON export schema
- [ ] Implement JSON parser and normalizer
- [ ] Add to manual input dispatcher (alongside Sonar and Trivy JSON inputs)

**File:** `codesentinel/parsers/mend/json_parser.py`

---

#### TASK-3.6 — Mend Vulnerability Risk Mapping
**Owner:** Backend Dev | **Effort:** 1 day | **Priority:** High

**Sub-tasks:**
- [ ] Implement risk classifier for Mend findings:
  - Has `Fixed Version` AND severity is `LOW/MEDIUM` → `LOW` risk (auto-fix eligible)
  - No `Fixed Version` available → `HIGH` risk (flag manual)
  - Severity `HIGH/CRITICAL` → `HIGH` risk (flag manual, even if fix exists)
- [ ] Write unit tests covering all branches

**File:** `codesentinel/parsers/mend/mapper.py`

---

#### TASK-3.7 — Mend LLM Remediation Prompts
**Owner:** AI/ML Dev | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement manifest file detector: identify `package.json`, `requirements.txt`, `pom.xml`, `build.gradle`, `go.mod`, `Gemfile`, `Cargo.toml` in repo
- [ ] Implement per-manifest prompt templates:
  - **requirements.txt:** `Change <library>==<current> to <library>==<fixed>`
  - **package.json:** `Update "<library>": "<current>" to "<library>": "<fixed>"` in dependencies or devDependencies
  - **pom.xml:** Update `<version>` tag within correct `<dependency>` block
  - **go.mod:** Update `require` directive for module
- [ ] Implement version constraint preservation: if current is `^1.2.3`, output `^<fixed>`
- [ ] Test prompts against multiple manifest types; document accuracy
- [ ] Write unit tests for prompt structure and diff output

**File:** `codesentinel/llm/prompts/mend.py`

---

#### TASK-3.8 — Mend End-to-End Integration Test
**Owner:** QA | **Effort:** 2 days | **Priority:** Critical

- [ ] Create test repo with intentionally outdated dependencies in `requirements.txt` and `package.json`
- [ ] Ingest via CSV and PDF (sample fixtures)
- [ ] Run full pipeline → verify dependency bump PRs opened correctly
- [ ] **M4 sign-off:** at least 2 manifest types fixed, PDF and CSV both ingested successfully

---

## 7. Phase 4 — Trivy Integration

**Duration:** 3 weeks | **Dates:** Jun 15 – Jul 03, 2026 | **Milestone:** M5

### Objectives
- Implement Trivy API client (client-server mode) and Operator integration
- Build parsers for Trivy JSON, SARIF, and CycloneDX output formats
- Develop LLM prompts for container and OS package vulnerability fixes
- Deliver automated container/OS fix PRs

### Tasks

#### TASK-4.1 — Trivy API Client
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Deploy Trivy in client-server mode (Docker) for testing
- [ ] Implement Trivy server REST API client: authenticate, submit scan target, fetch results
- [ ] Implement Trivy Operator webhook receiver (Kubernetes CRD events) as alternative input
- [ ] Handle scan status polling (async scan completion)
- [ ] Implement rate limiting
- [ ] Write unit tests

**File:** `codesentinel/parsers/trivy/api_client.py`

---

#### TASK-4.2 — Trivy JSON Parser
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement parser for Trivy JSON output structure:
  ```json
  {
    "Results": [{
      "Target": "...",
      "Type": "...",
      "Vulnerabilities": [{
        "PkgName": "...",
        "InstalledVersion": "...",
        "FixedVersion": "...",
        "VulnerabilityID": "...",
        "Severity": "...",
        "PrimaryURL": "..."
      }]
    }]
  }
  ```
- [ ] Extract all fields from `Vulnerabilities` array across all `Results`
- [ ] Implement manual JSON file input mode
- [ ] Normalize to internal finding schema
- [ ] Write unit tests with sample Trivy JSON fixtures

**File:** `codesentinel/parsers/trivy/json_parser.py`

---

#### TASK-4.3 — Trivy SARIF & CycloneDX Parsers
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Medium

**Sub-tasks:**
- [ ] Implement SARIF format parser: extract `results[].locations`, `ruleId`, `message`
- [ ] Implement CycloneDX format parser: extract `components[].vulnerabilities`
- [ ] Map both formats to internal finding schema
- [ ] Write unit tests with sample SARIF and CycloneDX fixtures

**File:** `codesentinel/parsers/trivy/sarif_parser.py`, `codesentinel/parsers/trivy/cyclonedx_parser.py`

---

#### TASK-4.4 — Trivy Risk Classification
**Owner:** Backend Dev | **Effort:** 1 day | **Priority:** High

**Sub-tasks:**
- [ ] Implement risk classifier:
  - `FixedVersion` present AND severity `LOW/MEDIUM` → `LOW` risk
  - `FixedVersion` absent → `HIGH` risk
  - Severity `HIGH/CRITICAL` → `HIGH` risk
  - Target type `container` or `os-pkgs` → eligible for auto-fix if LOW risk
  - Target type `code` → route to SonarQube-style fix logic
- [ ] Write unit tests

**File:** `codesentinel/parsers/trivy/mapper.py`

---

#### TASK-4.5 — Trivy LLM Remediation Prompts
**Owner:** AI/ML Dev | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement Dockerfile parser: detect `FROM`, `RUN apt-get install`, `RUN yum install` lines
- [ ] Implement Dockerfile fix prompts:
  - **Base image bump:** Update `FROM ubuntu:20.04` to `FROM ubuntu:22.04`
  - **apt-get package version pin:** Add `=<fixed_version>` to package install command
  - **yum package version:** Add version constraint to install command
- [ ] Implement OS package manifest fix for non-containerized repos (e.g., `requirements-system.txt`)
- [ ] Test prompts against sample Dockerfiles; document success rates
- [ ] Write unit tests

**File:** `codesentinel/llm/prompts/trivy.py`

---

#### TASK-4.6 — Trivy End-to-End Integration Test
**Owner:** QA | **Effort:** 1 day | **Priority:** Critical

- [ ] Create test repo with Dockerfile using outdated base image and packages with known CVEs
- [ ] Run full pipeline: Trivy JSON → classify → fix Dockerfile → lint → PR
- [ ] **M5 sign-off:** at least one Dockerfile base image bump and one package pin PR opened successfully

---

## 8. Phase 5 — Remediation Engine Enhancement

**Duration:** 4 weeks | **Dates:** Jul 06 – Jul 31, 2026 | **Milestone:** M6

### Objectives
- Harden the remediation engine with advanced prompt engineering
- Implement multi-language syntax validation via linters
- Build LLM self-correction retry loop
- Implement optional CI build verification hook
- Add dry-run / report-only mode
- Implement robust rate limiting across all external APIs

### Tasks

#### TASK-5.1 — Enhanced Risk Assessment Module
**Owner:** AI/ML Dev + Backend Dev | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Replace ad-hoc risk checks with formal policy rules engine
- [ ] Implement rule evaluation against finding attributes: source, type, severity, rule_id, has_fix_version
- [ ] Load safe-rule lists from external YAML config (operator-maintainable without code change)
- [ ] Implement override mechanism: per-repo `.codesentinel.yml` can add or remove rules from safe list
- [ ] Add logging: every classification decision logged with rule that triggered it
- [ ] Write unit tests: 100% branch coverage on risk classifier

**File:** `codesentinel/agents/risk_classifier.py`

---

#### TASK-5.2 — Context Retrieval Enhancement
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** High

**Sub-tasks:**
- [ ] Upgrade context window: fetch ±50 lines around finding (configurable, default 50)
- [ ] Add file-level context: include all import statements regardless of finding line
- [ ] For dependency findings: include full manifest file content (not just surrounding lines)
- [ ] Implement context truncation: if total context > LLM token limit, prioritize finding lines + imports
- [ ] Cache retrieved contexts per session to avoid redundant VCS API calls
- [ ] Write unit tests

**File:** `codesentinel/agents/context_retriever.py`

---

#### TASK-5.3 — Advanced Prompt Engineering
**Owner:** AI/ML Dev | **Effort:** 4 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement structured system prompt with role definition, output format contract, and coding standards injection
- [ ] Implement few-shot examples per fix category (3 examples each): unused import removal, naming fix, dep bump, Dockerfile update
- [ ] Implement chain-of-thought elicitation for complex fixes: `<think>` block before diff
- [ ] Implement output format enforcement: strict unified diff, validated with `difflib` before accepting
- [ ] Implement per-language coding standard injection (e.g., PEP 8 for Python, Airbnb style for JS)
- [ ] Run A/B comparison: base prompts vs enhanced prompts on 20 sample findings; measure first-pass success rate
- [ ] Document final prompt templates with rationale

**File:** `codesentinel/llm/prompt_builder.py`

---

#### TASK-5.4 — LLM Self-Correction Loop
**Owner:** AI/ML Dev + Backend Dev | **Effort:** 3 days | **Priority:** Critical

This is Agent Loop 4's retry mechanism — the core reliability feature of the system.

**Sub-tasks:**
- [ ] Implement retry orchestrator: wraps LLM call + validation in loop with max 3 retries
- [ ] On validation failure: append linter error output to next prompt:
  ```
  The previous fix attempt produced the following linter error:
  <linter_output>
  Please revise the unified diff to resolve this error while still fixing the original issue.
  Output ONLY the corrected unified diff.
  ```
- [ ] Track retry count on each finding object; log each attempt with prompt hash and outcome
- [ ] After 3 failures: set finding status to `AUTO_FIX_FAILED`, write full audit record, do not commit anything
- [ ] Implement temperature escalation on retries: attempt 1 = 0.0, attempt 2 = 0.1, attempt 3 = 0.2
- [ ] Write unit tests: mock LLM to fail twice then succeed; verify retry behavior

**File:** `codesentinel/agents/fix_generator.py`

---

#### TASK-5.5 — Syntax Validation Module
**Owner:** Backend Dev | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Implement language detector: detect language from file extension and content
- [ ] Implement linter runner registry:
  | Language | Linter | Command |
  |----------|--------|---------|
  | Python | flake8 | `flake8 --select=E,W,F <file>` |
  | JavaScript | eslint | `eslint <file>` |
  | TypeScript | eslint | `eslint --ext .ts <file>` |
  | Java | checkstyle | `checkstyle -c /google_checks.xml <file>` |
  | Go | gofmt | `gofmt -l <file>` |
  | YAML/Dockerfile | hadolint | `hadolint <file>` |
- [ ] Implement linter availability check: skip if linter not installed, log warning
- [ ] Run linter on modified file only (not entire repo) for speed
- [ ] Parse linter output: detect errors vs warnings; treat errors as failures, warnings as notices
- [ ] Write unit tests: inject known bad Python/JS and verify linter catches it

**File:** `codesentinel/validation/linter_runner.py`

---

#### TASK-5.6 — Optional CI Build Verification Hook
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** Medium

**Sub-tasks:**
- [ ] Implement CI hook interface: configurable per repo in `.codesentinel.yml`:
  ```yaml
  ci:
    enabled: true
    provider: github_actions   # or gitlab_ci, jenkins
    workflow: pre-check.yml
    timeout_minutes: 10
  ```
- [ ] Implement GitHub Actions trigger via `workflow_dispatch` API
- [ ] Implement GitLab pipeline trigger via pipeline API
- [ ] Implement build result polling with timeout
- [ ] On build failure: feed build log summary back into LLM retry loop
- [ ] Write integration tests with mock CI endpoints

**File:** `codesentinel/validation/ci_hook.py`

---

#### TASK-5.7 — Dry-Run / Report-Only Mode
**Owner:** Backend Dev | **Effort:** 1 day | **Priority:** High

**Sub-tasks:**
- [ ] Add `--dry-run` CLI flag and `DRY_RUN=true` environment variable
- [ ] In dry-run mode: execute full pipeline (ingest → classify → retrieve → generate → validate) but skip branch creation, commit, and PR creation
- [ ] Output dry-run report as JSON and human-readable Markdown:
  - Findings processed
  - Risk classifications
  - Fixes that would have been generated (with diff)
  - Validation results
  - Estimated PRs that would be opened
- [ ] Write unit tests

---

#### TASK-5.8 — Rate Limiting & Reliability Hardening
**Owner:** Backend Dev | **Effort:** 2 days | **Priority:** High

**Sub-tasks:**
- [ ] Implement centralized rate limiter with per-API token bucket:
  - SonarQube: configurable (default 10 req/s)
  - Mend: configurable (default 5 req/s)
  - GitHub API: respect `X-RateLimit-Remaining` header
  - GitLab API: respect `RateLimit-Remaining` header
  - LLM API: respect `x-ratelimit-remaining-requests` header
- [ ] Implement exponential backoff with full jitter: `sleep(min(cap, base * 2^attempt) * random())`
- [ ] Implement circuit breaker: after 5 consecutive failures on an API, pause that tool's ingestion for 5 minutes
- [ ] Write unit tests

**File:** `codesentinel/utils/rate_limiter.py`

---

## 9. Phase 6 — Testing, Deployment & Documentation

**Duration:** 3 weeks | **Dates:** Aug 03 – Aug 21, 2026 | **Milestone:** M7

### Objectives
- Achieve comprehensive test coverage across all modules
- Pass security audit and penetration testing
- Deploy production Kubernetes infrastructure
- Complete all documentation and training materials

### Tasks

#### TASK-6.1 — Unit Test Suite
**Owner:** QA + All Devs | **Effort:** 3 days | **Priority:** Critical

**Coverage targets: ≥80% line coverage, 100% branch coverage on risk classifier and auth modules**

**Sub-tasks:**
- [ ] Unit tests: all parsers (Sonar, Mend PDF/Excel/CSV/JSON, Trivy JSON/SARIF/CycloneDX)
- [ ] Unit tests: all API clients with mocked HTTP responses
- [ ] Unit tests: risk classifier — all classification branches
- [ ] Unit tests: prompt builder — all template variants
- [ ] Unit tests: linter runner — happy path and failure paths
- [ ] Unit tests: git operations — using in-memory git fixture
- [ ] Unit tests: audit logger — event schema validation
- [ ] Run `pytest --cov` and publish coverage report

---

#### TASK-6.2 — Integration Test Suite
**Owner:** QA | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Integration test: SonarQube API → parse → normalize (live sandbox)
- [ ] Integration test: Mend API → parse → normalize (live sandbox)
- [ ] Integration test: Trivy server → parse → normalize (Docker Trivy server)
- [ ] Integration test: GitHub App → create branch → commit → open PR → verify (test repo)
- [ ] Integration test: GitLab Bot → full PR flow (test repo)
- [ ] Integration test: PR comment → feedback loop → amended commit

---

#### TASK-6.3 — End-to-End Test Suite
**Owner:** QA | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] E2E test scenario 1: SonarQube unused import → fix → lint pass → PR opened (Python)
- [ ] E2E test scenario 2: Mend CSV dep vulnerability → bump requirements.txt → PR opened
- [ ] E2E test scenario 3: Trivy JSON container CVE → Dockerfile base image bump → PR opened
- [ ] E2E test scenario 4: LLM fix fails linting → self-correction succeeds on retry 2
- [ ] E2E test scenario 5: dry-run mode → report generated, no PR created
- [ ] E2E test scenario 6: PR reviewer requests change → agent amends and pushes
- [ ] E2E test scenario 7: HIGH risk finding → skipped, audit log entry written

---

#### TASK-6.4 — Security Audit & Penetration Testing
**Owner:** Security Team + External Auditor | **Effort:** 5 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Credential audit: verify zero secrets in code, logs, PR descriptions, or environment variables outside Vault
- [ ] Prompt injection testing: attempt to manipulate agent behavior via malicious findings content
- [ ] Data leakage review: verify source code does not persist beyond ephemeral workspace
- [ ] Dependency vulnerability scan: run Trivy on the agent's own container image
- [ ] OWASP API security review: all HTTP clients (SonarQube, Mend, GitHub)
- [ ] Penetration test: attempt unauthorized PR creation, log tampering, repo access
- [ ] Remediate all findings before M7 sign-off

---

#### TASK-6.5 — Docker & Kubernetes Deployment
**Owner:** DevOps | **Effort:** 3 days | **Priority:** Critical

**Sub-tasks:**
- [ ] Write `Dockerfile`: multi-stage build (builder → runtime), non-root user, minimal base image
- [ ] Write `docker-compose.yml` for local development (agent + Redis + Vault dev mode)
- [ ] Write Kubernetes manifests:
  - `Deployment` (agent, replicas: configurable)
  - `ConfigMap` (non-secret config)
  - `ExternalSecret` (Vault/AWS Secrets Manager integration)
  - `CronJob` (scheduled scan polling, configurable interval)
  - `ServiceAccount` with minimal RBAC
- [ ] Write Helm chart with values for: LLM provider, VCS provider, tool endpoints, dry-run toggle
- [ ] Implement Kubernetes health check endpoints: `/health/live`, `/health/ready`
- [ ] Write CI/CD pipeline (GitHub Actions) for: test → build → push to container registry → deploy to staging

---

#### TASK-6.6 — Monitoring & Alerting
**Owner:** DevOps | **Effort:** 2 days | **Priority:** High

**Sub-tasks:**
- [ ] Expose Prometheus metrics endpoint `/metrics`:
  - `codesentinel_findings_ingested_total` (labels: source, severity)
  - `codesentinel_fixes_generated_total` (labels: source, outcome: success/failed/skipped)
  - `codesentinel_prs_opened_total` (labels: source)
  - `codesentinel_llm_retries_total` (labels: source)
  - `codesentinel_llm_latency_seconds` (histogram)
  - `codesentinel_api_errors_total` (labels: api, error_type)
- [ ] Create Grafana dashboard with key panels: fix rate, failure rate, retry rate, latency
- [ ] Configure alerts: LLM error rate > 20% in 5 min, API circuit breaker triggered, queue backlog > 100 findings

---

#### TASK-6.7 — User Documentation
**Owner:** Tech Writer + Tech Lead | **Effort:** 3 days | **Priority:** High

**Deliverables:**
- [ ] **Setup Guide** (`docs/setup.md`): prerequisites, installation, Vault config, first run
- [ ] **Configuration Reference** (`docs/config.md`): all environment variables and `.codesentinel.yml` options
- [ ] **Tool Integration Guide** (`docs/integrations.md`): SonarQube, Mend, Trivy setup and auth
- [ ] **Operator Guide** (`docs/operator.md`): safe-rule list management, dry-run, monitoring
- [ ] **Troubleshooting Runbook** (`docs/troubleshooting.md`): common errors and remediation steps
- [ ] **API Reference** (`docs/api.md`): internal REST API if exposed (dry-run trigger, status endpoints)

---

#### TASK-6.8 — Training Materials
**Owner:** Tech Lead + PM | **Effort:** 2 days | **Priority:** Medium

**Deliverables:**
- [ ] **Developer Onboarding Deck** (10 slides): architecture, agent loops, adding new tool integrations
- [ ] **Security Team Overview** (5 slides): what the agent does/doesn't touch, audit log access, override mechanisms
- [ ] **Demo Walkthrough Recording**: screen recording of end-to-end fix from SonarQube finding to merged PR
- [ ] **FAQ Document**: top 20 anticipated questions from reviewers and operators

---

## 10. Agentic Loop Specifications

### Loop 1 — Ingestion Agent

**Trigger:** Scheduled poll (configurable interval) OR manual file upload OR webhook  
**Input:** Tool API credentials or file path  
**Output:** Normalized findings → findings queue  

```
START
  FOR each configured tool (SonarQube, Mend, Trivy):
    IF api_mode:
      authenticate(tool)
      findings_raw = fetch_all_pages(tool.api)
    ELSE IF file_mode:
      findings_raw = parse_file(file_path, detect_format())
    findings_normalized = normalize(findings_raw, tool_schema)
    validate_schema(findings_normalized)
    audit_log(FINDING_INGESTED, count=len(findings_normalized))
    queue.push_all(findings_normalized)
END
```

---

### Loop 2 — Risk Classifier

**Trigger:** Finding dequeued from findings queue  
**Input:** Normalized finding  
**Output:** Finding with `risk_level` set → classification queue  

```
START
  finding = queue.pop()
  policy = load_policy(finding.source, finding.repo)
  risk_level = evaluate_policy(finding, policy)
  finding.risk_level = risk_level
  audit_log(RISK_CLASSIFIED, finding_id, risk_level, rule_triggered)
  IF risk_level == HIGH:
    finding.status = SKIPPED_HIGH_RISK
    write_report(finding)
    STOP
  ELSE:
    classification_queue.push(finding)
END
```

---

### Loop 3 — Context Retriever

**Trigger:** Finding dequeued from classification queue  
**Input:** LOW-risk normalized finding  
**Output:** Finding with `code_context` attached → fix queue  

```
START
  finding = classification_queue.pop()
  repo = vcs_client.clone_ephemeral(finding.repo)
  file_content = repo.read_file(finding.file_path)
  context_lines = extract_context(file_content, finding.line_start, window=50)
  imports = extract_imports(file_content)
  IF finding.category == DEPENDENCY:
    manifest = find_and_read_manifest(repo)
    finding.manifest_content = manifest
  finding.code_context = merge(context_lines, imports)
  audit_log(CONTEXT_RETRIEVED, finding_id)
  fix_queue.push(finding)
  cleanup_ephemeral_clone(repo)
END
```

---

### Loop 4 — LLM Fix Generator

**Trigger:** Finding dequeued from fix queue  
**Input:** Finding with code context  
**Output:** Finding with validated `fix_diff` → pr queue OR marked failed  

```
START
  finding = fix_queue.pop()
  FOR attempt IN [1, 2, 3]:
    prompt = build_prompt(finding, attempt, previous_error=None)
    diff_raw = llm.call(prompt, temperature=0.0 + (attempt-1)*0.1)
    diff = parse_unified_diff(diff_raw)
    IF diff is invalid:
      previous_error = "Invalid diff format"
      CONTINUE
    apply_diff(repo_clone, diff)
    lint_result = linter.run(finding.file_path, finding.language)
    IF lint_result.passed:
      finding.fix_diff = diff
      finding.status = FIX_VALIDATED
      audit_log(VALIDATION_PASSED, finding_id, attempt)
      pr_queue.push(finding)
      STOP
    ELSE:
      previous_error = lint_result.errors
      revert_diff(repo_clone)
      audit_log(VALIDATION_FAILED, finding_id, attempt, lint_result.errors)
  finding.status = AUTO_FIX_FAILED
  audit_log(FIX_FAILED, finding_id, retries=3)
END
```

---

### Loop 5 — PR Automation Agent

**Trigger:** Finding dequeued from PR queue  
**Input:** Finding with validated fix diff  
**Output:** PR opened on VCS; finding status updated  

```
START
  finding = pr_queue.pop()
  repo = vcs_client.clone(finding.repo)
  branch_name = f"fix/{finding.source}-{finding.finding_id}"
  repo.create_branch(branch_name)
  repo.apply_diff(finding.fix_diff)
  commit_msg = build_commit_message(finding)
  repo.commit_and_push(branch_name, commit_msg)
  pr_description = build_pr_description(finding)
  pr_url = vcs_client.create_pr(
    branch=branch_name,
    title=f"[Auto-Fix] {finding.message[:72]}",
    description=pr_description,
    labels=["auto-fix", finding.source, finding.severity],
    reviewers=get_reviewers(finding.repo)
  )
  finding.pr_url = pr_url
  finding.status = PR_OPEN
  audit_log(PR_CREATED, finding_id, pr_url)
  monitor_queue.push(finding)
END
```

---

### Loop 6 — Feedback Monitor

**Trigger:** Scheduled poll on open auto-fix PRs  
**Input:** PR with new human comments  
**Output:** Amended commit OR PR closed  

```
START
  FOR each finding IN monitor_queue WHERE status == PR_OPEN:
    comments = vcs_client.get_new_comments(finding.pr_url, since=finding.last_checked)
    IF no new comments: CONTINUE
    FOR comment IN comments:
      intent = llm.classify_intent(comment.body)
      IF intent == APPROVE:
        finding.status = PR_APPROVED
        audit_log(PR_APPROVED, finding_id)
        monitor_queue.remove(finding)
      ELIF intent == REJECT:
        vcs_client.close_pr(finding.pr_url)
        finding.status = HUMAN_DECLINED
        audit_log(PR_REJECTED, finding_id, reason=comment.body)
        monitor_queue.remove(finding)
      ELIF intent == CHANGE_REQUEST:
        IF finding.revision_count >= 3:
          add_pr_comment("Max revisions reached. Please resolve manually.")
          finding.status = ESCALATED
          monitor_queue.remove(finding)
        ELSE:
          finding.reviewer_instruction = comment.body
          fix_queue.push(finding)  // re-run Loop 4
          finding.revision_count += 1
          audit_log(FIX_AMENDED, finding_id, revision=finding.revision_count)
    finding.last_checked = now()
END
```

---

## 11. Technology Stack

### Core

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Language | Python | 3.11+ | Required for asyncio improvements |
| Agent Framework | LangChain | Latest stable | Primary; CrewAI as alternative |
| HTTP Client | httpx | Latest | Async support |
| Git Operations | GitPython | Latest | Local git ops |

### LLM Providers

| Provider | Model | Use Case | Notes |
|----------|-------|----------|-------|
| OpenAI | GPT-4o | Primary code reasoning | High accuracy, higher cost |
| Anthropic | Claude 3.5 Sonnet | Alternative | Good code reasoning, cost-effective |
| GitHub Copilot | auto-mode | Optional enterprise | Requires Copilot Enterprise license |

### Parsing Libraries

| Library | Use Case |
|---------|----------|
| PyMuPDF (fitz) | Mend PDF extraction |
| pandas | Excel/CSV parsing |
| openpyxl | Excel write support |
| jsonschema | Schema validation |

### Validation

| Language | Linter |
|----------|--------|
| Python | flake8, pylint |
| JavaScript/TypeScript | eslint |
| Java | checkstyle |
| Go | gofmt |
| Dockerfile | hadolint |

### Infrastructure

| Component | Technology |
|-----------|-----------|
| Containerization | Docker (multi-stage) |
| Orchestration | Kubernetes + Helm |
| Secret Management | HashiCorp Vault / AWS Secrets Manager |
| Monitoring | Prometheus + Grafana |
| Alerting | PagerDuty / Alertmanager |
| CI/CD | GitHub Actions |

### VCS Connectivity

| Platform | Method |
|----------|--------|
| GitHub | GitHub App (recommended) or PAT |
| GitLab | Bot Token |
| Azure DevOps | PAT or MCP server (spec TBD — TASK-0.1) |

---

## 12. Risk Register & Mitigation

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R-001 | GitHub Copilot enterprise licensing not approved | Medium | Low | Copilot is optional; GPT-4o/Claude are primary LLMs. Decouple LLM config from agent logic. |
| R-002 | Azure Repos MCP server spec not finalized before Phase 1 | High | Medium | Implement direct Azure DevOps REST API in Phase 1; add MCP layer as enhancement in Phase 5. |
| R-003 | Mend PDF table extraction fails on non-standard report layouts | High | Medium | Implement confidence scoring; fall back to manual review flag. Add 1-week buffer to Phase 3 estimate. |
| R-004 | Phase 3 timeline underestimated | Medium | Medium | Build PDF parser (TASK-3.2) first; if >3 days behind after 2 days, escalate and adjust scope. |
| R-005 | On-prem LLM inference required for data sovereignty | Medium | High | Evaluate Ollama (Llama-3) or Azure OpenAI private endpoint as on-prem options. Decide in Phase 0. |
| R-006 | LLM generates incorrect diffs for complex manifest formats (pom.xml) | Medium | Medium | Extensive few-shot examples in prompts; add pom.xml-specific parser as fallback to LLM. |
| R-007 | Security audit uncovers critical issues in Phase 6 | Low | High | Conduct rolling security reviews from Phase 1 (credential audit at every milestone). |
| R-008 | No slack between phases — any slip cascades | High | High | Add 3-day buffer at end of Phase 3 (highest risk phase). Track velocity weekly from Phase 1. |

---

## 13. Definition of Done

### Per Task
- [ ] Code written, reviewed, and merged to main branch
- [ ] Unit tests written and passing (≥80% coverage for new code)
- [ ] No secrets in code or logs
- [ ] Audit log events emitted correctly
- [ ] Documentation updated if public interface changed

### Per Phase
- [ ] All tasks in phase completed and merged
- [ ] Integration test for phase passing against sandbox
- [ ] Milestone demo conducted and recorded
- [ ] Phase retrospective completed; risks updated

### Project Complete (M7)
- [ ] All 40 tasks completed
- [ ] Unit test coverage ≥80% overall
- [ ] All E2E scenarios (TASK-6.3) passing
- [ ] Security audit passed with no critical findings
- [ ] Kubernetes deployment running in staging for ≥48 hours without incident
- [ ] All documentation published
- [ ] Training materials delivered
- [ ] Stakeholder sign-off obtained

---

*Document generated: 2026-03-15*  
*Source: CodeSentinel — Enterprise Requirements, SRS, Project Plan, Milestones (validated)*
