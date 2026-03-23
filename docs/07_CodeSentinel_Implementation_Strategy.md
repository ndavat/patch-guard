# CodeSentinel — Structured Implementation Strategy

### Autonomous AI Auto-Fixer: Enterprise-Grade Remediation Agent

**Version:** 1.0  
**Date:** 2026-03-15  
**Status:** Strategy for Approval — To be broken down into executable tasks for Gemini 3 Flash  
**Source Documents Validated:** Enterprise Requirements, SRS, Project Plan, Milestones, Presentation Content, Recommended Frameworks

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architectural Approach](#2-architectural-approach)
3. [Technology Integration Strategy](#3-technology-integration-strategy)
4. [Development Phases](#4-development-phases)
5. [Modularity & Extensibility Design](#5-modularity--extensibility-design)
6. [Scalability Architecture](#6-scalability-architecture)
7. [Security & Compliance Architecture](#7-security--compliance-architecture)
8. [Test-Driven Development Strategy](#8-test-driven-development-strategy)
9. [Risk Management & Contingency](#9-risk-management--contingency)
10. [Success Criteria & Definition of Done](#10-success-criteria--definition-of-done)

---

## 1. Executive Summary

### 1.1 Problem Statement

Enterprise development teams face a growing backlog of **critical and high-severity** security vulnerabilities and bugs identified by static analysis (SonarQube), SCA scanners (Mend), and container vulnerability scanners (Trivy). These findings — blocking bugs, critical vulnerabilities, and high-severity CVEs — demand urgent remediation but compete for developer bandwidth against feature delivery. The result: critical security debt lingers in production.

### 1.2 Solution

**CodeSentinel** is an autonomous AI agent that accelerates the remediation of **high-severity** findings. It ingests critical and high-priority scan results from SonarQube (Bugs/Vulnerabilities at Blocker/Critical severity), Mend (Critical/High SCA findings), and Trivy (Critical/High container vulnerabilities) — all via **JSON format** — classifies them against a Safe-to-Fix policy; generates verified code patches using LLMs; validates those patches with language-specific linters; and submits fully-documented Pull Requests for mandatory human review.

### 1.3 Strategic Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Six Cooperating Agentic Loops** | Discrete responsibilities enable independent scaling, testing, and failure isolation |
| **Normalized Internal Schema** | Single data contract decouples tool-specific parsers from remediation logic |
| **LLM-Agnostic Interface** | Swap between GPT-4o, Claude 3.5 Sonnet, or GitHub Copilot without code changes |
| **Human-in-the-Loop by Default** | Every fix goes through PR review; the agent amends based on reviewer feedback |
| **Audit-Everything** | Tamper-proof event log for every action — ingestion through PR merge |
| **TDD from Day One** | Every component built test-first; ≥80% coverage enforced at every milestone |

---

## 2. Architectural Approach

### 2.1 System Topology

CodeSentinel is structured as **six cooperating agentic loops** communicating via internal queues, with a shared audit log store. This architecture was chosen over a monolithic agent design for three critical reasons: (1) each loop can be developed, tested, and scaled independently; (2) failure in one loop (e.g., LLM timeout) does not cascade to others; and (3) new tool integrations only touch Loop 1 (Ingestion) without modifying downstream logic.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           CodeSentinel                                   │
│                                                                          │
│  ┌────────────────┐     ┌────────────────┐     ┌──────────────────┐     │
│  │  LOOP 1        │     │  LOOP 2        │     │  LOOP 3          │     │
│  │  Ingestion     │────▶│  Risk          │────▶│  Context         │     │
│  │  Agent         │     │  Classifier    │     │  Retriever       │     │
│  │                │     │                │     │                  │     │
│  │  SonarQube     │     │  Safe-to-Fix   │     │  ±50 lines       │     │
│  │  Mend          │     │  Policy Engine │     │  + imports       │     │
│  │  Trivy         │     │                │     │  + manifests     │     │
│  └────────────────┘     └────────────────┘     └──────────────────┘     │
│         │                      │                        │               │
│         ▼                      ▼                        ▼               │
│  ┌────────────────┐     ┌────────────────┐     ┌──────────────────┐     │
│  │  LOOP 6        │     │  LOOP 5        │     │  LOOP 4          │     │
│  │  Feedback      │◀────│  PR            │◀────│  LLM Fix         │     │
│  │  Monitor       │     │  Automation    │     │  Generator       │     │
│  │                │     │                │     │                  │     │
│  │  PRMonitor    │     │  Branch/commit │     │  Prompt build    │     │
│  │  Intent classify│     │  PR create     │     │  LLM call        │     │
│  │  Amend/escalate │     │  Label/assign  │     │  Lint validate   │     │
│  └────────────────┘     └────────────────┘     │  Self-correct ×3 │     │
│                                                 └──────────────────┘     │
│  ════════════════════════════════════════════════════════════════════    │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │          Audit Log Store  ·  Findings Queue  ·  State Store     │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Normalized Internal Data Schema

Every finding — regardless of whether it originates from SonarQube, Mend, or Trivy — is normalized into a single canonical schema before entering the agentic pipeline. This is the foundational design decision that enables the remediation engine to be tool-agnostic.

```json
{
  "finding_id": "SONAR-12345",
  "source": "sonarqube | mend | trivy",
  "tool_version": "10.x",
  "ingested_at": "2026-03-15T10:00:00Z",
  "repo": "org/repo-name",
  "file_path": "src/utils/helper.py",
  "line_start": 42,
  "line_end": 42,
  "severity": "CRITICAL | HIGH | BLOCKER",
  "rule_id": "python:S5443",
  "message": "Make sure this file handling is safe here.",
  "fix_hint": "Use secure file handling",
  "category": "BUG | VULNERABILITY | DEPENDENCY",
  "risk_level": "LOW | HIGH | null",
  "status": "QUEUED | CLASSIFIED | CONTEXT_READY | FIX_VALIDATED | PR_OPEN | PR_APPROVED | AUTO_FIX_FAILED | SKIPPED_HIGH_RISK | HUMAN_DECLINED | ESCALATED",
  "fix_diff": null,
  "pr_url": null,
  "retries": 0,
  "revision_count": 0,
  "code_context": null,
  "manifest_content": null,
  "audit_trail": []
}
```

### 2.2.1 Ingestion Criteria

The agent only ingests findings matching these **severity and type filters** — all via **JSON format**:

| Tool | Types Ingested | Severities Ingested | File Format |
|------|---------------|--------------------|-----------|
| **SonarQube** | Bug, Vulnerability | Blocker, Critical | JSON |
| **Mend** | All (SCA findings) | Critical, High | JSON |
| **Trivy** | All (container/OS vulnerabilities) | CRITICAL, HIGH | JSON |

### 2.3 Safe-to-Fix Policy Engine

Because CodeSentinel targets **Critical and High severity findings**, the Safe-to-Fix policy uses a more cautious, tiered approach. Only findings with a **clear, deterministic fix path** and limited blast radius proceed to auto-fix. All others receive an AI-generated fix *suggestion* attached to the PR but require explicit human approval before merge.

The policy is implemented as an external YAML configuration, operator-extensible without code changes, with per-repo overrides via `.codesentinel.yml`.

| Category | Examples | Risk Level | Action |
|----------|----------|------------|--------|
| Dependency version bump (direct) | `FixedVersion` available, direct dependency | LOW | Auto-fix PR (human review required) |
| Container base image bump | `FROM ubuntu:20.04` → `ubuntu:22.04` | LOW | Auto-fix PR (human review required) |
| Known vulnerability pattern fix | Insecure headers, hardcoded secrets removal | LOW | Auto-fix PR (human review required) |
| Transitive dependency vulnerability | Fix requires cascading dependency changes | HIGH | Fix suggestion only — manual review |
| Complex bug fix | Logic errors, null pointer, race conditions | HIGH | Fix suggestion only — manual review |
| Auth/security flow changes | Authentication/authorization logic | HIGH | Flag only — no fix generated |
| No fix version available | CVE without FixedVersion | HIGH | Flag only — no fix generated |
| Architectural/multi-file changes | Changes spanning 3+ files or core abstractions | HIGH | Flag only — no fix generated |

> **Key difference from low-risk strategies:** Because all ingested findings are Critical/High severity, **every auto-fix PR requires mandatory human review** before merge. The agent never auto-merges.

### 2.4 Concurrency Model

- **Framework:** Python 3.11+ `asyncio` with task queues for parallel repository processing
- **Queue Backend:** Redis (production) or in-memory queue (development), configurable
- **State Store:** Redis for finding state tracking and inter-loop communication
- **Concurrency Guarantee:** Each finding is processed by at most one loop at a time (dequeue-process-requeue pattern)

---

## 3. Technology Integration Strategy

### 3.1 Recommended Template & Framework Integration

This section details how each recommended GitHub template and framework will be integrated into CodeSentinel's architecture, rather than used as-is.

#### `vercel-labs/coding-agent-template` → Orchestration Layer

**Role:** Provides the foundational patterns for agent orchestration, sandbox execution, and automated branch naming.

**Integration approach:**
- **Adopt:** Branch naming conventions (`fix/<source>-<finding_id>`), sandbox execution model (ephemeral repo clones with cleanup), and agent configuration patterns
- **Adapt:** Replace Vercel-specific infrastructure with our Kubernetes-based deployment and Vault-backed secret management
- **Extend:** Add our six-loop architecture on top of the template's single-agent model, with internal queue routing

#### `qodo-ai/pr-agent` → PR Workflow Layer

**Role:** Provides battle-tested patterns for PR documentation, review interaction, and feedback loop management.

**Integration approach:**
- **Adopt:** PR description template structure (summary, risk level, validation results), label taxonomy, and comment parsing patterns
- **Adapt:** Replace pr-agent's standalone PR review model with our Loop 5 (PR Automation) and Loop 6 (Feedback Monitor) architecture
- **Extend:** Add intent classification (APPROVE/REJECT/CHANGE_REQUEST) using LLM, max-revision limits (3 cycles), and escalation logic

#### `nhomyk/AgenticQA` → Compliance & Validation Patterns

**Role:** Provides enterprise compliance validation patterns and quality assurance workflows.

**Integration approach:**
- **Adopt:** Validation pipeline patterns (multi-stage: syntax → build → compliance), audit event structures
- **Adapt:** Integrate compliance checks into our Loop 4 (LLM Fix Generator) validation stage
- **Extend:** Add Safe-to-Fix policy evaluation as a compliance gate before remediation

#### `gabrielviegas/trivy-sonar-converter` & `mendhak/trivy-template-output-to-sonarqube` → Report Normalization

**Role:** Provides proven patterns for converting between scan tool report formats.

**Integration approach:**
- **Adopt:** Field mapping logic between Trivy and SonarQube schemas as reference for our own normalizers
- **Adapt:** Build our own JSON normalizers targeting our internal schema (Section 2.2) rather than converting between tool formats
- **Note:** All ingestion is JSON-only per requirements — no PDF/Excel/CSV/SARIF/CycloneDX parsers needed

#### `pvojtechovsky/sonarqube-repair` → Remediation Logic Patterns

**Role:** Provides early remediation logic patterns for SonarQube rules (Java-focused).

**Integration approach:**
- **Adopt:** Rule-to-remediation mapping patterns for Bug and Vulnerability types
- **Adapt:** Extend from Java-only to multi-language (Python, JavaScript, TypeScript, Go) and from deterministic transforms to LLM-augmented generation for Blocker/Critical severity fixes
- **Extend:** Add our per-rule prompt templates and few-shot examples for security-focused LLM-based fixing

### 3.2 MCP Server Integration

**MCP (Model Context Protocol)** servers provide secure, streamlined VCS operations without exposing raw credentials to the agent.

| MCP Server | Operations | Fallback |
|------------|-----------|----------|
| **GitHub MCP Server** | `clone`, `checkout_branch`, `commit_files`, `push_branch`, `create_pr`, `get_comments` | GitHub REST API via GitHub App |
| **Azure DevOps MCP Server** | Same operations for Azure Repos | Azure DevOps REST API via PAT |
| **Git Commit, Push & PR Skill** | End-to-end Git workflow automation as a single MCP tool call | Direct GitPython + REST API |

**Key design decision:** The VCS client layer implements a **factory pattern** that returns the appropriate client (MCP or REST API) based on repo URL and available configuration. If MCP is unreachable, the system seamlessly falls back to REST API mode. This is critical because the Azure Repos MCP server spec may not be finalized by Phase 1 (Risk R-002).

### 3.3 LLM Provider Strategy

The agent supports a pluggable LLM backend via an abstract interface, allowing enterprise teams to select their preferred provider.

| Provider | Model | Primary Use Case | Configuration |
|----------|-------|-----------------|---------------|
| **OpenAI** | GPT-4o | Primary code reasoning engine | `CODESENTINEL_LLM_PROVIDER=openai` |
| **Anthropic** | Claude 3.5 Sonnet | Alternative provider, strong at code tasks | `CODESENTINEL_LLM_PROVIDER=anthropic` |
| **GitHub Copilot** | Auto-mode | Optional, requires Copilot Enterprise license | `CODESENTINEL_LLM_PROVIDER=copilot` |
| **Azure OpenAI** | GPT-4o (private endpoint) | On-prem / data sovereignty requirement | `CODESENTINEL_LLM_PROVIDER=azure_openai` |
| **Ollama** | Llama-3 | Fully on-prem inference (no data leaves network) | `CODESENTINEL_LLM_PROVIDER=ollama` |

**Temperature strategy for self-correction:** Attempt 1 = `0.0` (deterministic), Attempt 2 = `0.1` (slight variation), Attempt 3 = `0.2` (more exploration).

---

## 4. Development Phases

### 4.1 Phase Overview & Timeline

| Phase | Name | Duration | Dates | Milestone | Key Deliverable |
|-------|------|----------|-------|-----------|-----------------|
| 0 | Project Setup & Planning | 2 weeks | Mar 16 – Mar 27 | M1 | Approved plan, environments, schemas |
| 1 | Core Agent & VCS Integration | 4 weeks | Mar 30 – Apr 24 | M2 | Agent creates branch → commit → PR on test repo |
| 2 | SonarQube Integration | 3 weeks | Apr 27 – May 15 | M3 | End-to-end: Sonar Bug/Vuln JSON → fix → lint → PR |
| 3 | Mend (SCA) Integration | 2 weeks | May 18 – May 29 | M4 | Mend JSON → dep bump PR opened & validated |
| 4 | Trivy Integration | 2 weeks | Jun 01 – Jun 12 | M5 | Trivy JSON → container/pkg fix PR opened |
| 5 | Remediation Engine Enhancement | 4 weeks | Jun 15 – Jul 10 | M6 | Self-correction loop, CI hook, dry-run mode |
| 6 | Testing, Deployment & Documentation | 3 weeks | Jul 13 – Aug 01 | M7 | Security audit passed, k8s deployed, docs published |
| **Total** | | **20 weeks** | | | |

> **📌 Timeline reduction:** JSON-only ingestion eliminates PDF, Excel, CSV, SARIF, and CycloneDX parser development, saving ~3 weeks (Mend reduced from 4→2 weeks, Trivy from 3→2 weeks).

### 4.2 Phase 0 — Project Setup & Planning (2 weeks)

**Objectives:** Reconcile all requirements, provision environments, define schemas, get sign-off.

**Critical tasks:**
1. **Requirements Reconciliation** — Resolve contradictions across 5 source documents (Copilot licensing discrepancy, Azure Repos MCP spec, on-prem LLM decision)
2. **Development Environment Setup** — Python 3.11+ venv, Docker Compose, Vault dev mode, pre-commit hooks (`black`, `isort`, `flake8`, `mypy`)
3. **Monorepo Structure Establishment:**
   ```
   codesentinel/
   ├── agents/          # Agent loop implementations (Loops 1-6)
   ├── parsers/         # Tool-specific JSON parsers (sonar/, mend/, trivy/)
   ├── vcs/             # VCS clients (github, gitlab, azure, mcp_client)
   ├── llm/             # LLM clients, prompt templates, prompt builder
   ├── validation/      # Linter runner, CI hook
   ├── config/          # Config schemas, loaders, safe-rule lists
   ├── audit/           # Audit log writer
   ├── utils/           # Rate limiter, helpers
   ├── tests/           # Unit, integration, e2e tests
   │   ├── unit/
   │   ├── integration/
   │   ├── e2e/
   │   └── fixtures/    # Sample JSON scan report files
   ├── docs/            # User & API documentation
   └── infra/           # Docker, Helm, k8s manifests
   ```
4. **Sandbox Credentials Provisioning** — SonarQube, Mend, Trivy, GitHub App, GitLab Bot, Azure DevOps PAT — all stored in Vault
5. **Internal Schema Definition** — Finalize finding schema, audit event schema, PR template schema, JSON Schema validation utility

**Exit Criteria (M1):** All requirements signed off, environments provisioned, `make dev-setup` runs cleanly.

### 4.3 Phase 1 — Core Agent & VCS Integration (4 weeks)

**Objectives:** Build the foundational framework that all subsequent phases depend on.

**Critical tasks and their agentic loop mapping:**

| Task | Description | Loop | File |
|------|-------------|------|------|
| 1.1 | Agent Core Framework (LangChain base, logging, config, queue, shutdown) | All | `agents/core.py` |
| 1.2 | VCS Authentication (GitHub App JWT, GitLab Bot Token, Azure PAT) | 5 | `vcs/auth.py` |
| 1.3 | MCP Integration for Azure Repos & GitHub | 5 | `vcs/mcp_client.py` |
| 1.4 | Git Operations (clone, branch, patch, commit, push, cleanup) | 5 | `vcs/git_ops.py` |
| 1.5 | PR Creation & Management (description template, labels, reviewers, status) | 5 | `vcs/pr_manager.py` |
| 1.6 | PRMonitor — PR Comment Feedback Loop (background poll, intent classify, auto-refine/escalate) | 6 | `agents/pr_monitor.py` |
| 1.7 | Audit Logging System (structured JSON Lines, event types, append-only) | All | `audit/logger.py` |
| 1.8 | M2 Integration Test (dummy finding → branch → commit → PR → audit verify) | — | `tests/e2e/` |

**Key design decision — Human-in-the-Loop Feedback via PRMonitor:**

The **PRMonitor** (Loop 6) runs continuously in the background, polling all open auto-fix PRs for new reviewer comments. The reviewer experience is simple and natural:

> **How it works for reviewers:**
> You can comment directly on the PR. If you ask for changes (e.g., *"Change this to a list comprehension"*), the PRMonitor (running in the background) will detect your comment and attempt to refine the fix automatically.

Under the hood, the PRMonitor uses the LLM to classify each new comment's intent:

| Comment Intent | Example | PRMonitor Action |
|---------------|---------|-----------------|
| `APPROVE` | "LGTM", "Looks good" | Log approval, stop monitoring PR |
| `REJECT` | "This is wrong, don't change this" | Close branch, log `HUMAN_DECLINED`, stop monitoring |
| `CHANGE_REQUEST` | "Change this to a list comprehension" | Extract instruction → re-trigger Loop 4 (LLM Fix Generator) with reviewer's feedback appended to the prompt → push amended commit → reply to comment |

After **3 revision cycles**, the PRMonitor posts a comment — *"Max revisions reached. Please resolve manually."* — sets the finding status to `ESCALATED`, and stops monitoring.

**Exit Criteria (M2):** Agent can create branch, commit, and open a documented PR on a test repo.

### 4.4 Phase 2 — SonarQube Integration (3 weeks)

**Objectives:** First real end-to-end auto-fix PR from SonarQube, targeting **Bugs and Vulnerabilities at Blocker/Critical severity**.

**Ingestion scope:**
- **Types:** `BUG`, `VULNERABILITY` only (Code Smells excluded)
- **Severities:** `BLOCKER`, `CRITICAL` only
- **Format:** JSON (API response + file-based JSON import)

**Critical tasks:**

| Task | Description | Loop | File |
|------|-------------|------|------|
| 2.1 | SonarQube API Client (httpx, token auth, pagination, rate limiting, `types=BUG,VULNERABILITY`, `severities=BLOCKER,CRITICAL`) | 1 | `parsers/sonarqube/api_client.py` |
| 2.2 | SonarQube JSON Parser (API response format + manual JSON file input) | 1 | `parsers/sonarqube/parser.py` |
| 2.3 | Issue Mapping & Risk Classification (Bug/Vulnerability, safe-rule list for known fixable patterns) | 2 | `parsers/sonarqube/mapper.py` |
| 2.4 | LLM Remediation Prompts (system prompt, per-category variants for bugs/vulnerabilities, ±50 line context) | 4 | `llm/prompts/sonarqube.py` |
| 2.5 | End-to-End Integration Test (bug fix + vulnerability fix PRs opened) | — | `tests/e2e/` |

**Prompt engineering approach for SonarQube (Bug/Vulnerability focus):**
- System prompt establishes the agent as a "senior security engineer performing critical bug and vulnerability fixes"
- Output contract: produce ONLY a valid unified diff — no explanation, no markdown fences
- Per-category variants: null pointer / resource leak bugs (add null checks, try-finally), security vulnerabilities (input validation, secure defaults, hardcoded credential removal)
- Context injection: ±50 lines of surrounding code + all import statements
- **Safety emphasis:** Prompt explicitly instructs the LLM to make the *minimal* change needed and to flag any fix that might alter business logic

**Exit Criteria (M3):** At least 2 Bug fixes and 1 Vulnerability fix completed end-to-end (ingest → classify → context → LLM → lint pass → PR opened).

### 4.5 Phase 3 — Mend (SCA) Integration (2 weeks)

> **📌 Simplified scope.** JSON-only ingestion eliminates PDF, Excel, and CSV parser development. Phase reduced from 4 weeks to 2 weeks.

**Ingestion scope:**
- **Severities:** `CRITICAL`, `HIGH` only
- **Format:** JSON only (API response + manual JSON file input)

**Critical tasks:**

| Task | Description | Complexity | File |
|------|-------------|-----------|------|
| 3.1 | Mend API Client (Platform API 3.0, auth, pagination) | Medium | `parsers/mend/api_client.py` |
| 3.2 | Mend JSON Parser (API response + manual JSON file input, severity filtering) | Low | `parsers/mend/json_parser.py` |
| 3.3 | Vulnerability Risk Mapping (has FixedVersion + direct dep → LOW risk, else HIGH) | Low | `parsers/mend/mapper.py` |
| 3.4 | LLM Remediation Prompts (per-manifest: requirements.txt, package.json, pom.xml, go.mod) | High | `llm/prompts/mend.py` |
| 3.5 | End-to-End Integration Test (2+ manifest types, Critical/High findings processed) | — | `tests/e2e/` |

**Key design decision — Manifest-aware prompts:**
The agent detects the package manifest type in the repo and uses per-manifest prompt templates. For `requirements.txt`, it's a simple version pin change; for `package.json`, it respects semver constraints (`^`, `~`); for `pom.xml`, it navigates the XML `<dependency>` block hierarchy.

**Exit Criteria (M4):** At least 2 manifest types fixed, Critical and High JSON findings ingested and processed.

### 4.6 Phase 4 — Trivy Integration (2 weeks)

> **📌 Simplified scope.** JSON-only ingestion eliminates SARIF and CycloneDX parser development. Phase reduced from 3 weeks to 2 weeks.

**Ingestion scope:**
- **Severities:** `CRITICAL`, `HIGH` only
- **Format:** JSON only (API response + manual JSON file input)

**Critical tasks:**

| Task | Description | File |
|------|-------------|------|
| 4.1 | Trivy API Client (client-server mode, Operator webhook, scan polling) | `parsers/trivy/api_client.py` |
| 4.2 | Trivy JSON Parser (Results → Vulnerabilities array, severity filtering for CRITICAL/HIGH, manual JSON input) | `parsers/trivy/json_parser.py` |
| 4.3 | Risk Classification (FixedVersion + severity → risk, target type routing) | `parsers/trivy/mapper.py` |
| 4.4 | LLM Remediation Prompts (Dockerfile: base image bump, apt-get pin, yum pin) | `llm/prompts/trivy.py` |
| 4.5 | End-to-End Integration Test (base image bump + package pin PR) | `tests/e2e/` |

**Key design decision — Target type routing:**
Trivy findings with `target_type: code` are routed to the SonarQube-style fix logic (code-level patches), while `target_type: container` or `os-pkgs` findings use Dockerfile-specific prompts. This prevents the agent from attempting to patch source code when the fix belongs in a Dockerfile.

**Exit Criteria (M5):** At least one Dockerfile base image bump and one package pin PR opened successfully, for CRITICAL or HIGH severity CVEs.

### 4.7 Phase 5 — Remediation Engine Enhancement (4 weeks)

**Objectives:** Harden the entire system — advanced prompts, validation, self-correction, reliability.

**Critical tasks:**

| Task | Description | File |
|------|-------------|------|
| 5.1 | Enhanced Risk Assessment (formal policy rules engine, per-repo overrides) | `agents/risk_classifier.py` |
| 5.2 | Context Retrieval Enhancement (configurable window, imports, manifest, token limit) | `agents/context_retriever.py` |
| 5.3 | Advanced Prompt Engineering (few-shot, chain-of-thought, output enforcement, A/B test) | `llm/prompt_builder.py` |
| 5.4 | LLM Self-Correction Loop (retry ×3, linter error feedback, temperature escalation) | `agents/fix_generator.py` |
| 5.5 | Syntax Validation Module (multi-language linter registry: flake8/eslint/checkstyle/gofmt/hadolint) | `validation/linter_runner.py` |
| 5.6 | Optional CI Build Verification Hook (GitHub Actions / GitLab CI trigger + polling) | `validation/ci_hook.py` |
| 5.7 | Dry-Run / Report-Only Mode (`--dry-run` flag, JSON + Markdown report output) | — |
| 5.8 | Rate Limiting & Reliability (token bucket per API, exponential backoff, circuit breaker) | `utils/rate_limiter.py` |

**Self-correction loop (Loop 4 core mechanism):**
```
FOR attempt IN [1, 2, 3]:
  prompt = build_prompt(finding, attempt, previous_error)
  diff = llm.call(prompt, temperature = 0.0 + (attempt-1) * 0.1)
  IF parse_diff(diff) fails → previous_error = "Invalid diff format" → CONTINUE
  apply_diff(repo_clone, diff)
  lint_result = linter.run(file, language)
  IF lint_result.passed → finding.status = FIX_VALIDATED → STOP (success)
  ELSE → previous_error = lint_result.errors → revert_diff → CONTINUE
finding.status = AUTO_FIX_FAILED  (after 3 failures)
```

**Exit Criteria (M6):** Self-correction loop working, CI hook tested, dry-run mode live.

### 4.8 Phase 6 — Testing, Deployment & Documentation (3 weeks)

**Critical tasks:**

| Task | Description |
|------|-------------|
| 6.1 | Unit Test Suite (≥80% line coverage, 100% branch coverage on risk classifier + auth) |
| 6.2 | Integration Test Suite (live sandbox calls per tool + VCS) |
| 6.3 | End-to-End Test Suite (7 scenarios covering all fix types, self-correction, dry-run, feedback loop) |
| 6.4 | Security Audit & Penetration Testing (credential audit, prompt injection, data leakage, OWASP) |
| 6.5 | Docker & Kubernetes Deployment (multi-stage Dockerfile, Helm chart, CronJob, health checks) |
| 6.6 | Monitoring & Alerting (Prometheus metrics endpoint, Grafana dashboard, alerting rules) |
| 6.7 | User Documentation (setup guide, config reference, integrations guide, operator guide, troubleshooting) |
| 6.8 | Training Materials (developer onboarding deck, security team overview, demo recording, FAQ) |

**E2E Test Scenarios:**
1. SonarQube Critical Bug (null pointer) → fix → lint pass → PR opened (Python)
2. SonarQube Blocker Vulnerability (hardcoded secret) → fix → lint pass → PR opened
3. Mend Critical dependency vulnerability (JSON) → bump `requirements.txt` → PR opened
4. Trivy HIGH container CVE (JSON) → Dockerfile base image bump → PR opened
5. LLM fix fails linting → self-correction succeeds on retry 2
6. Dry-run mode → report generated, no PR created
7. PR reviewer requests change → agent amends and pushes
8. HIGH risk finding (no fix version / complex logic) → flagged, no fix generated, audit log entry written

**Exit Criteria (M7):** Security audit passed, Kubernetes running 48h without incident, all docs published, stakeholder sign-off.

---

## 5. Modularity & Extensibility Design

### 5.1 Plugin Architecture for Tool Integration

Adding a new scanning tool (e.g., Snyk, Checkmarx) requires implementing only three components:

```
codesentinel/parsers/<new_tool>/
├── api_client.py    # Implements ToolAPIClient interface
├── parser.py        # Implements ToolParser interface → normalized findings
└── mapper.py        # Implements RiskMapper interface → risk classification
```

**No changes required** to agents, LLM prompts, VCS operations, or validation logic — because all downstream components operate on the normalized finding schema.

### 5.2 Interface Contracts

| Interface | Methods | Implemented By |
|-----------|---------|----------------|
| `ToolAPIClient` | `authenticate()`, `fetch_findings()`, `handle_pagination()` | SonarQube, Mend, Trivy API clients |
| `ToolParser` | `parse(input) → List[Finding]`, `validate_schema(input)` | JSON parsers (SonarQube, Mend, Trivy) |
| `RiskMapper` | `classify(finding) → RiskLevel`, `load_policy(source, repo)` | Per-tool mappers + enhanced policy engine |
| `LLMProvider` | `call(prompt, temperature) → str`, `classify_intent(text) → Intent` | OpenAI, Anthropic, Copilot, AzureOpenAI, Ollama adapters |
| `VCSClient` | `clone()`, `create_branch()`, `commit()`, `push()`, `create_pr()`, `get_comments()` | GitHub, GitLab, Azure (REST or MCP) |
| `LinterRunner` | `run(file_path, language) → LintResult` | flake8, eslint, checkstyle, gofmt, hadolint wrappers |

### 5.3 Configuration Extensibility

All operator-facing configuration is externalized as YAML, not code:

- **Safe-rule list** — Add new SonarQube Bug/Vulnerability rules to auto-fix without redeployment
- **Severity filter** — Configure which severity levels to ingest per tool
- **Linter registry** — Add new linters for new languages
- **CI hook config** — Per-repo `.codesentinel.yml` for CI provider, workflow, timeout
- **LLM provider** — Switch via environment variable

---

## 6. Scalability Architecture

### 6.1 Horizontal Scaling

```
                    ┌──────────────────┐
                    │  Load Balancer   │
                    │  (Webhook/API)   │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │ Agent Pod 1 │  │ Agent Pod 2 │  │ Agent Pod N │
     │ (Loops 1-6) │  │ (Loops 1-6) │  │ (Loops 1-6) │
     └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
                    ┌────────┴─────────┐
                    │  Redis Queue     │
                    │  + State Store   │
                    └──────────────────┘
```

- **Kubernetes HPA** scales agent pods based on queue depth
- Each pod runs all 6 loops, consuming from the shared Redis queue
- Finding-level locking (Redis) prevents duplicate processing

### 6.2 Rate Limit Awareness

| API | Strategy | Default Limit |
|-----|----------|---------------|
| SonarQube | Token bucket, configurable | 10 req/s |
| Mend | Token bucket, configurable | 5 req/s |
| GitHub | `X-RateLimit-Remaining` header tracking | API-defined |
| GitLab | `RateLimit-Remaining` header tracking | API-defined |
| LLM APIs | `x-ratelimit-remaining-requests` header | Provider-defined |

**Backoff formula:** `sleep(min(cap, base × 2^attempt) × random())`  
**Circuit breaker:** After 5 consecutive failures → pause that API for 5 minutes.

---

## 7. Security & Compliance Architecture

### 7.1 Credential Management

```
┌───────────────┐         ┌──────────────────────────┐
│  Agent Pod    │ ──────▶ │  HashiCorp Vault         │
│               │  mTLS   │  (or AWS Secrets Manager) │
│  - No local   │         │                          │
│    secrets    │         │  codesentinel/secrets/    │
│  - Runtime    │         │  ├── sonarqube_token      │
│    fetch only │         │  ├── mend_user_key        │
│               │         │  ├── trivy_api_key        │
│               │         │  ├── github_app_key       │
│               │         │  ├── gitlab_bot_token     │
│               │         │  └── azure_devops_pat     │
└───────────────┘         └──────────────────────────┘
```

**Zero-secret guarantee:**
- No credentials in code, config files, environment variables on dev machines, logs, or PR descriptions
- Credentials fetched from Vault at runtime with short-lived tokens
- Credential audit at every milestone (M1–M7)

### 7.2 Data Sovereignty

- **On-prem deployment:** Full Kubernetes support with Ollama or Azure OpenAI private endpoint for LLM inference
- **Ephemeral workspaces:** Cloned repositories are deleted after each finding is processed
- **No permanent source code storage:** The agent holds source code only in memory during fix generation
- **LLM prompt sanitization:** PII/PHI scrubbed before LLM invocation; prompt hashes stored (not full prompts) for auditability

### 7.3 Audit Trail Design

Every action emits a structured event to the tamper-proof audit log:

| Event Type | Trigger | Key Fields |
|------------|---------|------------|
| `FINDING_INGESTED` | Loop 1 completes | finding_id, source, repo, count |
| `RISK_CLASSIFIED` | Loop 2 completes | finding_id, risk_level, rule_triggered |
| `CONTEXT_RETRIEVED` | Loop 3 completes | finding_id, context_lines_fetched |
| `FIX_GENERATED` | Loop 4 attempt | finding_id, attempt, prompt_hash |
| `VALIDATION_PASSED` | Linter passes | finding_id, attempt, linter_name |
| `VALIDATION_FAILED` | Linter fails | finding_id, attempt, errors |
| `PR_CREATED` | Loop 5 completes | finding_id, pr_url, branch_name |
| `PR_COMMENT_RECEIVED` | Loop 6 detects comment | finding_id, intent, comment_hash |
| `FIX_AMENDED` | Loop 6 → Loop 4 re-run | finding_id, revision_count |
| `FIX_SKIPPED` | HIGH risk classification | finding_id, reason |
| `FIX_FAILED` | 3 retries exhausted | finding_id, total_attempts |

**Storage:** Append-only JSON Lines file → configurable output to S3, database, or SIEM.

---

## 8. Test-Driven Development Strategy

### 8.1 TDD Workflow (Applied to Every Task)

```
┌─────────────────────────────────────────────────┐
│  1. RED: Write a failing test                   │
│     Define expected behavior before code exists │
│                                                 │
│  2. GREEN: Write minimal code to pass           │
│     Only implement what the test requires       │
│                                                 │
│  3. REFACTOR: Improve without changing behavior │
│     All tests must still pass after refactor    │
└─────────────────────────────────────────────────┘
```

### 8.2 Test Categories & Coverage Targets

| Category | Scope | Target Coverage | Run Frequency |
|----------|-------|-----------------|---------------|
| **Unit Tests** | Individual functions, classes, parsers | ≥80% line, 100% branch on risk classifier + auth | Every commit (pre-push hook) |
| **Integration Tests** | API clients ↔ live sandbox, VCS ↔ test repo | All critical paths | Every PR merge |
| **End-to-End Tests** | Full pipeline: ingest → classify → fix → lint → PR | 8 scenarios (Section 4.8) | Every milestone |

### 8.3 TDD Applied to Key Components

**JSON Parsers (highest TDD value):**
- Fixture files (sample JSON scan reports from SonarQube, Mend, and Trivy) committed to `tests/fixtures/`
- Tests written first for each JSON format, including edge cases (malformed input, empty arrays, missing fields, wrong severity levels filtered out)
- Parser code then implemented to pass all fixture tests

**Risk Classifier (100% branch coverage required):**
- Tests enumerate every combination of `(source, type, severity, rule_id, has_fix_version)` → expected risk level
- Policy override tests: per-repo `.codesentinel.yml` adds/removes rules from safe list

**LLM Prompts (mocked LLM responses):**
- Tests validate prompt structure: correct system prompt, context injection, output format contract
- Tests validate diff parsing: given a known LLM response, verify the diff is correctly extracted and applied

**VCS Operations (test repo fixtures):**
- Tests use an in-memory Git fixture or test repo
- Verify: branch created, diff applied, commit message structured correctly, PR opened with correct labels

### 8.4 Test Infrastructure

- **Framework:** `pytest` with `pytest-asyncio`, `pytest-cov`, `pytest-httpx` (HTTP mocking)
- **Fixtures:** Sample scan reports, test repo with known violations, mock LLM responses
- **CI Integration:** GitHub Actions runs full test suite on every PR; coverage report published as PR comment
- **Pre-commit hooks:** `black`, `isort`, `flake8`, `mypy` — enforce code quality before tests even run

---

## 9. Risk Management & Contingency

| ID | Risk | Probability | Impact | Mitigation Strategy |
|----|------|:-----------:|:------:|---------------------|
| R-001 | GitHub Copilot enterprise licensing not approved | Medium | Low | Copilot is optional; GPT-4o/Claude are primary. LLM config fully decoupled from agent logic. |
| R-002 | Azure Repos MCP server spec not finalized before Phase 1 | High | Medium | Implement direct Azure DevOps REST API first; add MCP layer as enhancement in Phase 5. VCS client factory enables seamless swap. |
| R-003 | LLM generates unsafe fixes for Critical/High severity bugs | High | High | Mandatory human review on all PRs; agent never auto-merges. Prompt engineering emphasizes minimal changes. Fix suggestion mode for complex findings. |
| R-004 | LLM generates incorrect diffs for complex manifests (pom.xml) | Medium | Medium | Extensive few-shot examples; add deterministic pom.xml parser as fallback to LLM for version-only changes. |
| R-005 | On-prem LLM inference required for data sovereignty | Medium | High | Evaluate Ollama (Llama-3) or Azure OpenAI private endpoint. Decision in Phase 0 (TASK-0.1). LLM interface already supports pluggable providers. |
| R-006 | Security audit uncovers critical issues in Phase 6 | Low | High | Rolling security reviews from Phase 1: credential audit at every milestone. |
| R-007 | False sense of security from auto-generated fixes | Medium | High | Clear PR labeling (`auto-fix`, `requires-security-review`), mandatory reviewer assignment, and audit trail showing full LLM reasoning. |
| R-008 | No slack between phases — any slip cascades | Medium | Medium | 3-day buffer at end of Phase 2. Track velocity weekly from Phase 1. Reduced timeline (20 weeks) provides earlier completion margin. |

---

## 10. Success Criteria & Definition of Done

### 10.1 Per-Task Definition of Done

- [ ] Code written, peer-reviewed, and merged to main branch
- [ ] Unit tests written and passing (≥80% coverage for new code)
- [ ] No secrets in code, logs, or PR descriptions
- [ ] Audit log events emitted correctly for all agent actions
- [ ] Documentation updated if any public interface changed

### 10.2 Per-Phase Definition of Done

- [ ] All tasks in phase completed and merged
- [ ] Integration test for phase passing against live sandbox
- [ ] Milestone demo conducted and screen-recorded
- [ ] Phase retrospective completed; risk register updated

### 10.3 Project Complete (M7 — Aug 01, 2026)

- [ ] All tasks completed across 7 phases
- [ ] Unit test coverage ≥80% overall
- [ ] All 8 E2E scenarios passing
- [ ] Security audit passed with no critical findings
- [ ] Kubernetes deployment running in staging ≥48 hours without incident
- [ ] All documentation published (setup, config, integrations, operator, troubleshooting, API)
- [ ] Training materials delivered (developer deck, security overview, demo recording, FAQ)
- [ ] Stakeholder sign-off obtained

### 10.4 Key Metrics (Post-Deployment)

| Metric | Target | Measurement |
|--------|--------|-------------|
| First-pass fix success rate | ≥70% | Fixes that pass linting on first LLM attempt |
| Overall fix success rate (with retries) | ≥90% | Fixes that pass after up to 3 attempts |
| PR merge rate | ≥80% | Auto-fix PRs merged by human reviewers |
| Mean time to PR | <5 minutes | From finding ingestion to PR opened |
| False positive rate | <5% | Fixes rejected as incorrect by reviewers |

---

*This strategy document, once approved, will be decomposed into executable Gemini 3 Flash tasks following the TDD methodology outlined in Section 8.*

---

**Document generated:** 2026-03-15  
**Source:** CodeSentinel Documentation Bundle — Enterprise Requirements, SRS, Project Plan, Milestones, Presentation, Implementation Plan, Recommended Frameworks (all validated)
