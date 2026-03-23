# PatchGuard — Project Summary
### Autonomous Security Remediation Agent

> *Turning security scan backlogs into verified Pull Requests — automatically.*

**Version:** 1.0 &nbsp;|&nbsp; **Date:** 2026-03-22 &nbsp;|&nbsp; **Status:** Planning

---

## 1. Problem Statement & Requirements

### 1.1 The Security Debt Crisis

Enterprise development teams today are drowning in security findings. Static analysis tools like **SonarQube**, software composition analysis (SCA) platforms like **Mend**, and container vulnerability scanners like **Trivy** continuously flag hundreds of critical and high-severity issues — SQL injection bugs, known CVEs in third-party dependencies, and vulnerable container base images. Each finding demands analysis, a code fix, validation, and a Pull Request — a repetitive toil cycle that directly competes with feature delivery.

**The result**: critical security vulnerabilities linger in production while developers prioritize sprint commitments. Teams accumulate security debt that grows with every scan cycle, and even when fixes are straightforward (a dependency version bump, a missing input validation check), the manual effort required to remediate, document, and submit for review creates bottlenecks that delay resolution by days or weeks.

### 1.2 Core Requirements

PatchGuard must address these requirements:

| # | Requirement | Description |
|---|------------|-------------|
| R1 | **Multi-Tool Ingestion** | Ingest scan findings from SonarQube, Mend, and Trivy via JSON files or authenticated API access |
| R2 | **Severity-Based Filtering** | Process only high-priority findings: Blocker/Critical (SonarQube Bugs & Vulnerabilities), Critical/High (Mend SCA), Critical/High (Trivy container vulns) |
| R3 | **Risk Classification** | Classify each finding as Low-Risk (auto-fixable) or High-Risk (flag-only) using a configurable Safe-to-Fix policy |
| R4 | **AI-Powered Fix Generation** | Generate verified code patches using LLMs (GPT-4o, Claude 3.5 Sonnet, or similar) with linter validation and self-correction |
| R5 | **Automated PR Workflow** | Create branches, commit fixes, and open fully-documented Pull Requests with finding links, risk justification, and validation evidence |
| R6 | **Mandatory Human Review** | Every auto-fix PR requires human approval — the agent never auto-merges. Reviewer feedback triggers automatic fix amendments |
| R7 | **Enterprise Security** | Zero-secret guarantee (Vault-backed credential management), audit logging, ephemeral workspaces, and LLM prompt sanitization |
| R8 | **Test-Driven Development** | All components built test-first (RED → GREEN → REFACTOR), with ≥80% code coverage enforced at every milestone |

---

## 2. Suggested Approach

### 2.1 Architecture — Six Cooperating Agentic Loops

PatchGuard decomposes the remediation pipeline into **six independently scalable loops**, each with a single responsibility. This modular design ensures failure isolation, independent testing, and plug-in extensibility for new scanning tools.

```
┌──────────────────────────────────────────────────────────────────────┐
│                           PatchGuard                                 │
│                                                                      │
│  Loop 1: Ingestion ──▶ Loop 2: Risk Classifier ──▶ Loop 3: Context  │
│  (SonarQube/Mend/Trivy)  (Safe-to-Fix Policy)      (±50 lines code) │
│                                                                      │
│  Loop 6: Feedback ◀── Loop 5: PR Automation ◀── Loop 4: LLM Fixer  │
│  (PR comment monitor)    (branch/commit/PR)     (prompt → diff → lint)│
│                                                                      │
│  ═══════════════════════════════════════════════════════════════════  │
│  [ Audit Log Store  ·  Findings Queue  ·  State Store (Redis) ]      │
└──────────────────────────────────────────────────────────────────────┘
```

**Why six loops?** (1) Each loop can be developed, tested, and scaled independently. (2) Failure in one loop (e.g., LLM timeout) doesn't cascade. (3) Adding a new scanner (Snyk, Checkmarx) only touches Loop 1 — all downstream logic is tool-agnostic thanks to the Normalized Finding Schema.

### 2.2 Normalized Finding Schema

All incoming scan data — regardless of source — is converted to a single canonical schema before entering the pipeline. This is the key design decision that allows the remediation engine, PR automation, and audit system to be completely tool-agnostic:

| Field | Description | Example |
|-------|------------|---------|
| `finding_id` | Unique identifier | `CVE-2024-38816` |
| `source` | Originating tool | `trivy` |
| `severity` | Normalized severity | `CRITICAL` |
| `file_path` | Affected file | `src/utils/helper.py` |
| `message` | Description of the issue | `Update Spring Boot to 3.3.4` |
| `fix_hint` | Suggested resolution | `FixedVersion: 3.3.4` |
| `status` | Pipeline state | `QUEUED → FIX_VALIDATED → PR_OPEN` |

### 2.3 TDD-First Development Strategy

PatchGuard follows strict Test-Driven Development across all phases:

1. **RED**: Write a failing test that defines the expected behavior
2. **GREEN**: Write the minimal code required to pass the test
3. **REFACTOR**: Improve code design while keeping all tests green

**Test categories and targets:**

