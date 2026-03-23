# PatchGuard

**Autonomous Security Remediation Agent**

PatchGuard ingests security scan findings from SonarQube, Mend, and Trivy, normalizes them into a canonical format, and prepares them for automated remediation through AI-powered code fixes and Pull Request automation.

## Status

✅ **Phase 1-5 Complete**: Parser foundation implemented with full TDD coverage

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=patchguard --cov-report=term-missing
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        PatchGuard                           │
│                                                             │
│  Ingestion → Risk Classifier → Context → LLM Fixer → PR    │
│  (Phase 1-5)   (Future)        (Future)   (Future)  (Future)│
└─────────────────────────────────────────────────────────────┘
```

## Features

### ✅ Implemented (Phase 1-5)

- **Multi-Tool Ingestion**: Parse JSON from SonarQube, Mend, and Trivy
- **Normalized Schema**: Convert all findings to canonical `Finding` format
- **Severity Filtering**: Tool-specific severity thresholds
- **Extensible Design**: Abstract base class for adding new scanners
- **100% TDD Coverage**: 61 test cases, all written before implementation

### 🚧 Planned (Phase 6+)

- Risk classification (Safe-to-Fix policy)
- Context retrieval (±50 lines code)
- LLM-powered fix generation
- PR automation with human review
- Feedback monitoring and auto-amendment

## Parsers

### SonarQube Parser
- **Filters**: BUG/VULNERABILITY, BLOCKER/CRITICAL
- **Input**: `issues[]` array from SonarQube API
- **Output**: Findings with file paths, line numbers, rule IDs

### Mend Parser
- **Filters**: ACTIVE alerts, all severity levels
- **Input**: `alerts[]` array from Mend SCA
- **Output**: Findings with CVE IDs, package names, fix hints

### Trivy Parser
- **Filters**: CRITICAL/HIGH/MEDIUM vulnerabilities
- **Input**: `Results[].Vulnerabilities[]` from Trivy scan
- **Output**: Findings with CVE IDs, package info, upgrade paths

## Usage Example

```python
from patchguard.parsers.sonarqube.parser import SonarQubeParser
from patchguard.parsers.mend.parser import MendParser
from patchguard.parsers.trivy.parser import TrivyParser
from patchguard.utils.severity import SeverityFilter

# Parse SonarQube scan
sonarqube_parser = SonarQubeParser()
with open("sonarqube_scan.json") as f:
    findings = sonarqube_parser.parse(f.read())

# Parse Mend scan
mend_parser = MendParser()
with open("mend_scan.json") as f:
    findings = mend_parser.parse(f.read())

# Parse Trivy scan
trivy_parser = TrivyParser()
with open("trivy_scan.json") as f:
    findings = trivy_parser.parse(f.read())

# Filter by severity
severity_filter = SeverityFilter()
critical_findings = severity_filter.filter(findings, "trivy")

# All findings are now in normalized format
for finding in critical_findings:
    print(f"{finding.finding_id}: {finding.message}")
    print(f"  Severity: {finding.severity.value}")
    print(f"  File: {finding.file_path}")
    if finding.fix_hint:
        print(f"  Fix: {finding.fix_hint}")
```

## Normalized Finding Schema

```python
@dataclass
class Finding:
    finding_id: str          # CVE-2024-38816 or AZrN_abc123
    source: str              # "sonarqube" | "mend" | "trivy"
    severity: Severity       # CRITICAL | HIGH | BLOCKER | MEDIUM | LOW
    category: str            # "BUG" | "VULNERABILITY" | "DEPENDENCY"
    file_path: str           # Affected file or package name
    message: str             # Description of the issue
    status: str              # "QUEUED" initially
    raw_data: dict           # Original tool-specific JSON
    line_start: int | None   # Line number (SonarQube) or None
    line_end: int | None     # End line or None
    fix_hint: str | None     # Suggested fix or fixed version
    rule_id: str | None      # Rule ID or CVE ID
    risk_level: str | None   # Set later by risk classifier
```

## Project Structure

```
PatchGuard/
├── patchguard/
│   ├── models/
│   │   └── finding.py              # Normalized Finding model
│   ├── parsers/
│   │   ├── base.py                 # Abstract ToolParser
│   │   ├── sonarqube/parser.py     # SonarQube parser
│   │   ├── mend/parser.py          # Mend parser
│   │   └── trivy/parser.py         # Trivy parser
│   └── utils/
│       └── severity.py             # SeverityFilter utility
├── tests/
│   ├── unit/                       # 5 test suites, 61 tests
│   └── fixtures/                   # 3 JSON test fixtures
├── docs/
│   ├── PROGRESS.md                 # Development progress
│   ├── IMPLEMENTATION_COMPLETE.md  # Completion summary
│   ├── PatchGuard_Project_Summary.md
│   └── PatchGuard_Task_Breakdown.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_sonarqube_parser.py -v

# With coverage
pytest tests/ --cov=patchguard --cov-report=html

# Coverage report will be in htmlcov/index.html
```

### Adding a New Parser

1. Create parser class inheriting from `ToolParser`
2. Implement `parse()` and `validate_schema()` methods
3. Write tests BEFORE implementation (TDD)
4. Add test fixture in `tests/fixtures/`
5. Update `SeverityFilter.DEFAULT_SEVERITIES`

Example:

```python
from patchguard.parsers.base import ToolParser
from patchguard.models.finding import Finding, Severity

class SnykParser(ToolParser):
    def parse(self, json_data: str | dict) -> List[Finding]:
        # Implementation here
        pass

    def validate_schema(self, data: dict) -> bool:
        # Validation here
        pass
```

## TDD Methodology

This project follows strict Test-Driven Development:

1. **RED**: Write failing tests first
2. **GREEN**: Write minimal code to pass tests
3. **REFACTOR**: Improve code while keeping tests green

Every line of implementation code was written to satisfy a failing test.

## Contributing

1. Follow TDD methodology (tests before code)
2. Maintain 80%+ test coverage
3. Use type hints throughout
4. Add docstrings to all public methods
5. Update tests when changing behavior

## License

[Add license information]

## Documentation

- [Project Summary](docs/PatchGuard_Project_Summary.md)
- [Task Breakdown](docs/PatchGuard_Task_Breakdown.md)
- [Implementation Complete](docs/IMPLEMENTATION_COMPLETE.md)
- [Progress Tracking](docs/PROGRESS.md)

## Contact

[Add contact information]

---

**Built with Test-Driven Development** 🧪
**Status**: Parser Foundation Complete ✅
**Next**: Risk Classification & Context Retrieval
