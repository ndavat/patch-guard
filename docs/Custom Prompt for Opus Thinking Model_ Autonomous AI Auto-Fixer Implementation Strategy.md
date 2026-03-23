## Custom Prompt for Opus Thinking Model: Autonomous AI Auto-Fixer Implementation Strategy

**Goal:** Develop a comprehensive implementation strategy for the **Autonomous AI Auto-Fixer** agent, considering all specified enterprise-grade requirements, recommended technologies, and a Test-Driven Development (TDD) approach.

**Project Context:**

The Autonomous AI Auto-Fixer is an enterprise-grade AI agent designed to automate the remediation of low-risk technical debt and security vulnerabilities. It integrates with static analysis and security scanning tools (SonarQube, Mend, Trivy) to identify issues and generate verified code fixes, significantly reducing developer burden and accelerating Pull Request (PR) cycles.

**Key Requirements & Features:**

1.  **Multi-Source Ingestion:**
    *   **SonarQube:** REST API (`api/issues/search`) and JSON (GitLab SAST or Sonar Export), including **manual JSON input**.
    *   **Mend (SCA):** Platform API 3.0, PDF, Excel (.xlsx), CSV reports, and **manual JSON input**.
    *   **Trivy:** Operator/Server API, JSON, SARIF, or CycloneDX, including **manual JSON input**.
2.  **Autonomous Remediation Engine (ARE):**
    *   **Risk Classification:** Evaluate findings against a "Safe-to-Fix" policy; flag "High Risk" for manual intervention.
    *   **Context-Aware Code Generation:** Retrieve relevant source code (50+ lines context) before LLM invocation.
    *   **Prompt Engineering:** Employ advanced techniques to optimize LLM output for accuracy, context, and coding standards.
    *   **LLM Options:** Support for configurable LLMs, including **GitHub Copilot (in auto-mode)**, GPT-4o, or Claude 3.5 Sonnet.
    *   **Remediation Logic:** Apply standard refactoring for code smells, dependency version increments for vulnerabilities, and targeted code changes for security patches.
3.  **Verification & Validation:**
    *   **Syntax Validation:** Run language-specific linters on modified files.
    *   **Build Verification (Optional):** Trigger "Pre-check" builds in CI environments.
    *   **LLM Self-Correction:** Iterative refinement of fixes based on validation failures (max 3 retries).
4.  **Pull Request Workflow:**
    *   **Branch Management:** Create unique branches for fixes.
    *   **VCS Integration:** Leverage **MCP for Azure Repos and GitHub Repositories** for seamless VCS operations (branch checkout, commit, push, PR creation).
    *   **PR Documentation:** Structured descriptions with summary, source ID, risk level, and validation results.
    *   **Human-in-the-Loop:** Monitor PR comments for feedback and agent-driven updates.
5.  **Non-Functional Requirements:** Security (credential isolation, data sovereignty, auditability), Scalability (parallel execution, rate limit awareness).

**Recommended Technologies & Templates:**

*   **Core Agent Frameworks:**
    *   `vercel-labs/coding-agent-template`: For orchestration, sandbox execution, and automated branch naming.
    *   `qodo-ai/pr-agent`: For comprehensive PR workflow, review, and feedback loop management.
    *   `nhomyk/AgenticQA`: For enterprise compliance and validation patterns.
*   **Specialized Tool Integrations:**
    *   `gabrielviegas/trivy-sonar-converter` & `mendhak/trivy-template-output-to-sonarqube`: For report conversion and simplified JSON input.
    *   `pvojtechovsky/sonarqube-repair`: For early remediation logic patterns.
*   **MCP Servers:**
    *   `GitHub MCP Server` & `Azure DevOps MCP Server`: For secure and streamlined VCS operations.
    *   `Git Commit, Push & PR Skill`: For end-to-end Git workflow automation.

**Task for Opus:**

Based on the above context, provide a detailed, high-level implementation strategy for the Autonomous AI Auto-Fixer. The strategy should outline the architectural approach, key development phases, and how the recommended technologies will be integrated. Emphasize modularity, scalability, security, and the adoption of a Test-Driven Development (TDD) methodology throughout the development lifecycle. Once this strategy is approved, it will be broken down into executable tasks for Gemini 3 Flash.

**Expected Output:** A structured implementation strategy document.