| Category | Scope | Coverage Target |
|----------|-------|----------------|
| Unit Tests | Parsers, models, classifiers | ≥80% line coverage |
| Integration Tests | API clients ↔ sandbox, VCS ↔ test repos | All critical paths |
| End-to-End Tests | Full pipeline: ingest → classify → fix → lint → PR | 8 key scenarios |

### 2.4 Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Framework | LangChain / CrewAI |
| LLM | GPT-4o · Claude 3.5 Sonnet (pluggable) |
| VCS | GitHub App · GitLab Bot · Azure Repos MCP |
| Validation | flake8 · eslint · checkstyle · hadolint |
| Testing | pytest · pytest-cov · pytest-asyncio |
| Infrastructure | Docker · Kubernetes · Helm |
| Secrets | HashiCorp Vault |

### 2.5 Human-in-the-Loop: PR Comment Feedback

PatchGuard never auto-merges. Every fix goes through a Pull Request that requires human approval. But the interaction doesn't stop at PR creation — the agent **actively monitors reviewer comments** and responds to feedback automatically.

**How it works for reviewers**: You review the PR as you would any other. If you want changes (e.g., *"Please use a list comprehension instead"* or *"Use Dapper instead of raw ADO.NET"*), simply comment on the PR. The **PRMonitor** (Loop 6), running continuously in the background, detects your comment within minutes and acts on it.

**Under the hood**, the PRMonitor uses the LLM to classify each new comment's intent and takes the appropriate action:

| Reviewer Comment | Detected Intent | PatchGuard Action |
|-----------------|-----------------|-------------------|
| *"LGTM"*, *"Looks good, approved"* | `APPROVE` | Log approval, stop monitoring this PR |
| *"This is wrong, don't change this file"* | `REJECT` | Close the branch, mark finding as `HUMAN_DECLINED`, stop monitoring |
| *"Please use a different naming convention"* | `CHANGE_REQUEST` | Extract the instruction → re-invoke Loop 4 (LLM Fix Generator) with the reviewer's feedback appended to the original prompt → push an amended commit → reply to the comment confirming the update |
| *"Can you also fix the null check on line 55?"* | `CHANGE_REQUEST` | Same flow — the agent treats this as an additional fix instruction and amends accordingly |

**Escalation safeguard**: After **3 revision cycles** on the same PR, the PRMonitor posts a comment — *"Maximum revisions reached. Please resolve manually or provide further guidance."* — sets the finding status to `ESCALATED`, and stops monitoring. This prevents infinite loops and ensures human oversight remains the final authority.

**Example flow**:
```
1. PatchGuard opens PR #42: fix(security): resolve SQL injection in UserController.cs
2. Reviewer comments: "Use parameterized queries with Dapper instead of raw SqlCommand"
3. PRMonitor detects comment → classifies as CHANGE_REQUEST
4. Loop 4 re-generates the fix using Dapper, validates with linter
5. PatchGuard pushes amended commit, replies: "Updated to use Dapper. Please re-review."
6. Reviewer comments: "LGTM"
7. PRMonitor detects APPROVE → logs approval, stops monitoring
```

---

## 3. Use Cases with Examples

### Use Case 1: SonarQube — Critical Vulnerability Auto-Fix

**Scenario**: SonarQube identifies a SQL injection vulnerability (`csharpsquid:S3649`) in a C# application at Blocker severity.

**Input** (SonarQube JSON excerpt):
```json
{
  "issues": [{
    "key": "AZrN_abc123",
    "rule": "csharpsquid:S3649",
    "severity": "CRITICAL",
    "component": "MyProject:Controllers/UserController.cs",
    "line": 42,
    "message": "Make sure this SQL injection is safe here.",
    "type": "VULNERABILITY",
    "status": "OPEN"
  }]
}
```

**Processing by PatchGuard**:
1. **Loop 1 (Ingestion)**: Parses the JSON, filters for `type=VULNERABILITY` + `severity=CRITICAL`, and normalizes to a `Finding` object
2. **Loop 2 (Risk Classifier)**: Evaluates against Safe-to-Fix policy — SQL injection with known pattern match → `LOW` risk (parameterized query replacement is deterministic)
3. **Loop 3 (Context Retriever)**: Fetches `UserController.cs` lines 1–92 (±50 around line 42) plus all `using` statements
4. **Loop 4 (LLM Fix Generator)**: Builds a prompt with the security context, generates a unified diff replacing string concatenation with parameterized query, validates via linter
5. **Loop 5 (PR Automation)**: Creates branch `fix/sonarqube-AZrN_abc123`, commits the diff, opens a PR with a structured description linking to the SonarQube issue
6. **Loop 6 (Feedback Monitor)**: Watches for reviewer comments; if the reviewer says "Use Dapper instead of raw ADO.NET", the agent amends the fix

**Output** (PR Description):
```
## PatchGuard Auto-Fix: SQL Injection (CRITICAL)

**Finding**: csharpsquid:S3649 — SQL injection in UserController.cs:42
**Risk Level**: LOW (deterministic fix: parameterized query replacement)
**Validation**: ✅ Linter passed (attempt 1/3)

### Changes
- Replaced string-concatenated SQL query with parameterized query
- Added SqlParameter objects for user-supplied inputs
```

