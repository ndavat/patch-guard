# Recommended GitHub Templates and Frameworks for Autonomous AI Auto-Fixer

Based on the research of existing open-source solutions and enterprise-grade requirements, the following templates and frameworks are recommended to kickstart the development of the **Autonomous AI Auto-Fixer**.

## 1. Core Agent Frameworks

| Template / Framework | Key Features | Best For |
| :--- | :--- | :--- |
| **[vercel-labs/coding-agent-template](https://github.com/vercel-labs/coding-agent-template)** | Multi-agent support, Vercel Sandbox integration, automated branch naming, and support for multiple LLMs (Claude, OpenAI, Gemini). | **Rapid Prototyping** of the core orchestration and sandbox execution environment. |
| **[qodo-ai/pr-agent](https://github.com/qodo-ai/pr-agent)** | Comprehensive PR review, improvement, and feedback loop management. Supports GitHub, GitLab, Bitbucket, and Azure DevOps. | **PR Workflow & Feedback Loop** logic. This is the industry standard for AI-human collaboration in PRs. |
| **[nhomyk/AgenticQA](https://github.com/nhomyk/AgenticQA)** | Enterprise-grade QA and compliance platform with specialized agents and self-healing CI/CD. | **Enterprise Compliance & Validation** patterns, specifically for ensuring fixes meet organizational standards. |

## 2. Specialized Tool Integrations

| Project | Integration Target | Utility |
| :--- | :--- | :--- |
| **[gabrielviegas/trivy-sonar-converter](https://github.com/gabrielviegas/trivy-sonar-converter)** | Trivy & SonarQube | Provides a pattern for converting Trivy reports into SonarQube-compatible formats, useful for unified ingestion. |
| **[mendhak/trivy-template-output-to-sonarqube](https://github.com/mendhak/trivy-template-output-to-sonarqube)** | Trivy & SonarQube | A custom Trivy template for generating SonarQube-friendly output, simplifying the manual JSON input requirement. |
| **[pvojtechovsky/sonarqube-repair](https://github.com/pvojtechovsky/sonarqube-repair)** | SonarQube | An initial draft system specifically for repairing SonarQube violations, providing early remediation logic. |

## 3. MCP Servers for VCS & Infrastructure

To meet the requirement for **MCP integration with Azure Repos and GitHub**, the following servers should be utilized:

*   **[GitHub MCP Server](https://github.com/github/github-mcp-server):** Official server for repository management, code search, and PR operations on GitHub.
*   **[Azure DevOps MCP Server](https://github.com/microsoft/azure-devops-mcp):** Official Microsoft server for interacting with Azure Repos, work items, and pipelines.
*   **[Git Commit, Push & PR Skill](https://mcpmarket.com/tools/skills/git-commit-push-pr):** A specialized MCP skill designed for the end-to-end automation of Git workflows.

## 4. Recommended Kickstart Strategy

1.  **Orchestration:** Use `coding-agent-template` as the base for the orchestration layer and sandbox execution.
2.  **Remediation Logic:** Incorporate patterns from `sonarqube-repair` and `AgenticQA` for the AI remediation engine.
3.  **PR Management:** Integrate `pr-agent` logic to handle the human-in-the-loop feedback and PR documentation.
4.  **VCS Connectivity:** Configure the `GitHub MCP Server` and `Azure DevOps MCP Server` to handle all repository operations securely.
5.  **Manual Ingestion:** Implement custom parsers (as outlined in the SRS) to ingest JSON files from SonarQube, Mend, and Trivy, using the converters above as reference.