---

### Use Case 2: Mend (SCA) — Critical Dependency Vulnerability

**Scenario**: Mend identifies a Critical CVE in the `System.Drawing.Common` NuGet package with a known fix version.

**Input** (Mend JSON excerpt):
```json
{
  "alerts": [{
    "vulnerabilityId": "CVE-2024-21312",
    "libraryName": "system.drawing.common.4.7.0.nupkg",
    "severity": "CRITICAL",
    "cvssScore": "9.8",
    "status": "ACTIVE",
    "exploitAvailable": "POC_CODE",
    "topFix": {
      "type": "UPGRADE_VERSION",
      "fixResolution": "Upgrade to version System.Drawing.Common - 8.0.1"
    }
  }]
}
```

**Processing by PatchGuard**:
1. **Loop 1 (Ingestion)**: Parses the Mend alerts JSON, extracts package name (`system.drawing.common`) and version (`4.7.0`) from the `libraryName` field, filters for `severity=CRITICAL`
2. **Loop 2 (Risk Classifier)**: Direct dependency + `FixedVersion` available + `UPGRADE_VERSION` type → `LOW` risk
3. **Loop 3 (Context Retriever)**: Locates `.csproj` file containing the `<PackageReference>` for `System.Drawing.Common`
4. **Loop 4 (LLM Fix Generator)**: Generates a diff updating the version attribute from `4.7.0` to `8.0.1`, validates the XML remains well-formed
5. **Loop 5 (PR Automation)**: Creates branch `fix/mend-CVE-2024-21312`, opens PR with CVE link, CVSS score, and version transition

**Output** (Git Commit Message):
```
fix(security): resolve CVE-2024-21312 in System.Drawing.Common

- CVE-2024-21312: Update System.Drawing.Common to 8.0.1 (CRITICAL, CVSS 9.8)
- Exploit available: POC_CODE — prioritized for immediate remediation

Library updates:
- System.Drawing.Common: v4.7.0 → v8.0.1

Files modified:
- MyProject.csproj
```

---

### Use Case 3: Trivy — Container Base Image Vulnerability

**Scenario**: Trivy scan of a Docker container image reports a Critical CVE in the `curl` package with a known fixed version.

**Input** (Trivy JSON excerpt):
```json
{
  "Results": [{
    "Target": "ubuntu:22.04 (ubuntu 22.04)",
    "Vulnerabilities": [{
      "VulnerabilityID": "CVE-2024-38816",
      "PkgName": "curl",
      "InstalledVersion": "7.81.0-1ubuntu1.15",
      "FixedVersion": "7.81.0-1ubuntu1.16",
      "Severity": "CRITICAL",
      "Title": "curl: HSTS subdomain overwrites parent cache entry",
      "CVSS": { "nvd": { "V3Score": 9.1 } }
    }]
  }]
}
```

**Processing by PatchGuard**:
1. **Loop 1 (Ingestion)**: Parses Trivy JSON from `Results[].Vulnerabilities[]`, filters for `Severity=CRITICAL`, extracts package and version info
2. **Loop 2 (Risk Classifier)**: `FixedVersion` present + OS package (apt-level fix) → `LOW` risk
3. **Loop 3 (Context Retriever)**: Identifies the `Dockerfile` associated with the scanned image (matched via `ArtifactName` or image tag in the scan metadata)
4. **Loop 4 (LLM Fix Generator)**: Generates a Dockerfile diff that either pins `curl` to the fixed version (`apt-get install curl=7.81.0-1ubuntu1.16`) or bumps the base image if a patched base exists. Validates with `hadolint`
5. **Loop 5 (PR Automation)**: Creates branch `fix/trivy-CVE-2024-38816`, opens PR

**Output** (Summary Report):
```markdown
## Security Fixes Applied — 2026-03-22

### Critical Vulnerabilities Fixed
- **CVE-2024-38816**: curl v7.81.0-1ubuntu1.15 → v7.81.0-1ubuntu1.16
  - Fix: Pinned curl version in Dockerfile apt-get install

### Files Modified
- Dockerfile

### Next Steps
- Rebuild container image and re-run Trivy scan to verify
- Deploy to staging for regression testing
```

---

### Use Case Summary: What PatchGuard Does NOT Auto-Fix

PatchGuard's Safe-to-Fix policy deliberately flags the following as **High-Risk** (no auto-fix — human-only):

| Scenario | Reason | PatchGuard Action |
|----------|--------|--------------------|
| Transitive dependency vulnerability requiring cascade changes | Blast radius too large | Fix suggestion only in PR |
| Complex logic bug (race conditions, null pointer in business logic) | Behavioral change risk | Fix suggestion with detailed analysis |
| Authentication/authorization flow changes | Security-critical code path | Flag only — no fix generated |
| CVE with no `FixedVersion` available | No deterministic resolution | Acknowledge & track — flag for manual triage |
| Changes spanning 3+ files or core abstractions | Architectural impact | Flag only — no fix generated |

---

*PatchGuard — Because your codebase deserves a guardian that patches while you ship features.*
