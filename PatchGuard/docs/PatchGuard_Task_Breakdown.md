# PatchGuard — Agentic AI Task Breakdown

## Project Context

**Project Name:** PatchGuard (renamed from CodeSentinel)  
**Purpose:** Autonomous security remediation agent that ingests scan findings from SonarQube, Mend, and Trivy (JSON format), normalizes them, classifies risk, generates LLM-powered code fixes, and opens Pull Requests for mandatory human review.  
**Root Directory:** `PatchGuard/` (all code, tests, and docs go here)

---

## 🛡️ Guardrails — MUST READ BEFORE EVERY TASK

> **These rules are NON-NEGOTIABLE. Violating any guardrail is a blocking failure.**

### TDD Enforcement

| ID | Rule |
|----|------|
| **G1** | **Test BEFORE code.** No implementation file may be created until its test file exists with at least one failing test. |
| **G2** | **RED first.** Every 🔴 RED task must produce tests that FAIL because no implementation exists yet. Run `pytest` to confirm failures. |
| **G3** | **GREEN means minimal.** Every 🟢 GREEN task writes ONLY the code needed to make existing tests pass. Nothing extra. |
| **G4** | **REFACTOR preserves green.** Every 🔵 REFACTOR must end with ALL tests still passing. Run `pytest` to confirm. |
| **G5** | **Sequential phases.** Execute phases in order: 1 → 2 → 3 → 4 → 5. Within each phase, follow task numbering strictly. |

### Requirements Adherence

| ID | Rule |
|----|------|
| **G6** | **Match prompt files.** Every parser must handle the exact JSON structure documented in `security-scan/<tool>/prompt/*.md`. |
| **G7** | **Match severity configs.** Parsed findings must respect severity levels from `security-scan/<tool>/severity.txt`. |
| **G8** | **No old names.** Never use "CodeSentinel" or "Verdent" in any new file — always use "PatchGuard" or "patchguard". |

### Deviation Check (Run After Every Phase)

```
□ All tests from this phase pass (pytest green)
□ No implementation code exists without a corresponding test
□ Parser output matches the Normalized Finding Schema
□ Severity filtering aligns with severity.txt for the tool
□ No references to "CodeSentinel" or "Verdent" in new files
□ Coverage ≥ 80% on newly added code
```

---

## Reference Files (Read Before Starting)

| File | What It Contains | Why You Need It |
|------|-----------------|-----------------|
| `security-scan/sonarqube/prompt/SONARQUBE_ISSUE_FIX_PROMPT.md` | SonarQube JSON structure, field names, severity levels | Defines the JSON schema the SonarQube parser must handle |
| `security-scan/sonarqube/severity.txt` | `Type=Bug, Type=Vulnerability, Severity=Blocker, Severity=Critical` | Defines what the SonarQube parser must filter for |
| `security-scan/mend/prompt/MEND_VULNERABILITY_FIX_PROMPT.md` | Mend JSON structure, `alerts[]` array, `libraryName` format | Defines the JSON schema the Mend parser must handle |
| `security-scan/mend/severity.txt` | `Critical, High, Medium, Low` | All four severity levels are in scope for Mend |
| `security-scan/trivy/prompt/SECURITY_VULNERABILITY_FIX_PROMPT.md` | Trivy JSON structure, `Results[].Vulnerabilities[]` | Defines the JSON schema the Trivy parser must handle |
| `security-scan/trivy/severity.txt` | `CRITICAL, HIGH, MEDIUM` | Defines what the Trivy parser must filter for |
| `security-scan/sonarqube/manual-scan-report/*.json` | Real SonarQube scan data | Source for test fixture creation |
| `security-scan/mend/manual-scan-report/*.json` | Real Mend scan data | Source for test fixture creation |
| `security-scan/trivy/manual-scan-report/*.json` | Real Trivy scan data | Source for test fixture creation |

---

## Normalized Finding Schema (All Parsers Must Output This)

Every parser converts tool-specific JSON into this canonical `Finding` object:

```python
@dataclass
class Finding:
    finding_id: str          # e.g., "CVE-2024-38816" or "AZrN_abc123"
    source: str              # "sonarqube" | "mend" | "trivy"
    severity: Severity       # CRITICAL | HIGH | BLOCKER | MEDIUM | LOW
    category: str            # "BUG" | "VULNERABILITY" | "DEPENDENCY"
    file_path: str           # Affected file (or package name for dependencies)
    line_start: int | None   # Line number (SonarQube) or None (Mend/Trivy)
    line_end: int | None     # End line or None
    message: str             # Description of the issue
    fix_hint: str | None     # Suggested fix (topFix, FixedVersion, etc.)
    rule_id: str | None      # SonarQube rule ID or CVE ID
    risk_level: str | None   # "LOW" | "HIGH" | None (set later by classifier)
    status: str              # "QUEUED" initially
    raw_data: dict           # Original tool-specific JSON record
```

---

## Phase 1 — Project Scaffold (Tasks 1.1–1.4)

### TASK 1.1: Create Directory Structure

**Action:** Create the following directory tree with empty `__init__.py` files.

```
PatchGuard/
├── patchguard/
│   ├── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── sonarqube/
│   │   │   └── __init__.py
│   │   ├── mend/
│   │   │   └── __init__.py
│   │   └── trivy/
│   │       └── __init__.py
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   └── fixtures/
└── docs/
```

**Verify:** All directories exist, all `__init__.py` files created.

---

### TASK 1.2: Create `pyproject.toml`

**Action:** Create `PatchGuard/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "patchguard"
version = "0.1.0"
description = "PatchGuard — Autonomous Security Remediation Agent"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["patchguard"]
omit = ["tests/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

---

### TASK 1.3: Create `requirements.txt`

**Action:** Create `PatchGuard/requirements.txt`:

```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
```

**Verify:** `pip install -r requirements.txt` succeeds.

---

### TASK 1.4: Create `tests/conftest.py`

**Action:** Create `PatchGuard/tests/conftest.py` with shared fixture loaders:

```python
"""Shared pytest fixtures for PatchGuard test suite."""
import json
import pathlib
import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def sonarqube_sample():
    """Load SonarQube sample JSON fixture."""
    with open(FIXTURES_DIR / "sonarqube_sample.json", "r") as f:
        return json.load(f)


@pytest.fixture
def mend_sample():
    """Load Mend sample JSON fixture."""
    with open(FIXTURES_DIR / "mend_sample.json", "r") as f:
        return json.load(f)


@pytest.fixture
def trivy_sample():
    """Load Trivy sample JSON fixture."""
    with open(FIXTURES_DIR / "trivy_sample.json", "r") as f:
        return json.load(f)
```

**✅ Phase 1 Complete — Run Deviation Check before proceeding.**

---

## Phase 2 — Finding Model, TDD (Tasks 2.1–2.3)

### TASK 2.1: 🔴 RED — Write `test_finding_model.py`

**Action:** Create `PatchGuard/tests/unit/test_finding_model.py` with these tests (implementation DOES NOT exist yet — all tests must FAIL):

```python
"""Tests for the Finding model and Severity enum — written BEFORE implementation (TDD RED)."""
import pytest


class TestSeverityEnum:
    """Test the Severity enumeration."""

    def test_severity_critical_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.CRITICAL.value == "CRITICAL"

    def test_severity_high_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.HIGH.value == "HIGH"

    def test_severity_blocker_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.BLOCKER.value == "BLOCKER"

    def test_severity_medium_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.MEDIUM.value == "MEDIUM"

    def test_severity_low_exists(self):
        from patchguard.models.finding import Severity
        assert Severity.LOW.value == "LOW"

    def test_severity_from_string(self):
        from patchguard.models.finding import Severity
        assert Severity("CRITICAL") == Severity.CRITICAL

    def test_severity_invalid_raises(self):
        from patchguard.models.finding import Severity
        with pytest.raises(ValueError):
            Severity("INVALID")


class TestFindingModel:
    """Test the Finding dataclass."""

    def test_create_finding_with_required_fields(self):
        from patchguard.models.finding import Finding, Severity
        f = Finding(
            finding_id="CVE-2024-1234",
            source="trivy",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="Dockerfile",
            message="Update curl to 7.81.0-1ubuntu1.16",
            status="QUEUED",
            raw_data={"VulnerabilityID": "CVE-2024-1234"}
        )
        assert f.finding_id == "CVE-2024-1234"
        assert f.source == "trivy"
        assert f.severity == Severity.CRITICAL

    def test_finding_optional_fields_default_to_none(self):
        from patchguard.models.finding import Finding, Severity
        f = Finding(
            finding_id="TEST-001",
            source="sonarqube",
            severity=Severity.BLOCKER,
            category="BUG",
            file_path="src/main.py",
            message="Null pointer",
            status="QUEUED",
            raw_data={}
        )
        assert f.line_start is None
        assert f.line_end is None
        assert f.fix_hint is None
        assert f.rule_id is None
        assert f.risk_level is None

    def test_finding_with_all_fields(self):
        from patchguard.models.finding import Finding, Severity
        f = Finding(
            finding_id="SONAR-42",
            source="sonarqube",
            severity=Severity.CRITICAL,
            category="VULNERABILITY",
            file_path="Controllers/UserController.cs",
            line_start=42,
            line_end=42,
            message="SQL injection risk",
            fix_hint="Use parameterized queries",
            rule_id="csharpsquid:S3649",
            risk_level="LOW",
            status="QUEUED",
            raw_data={"key": "SONAR-42"}
        )
        assert f.line_start == 42
        assert f.fix_hint == "Use parameterized queries"
        assert f.rule_id == "csharpsquid:S3649"
        assert f.risk_level == "LOW"

    def test_finding_to_dict(self):
        from patchguard.models.finding import Finding, Severity
        f = Finding(
            finding_id="CVE-2024-5678",
            source="mend",
            severity=Severity.HIGH,
            category="DEPENDENCY",
            file_path="package.json",
            message="Upgrade lodash",
            status="QUEUED",
            raw_data={}
        )
        d = f.to_dict()
        assert isinstance(d, dict)
        assert d["finding_id"] == "CVE-2024-5678"
        assert d["severity"] == "HIGH"
        assert d["source"] == "mend"

    def test_finding_equality(self):
        from patchguard.models.finding import Finding, Severity
        f1 = Finding(finding_id="X", source="trivy", severity=Severity.LOW,
                     category="VULNERABILITY", file_path="f.py",
                     message="msg", status="QUEUED", raw_data={})
        f2 = Finding(finding_id="X", source="trivy", severity=Severity.LOW,
                     category="VULNERABILITY", file_path="f.py",
                     message="msg", status="QUEUED", raw_data={})
        assert f1 == f2
```

**Verify (G2):** Run `pytest tests/unit/test_finding_model.py` → ALL tests must FAIL with `ModuleNotFoundError`.

---

### TASK 2.2: 🟢 GREEN — Implement Finding Model

**Action:** Create `PatchGuard/patchguard/models/finding.py` with minimal code to pass ALL tests from Task 2.1.

**Requirements:**
- `Severity` enum with values: `CRITICAL`, `HIGH`, `BLOCKER`, `MEDIUM`, `LOW`
- `Finding` dataclass with fields matching the Normalized Finding Schema (see above)
- Optional fields (`line_start`, `line_end`, `fix_hint`, `rule_id`, `risk_level`) default to `None`
- `to_dict()` method that returns a dict with `severity` as string value
- Equality based on dataclass default `__eq__`

**Verify (G3):** Run `pytest tests/unit/test_finding_model.py` → ALL tests must PASS.

---

### TASK 2.3: 🔵 REFACTOR — Polish Finding Model

**Action:** Add `__repr__`, field validation (e.g., `source` must be one of `sonarqube|mend|trivy`), and docstrings. 

**Verify (G4):** Run `pytest tests/unit/test_finding_model.py` → ALL tests STILL pass.

**✅ Phase 2 Complete — Run Deviation Check before proceeding.**

---

## Phase 3 — SonarQube Parser, TDD (Tasks 3.1–3.5)

### TASK 3.1: Create SonarQube Test Fixture

**Action:** Create `PatchGuard/tests/fixtures/sonarqube_sample.json`.

Read one of the real scan files from `security-scan/sonarqube/manual-scan-report/*.json`. Extract a sanitized subset containing:
- 2 issues with `type=VULNERABILITY`, `severity=CRITICAL` (should be INCLUDED)
- 1 issue with `type=BUG`, `severity=BLOCKER` (should be INCLUDED)
- 1 issue with `type=CODE_SMELL`, `severity=MAJOR` (should be EXCLUDED by parser)
- 1 issue with `type=BUG`, `severity=MINOR` (should be EXCLUDED by parser)

Structure must match the JSON format from `SONARQUBE_ISSUE_FIX_PROMPT.md`:
```json
{
  "issues": [
    {
      "key": "...",
      "rule": "csharpsquid:SXXXX",
      "severity": "CRITICAL",
      "component": "ProjectName:Path/To/File.cs",
      "line": 42,
      "message": "...",
      "type": "VULNERABILITY",
      "status": "OPEN",
      "impacts": [{"softwareQuality": "SECURITY", "severity": "HIGH"}],
      "cleanCodeAttribute": "TRUSTWORTHY",
      "cleanCodeAttributeCategory": "RESPONSIBLE"
    }
  ]
}
```

---

### TASK 3.2: 🔴 RED — Write `test_sonarqube_parser.py`

**Action:** Create `PatchGuard/tests/unit/test_sonarqube_parser.py`:

**Test cases (all must FAIL since parser doesn't exist):**

| Test | What It Asserts |
|------|----------------|
| `test_parse_returns_list_of_findings` | `parse()` returns a `list` of `Finding` objects |
| `test_filters_bug_and_vulnerability_only` | Only `type=BUG` and `type=VULNERABILITY` issues are returned |
| `test_filters_blocker_and_critical_only` | Only `severity=BLOCKER` and `severity=CRITICAL` issues pass through |
| `test_excludes_code_smells` | Issues with `type=CODE_SMELL` are excluded |
| `test_excludes_low_severity` | Issues with `severity=MINOR`, `MAJOR`, `INFO` are excluded |
| `test_maps_component_to_file_path` | `component` field `"ProjectName:Path/To/File.cs"` → `file_path="Path/To/File.cs"` (prefix stripped) |
| `test_maps_line_number` | `line` field → `line_start` and `line_end` |
| `test_maps_severity_correctly` | `"CRITICAL"` → `Severity.CRITICAL`, `"BLOCKER"` → `Severity.BLOCKER` |
| `test_source_is_sonarqube` | Every Finding has `source="sonarqube"` |
| `test_empty_issues_returns_empty_list` | `{"issues": []}` → returns `[]` |
| `test_malformed_json_raises_error` | Invalid JSON string raises `ValueError` |
| `test_missing_issues_key_raises_error` | `{"data": []}` (no `issues` key) raises `ValueError` |

**Verify (G2):** Run `pytest tests/unit/test_sonarqube_parser.py` → ALL FAIL.

---

### TASK 3.3: Create Abstract ToolParser Base

**Action:** Create `PatchGuard/patchguard/parsers/base.py`:

```python
"""Abstract base class for all tool-specific parsers."""
from abc import ABC, abstractmethod
from typing import List
from patchguard.models.finding import Finding


class ToolParser(ABC):
    """Base parser interface. All tool parsers must implement this."""

    @abstractmethod
    def parse(self, json_data: str | dict) -> List[Finding]:
        """Parse tool-specific JSON and return normalized Finding objects.
        
        Args:
            json_data: Either a JSON string or already-parsed dict.
            
        Returns:
            List of normalized Finding objects.
            
        Raises:
            ValueError: If the input is malformed or missing required fields.
        """
        ...

    @abstractmethod
    def validate_schema(self, data: dict) -> bool:
        """Validate that input data matches expected schema.
        
        Args:
            data: Parsed JSON dict.
            
        Returns:
            True if valid, raises ValueError otherwise.
        """
        ...
```

---

### TASK 3.4: 🟢 GREEN — Implement SonarQube Parser

**Action:** Create `PatchGuard/patchguard/parsers/sonarqube/parser.py`.

Implement `SonarQubeParser(ToolParser)` that:
1. Accepts JSON string or dict
2. Validates `issues` key exists
3. Filters: only `type` in (`BUG`, `VULNERABILITY`) AND `severity` in (`BLOCKER`, `CRITICAL`)
4. Maps each issue to a `Finding` object:
   - `finding_id` = `issue["key"]`
   - `source` = `"sonarqube"`
   - `severity` = mapped from issue `severity` string
   - `category` = issue `type`
   - `file_path` = `component` with project prefix stripped (everything before `:`)
   - `line_start` / `line_end` = issue `line`
   - `message` = issue `message`
   - `rule_id` = issue `rule`
   - `status` = `"QUEUED"`

**Verify (G3):** Run `pytest tests/unit/test_sonarqube_parser.py` → ALL PASS.

---

### TASK 3.5: 🔵 REFACTOR — Improve SonarQube Parser

**Action:** Extract helper methods, add docstrings, handle edge cases (missing `line`, missing `component` prefix).

**Verify (G4):** Run `pytest tests/unit/test_sonarqube_parser.py` → ALL STILL PASS.

**✅ Phase 3 Complete — Run Deviation Check. Cross-check against `SONARQUBE_ISSUE_FIX_PROMPT.md` and `sonarqube/severity.txt`.**

---

## Phase 4 — Mend Parser, TDD (Tasks 4.1–4.4)

### TASK 4.1: Create Mend Test Fixture

**Action:** Create `PatchGuard/tests/fixtures/mend_sample.json`.

Read from `security-scan/mend/manual-scan-report/*.json`. Extract a sanitized subset containing:
- 1 alert with `severity=CRITICAL`, `topFix` present (should be INCLUDED)
- 1 alert with `severity=HIGH`, `topFix` present (should be INCLUDED)
- 1 alert with `severity=MEDIUM` (should be INCLUDED — Mend processes all levels)
- 1 alert with `severity=LOW` (should be INCLUDED)
- 1 alert with `status=INACTIVE` (should be EXCLUDED — only `ACTIVE` processed)
- 1 alert with no `topFix` field (should be INCLUDED but `fix_hint=None`)

Structure must match `MEND_VULNERABILITY_FIX_PROMPT.md`:
```json
{
  "alerts": [
    {
      "vulnerabilityId": "CVE-XXXX-XXXXX",
      "libraryName": "package.name.1.0.0.nupkg",
      "severity": "HIGH",
      "cvssScore": "8.1",
      "status": "ACTIVE",
      "exploitAvailable": "POC_CODE",
      "confidenceScore": 0.011,
      "topFix": {
        "type": "UPGRADE_VERSION",
        "fixResolution": "Upgrade to version Package - 1.0.1"
      }
    }
  ]
}
```

---

### TASK 4.2: 🔴 RED — Write `test_mend_parser.py`

**Action:** Create `PatchGuard/tests/unit/test_mend_parser.py`:

| Test | What It Asserts |
|------|----------------|
| `test_parse_returns_list_of_findings` | Returns `list[Finding]` |
| `test_filters_active_alerts_only` | Only `status=ACTIVE` alerts are processed |
| `test_includes_all_severity_levels` | CRITICAL, HIGH, MEDIUM, LOW all included (per `mend/severity.txt`) |
| `test_extracts_package_name_from_library` | `"system.drawing.common.4.7.0.nupkg"` → package=`"system.drawing.common"`, version=`"4.7.0"` |
| `test_extracts_fix_hint_from_topfix` | `topFix.fixResolution` → `fix_hint` |
| `test_missing_topfix_sets_fix_hint_none` | Alert without `topFix` → `fix_hint=None` |
| `test_source_is_mend` | Every Finding has `source="mend"` |
| `test_category_is_dependency` | Every Finding has `category="DEPENDENCY"` |
| `test_finding_id_is_vulnerability_id` | `vulnerabilityId` → `finding_id` |
| `test_empty_alerts_returns_empty_list` | `{"alerts": []}` → returns `[]` |
| `test_malformed_json_raises_error` | Invalid input raises `ValueError` |
| `test_missing_alerts_key_raises_error` | Missing `alerts` key raises `ValueError` |

**Verify (G2):** Run `pytest tests/unit/test_mend_parser.py` → ALL FAIL.

---

### TASK 4.3: 🟢 GREEN — Implement Mend Parser

**Action:** Create `PatchGuard/patchguard/parsers/mend/parser.py`.

Implement `MendParser(ToolParser)` that:
1. Validates `alerts` key exists
2. Filters: only `status=ACTIVE`
3. Extracts package name and version from `libraryName` (format: `package.name.version.nupkg`)
4. Maps each alert to a `Finding` object:
   - `finding_id` = `vulnerabilityId`
   - `source` = `"mend"`
   - `severity` = mapped from alert `severity`
   - `category` = `"DEPENDENCY"`
   - `file_path` = package name (extracted from `libraryName`)
   - `message` = fix resolution or CVE description
   - `fix_hint` = `topFix.fixResolution` if present, else `None`
   - `rule_id` = `vulnerabilityId`

**Verify (G3):** Run `pytest tests/unit/test_mend_parser.py` → ALL PASS.

---

### TASK 4.4: 🔵 REFACTOR — Improve Mend Parser

**Action:** Improve `libraryName` version extraction regex, add deduplication for same CVE across multiple libraries, docstrings.

**Verify (G4):** ALL tests STILL PASS.

**✅ Phase 4 Complete — Run Deviation Check. Cross-check against `MEND_VULNERABILITY_FIX_PROMPT.md` and `mend/severity.txt`.**

---

## Phase 5 — Trivy Parser + Severity Filter, TDD (Tasks 5.1–5.5)

### TASK 5.1: Create Trivy Test Fixture

**Action:** Create `PatchGuard/tests/fixtures/trivy_sample.json`.

Read from `security-scan/trivy/manual-scan-report/*.json`. Extract a sanitized subset:
- 1 vulnerability with `Severity=CRITICAL`, `FixedVersion` present (INCLUDED)
- 1 vulnerability with `Severity=HIGH`, `FixedVersion` present (INCLUDED)
- 1 vulnerability with `Severity=MEDIUM`, `FixedVersion` present (INCLUDED — per `trivy/severity.txt`)
- 1 vulnerability with `Severity=LOW` (EXCLUDED)
- 1 vulnerability with `Severity=CRITICAL`, NO `FixedVersion` (INCLUDED but flagged)

Structure must match `SECURITY_VULNERABILITY_FIX_PROMPT.md`:
```json
{
  "Results": [
    {
      "Target": "image:tag (os version)",
      "Vulnerabilities": [
        {
          "VulnerabilityID": "CVE-XXXX-XXXXX",
          "PkgName": "package-name",
          "InstalledVersion": "1.0.0",
          "FixedVersion": "1.0.1",
          "Severity": "CRITICAL",
          "Title": "Short description",
          "CVSS": { "nvd": { "V3Score": 9.8 } }
        }
      ]
    }
  ]
}
```

---

### TASK 5.2: 🔴 RED — Write `test_trivy_parser.py`

**Action:** Create `PatchGuard/tests/unit/test_trivy_parser.py`:

| Test | What It Asserts |
|------|----------------|
| `test_parse_returns_list_of_findings` | Returns `list[Finding]` |
| `test_filters_critical_high_medium_only` | Only CRITICAL, HIGH, MEDIUM included (per `trivy/severity.txt`) |
| `test_excludes_low_severity` | LOW severity excluded |
| `test_maps_vulnerability_id` | `VulnerabilityID` → `finding_id` and `rule_id` |
| `test_maps_package_info` | `PkgName` → `file_path`, `InstalledVersion` in message |
| `test_maps_fixed_version_to_fix_hint` | `FixedVersion` → `fix_hint` |
| `test_missing_fixed_version_sets_fix_hint_none` | No `FixedVersion` → `fix_hint=None` |
| `test_source_is_trivy` | Every Finding has `source="trivy"` |
| `test_category_is_vulnerability` | Category = `"VULNERABILITY"` |
| `test_empty_results_returns_empty_list` | `{"Results": []}` → `[]` |
| `test_null_vulnerabilities_returns_empty_list` | `Results[0]` with no `Vulnerabilities` key → `[]` |
| `test_malformed_json_raises_error` | Invalid input raises `ValueError` |

**Verify (G2):** Run `pytest tests/unit/test_trivy_parser.py` → ALL FAIL.

---

### TASK 5.3: 🟢 GREEN — Implement Trivy Parser

**Action:** Create `PatchGuard/patchguard/parsers/trivy/parser.py`.

Implement `TrivyParser(ToolParser)` that:
1. Validates `Results` key exists
2. Iterates `Results[].Vulnerabilities[]`
3. Filters: only `Severity` in (`CRITICAL`, `HIGH`, `MEDIUM`) per `trivy/severity.txt`
4. Maps to `Finding`:
   - `finding_id` = `VulnerabilityID`
   - `source` = `"trivy"`
   - `severity` = mapped from `Severity`
   - `category` = `"VULNERABILITY"`
   - `file_path` = `PkgName`
   - `message` = `Title` or `Description`
   - `fix_hint` = `FixedVersion` if present
   - `rule_id` = `VulnerabilityID`

**Verify (G3):** Run `pytest tests/unit/test_trivy_parser.py` → ALL PASS.

---

### TASK 5.4: 🔴 RED — Write `test_severity_filter.py`

**Action:** Create `PatchGuard/tests/unit/test_severity_filter.py`:

| Test | What It Asserts |
|------|----------------|
| `test_filter_sonarqube_allows_blocker_critical` | SonarQube findings with BLOCKER/CRITICAL pass, others filtered |
| `test_filter_mend_allows_all_levels` | Mend findings with CRITICAL/HIGH/MEDIUM/LOW all pass |
| `test_filter_trivy_allows_critical_high_medium` | Trivy findings with CRITICAL/HIGH/MEDIUM pass, LOW filtered |
| `test_filter_with_custom_thresholds` | Custom severity list overrides defaults |
| `test_filter_empty_list_returns_empty` | Empty input → empty output |

**Verify (G2):** ALL FAIL.

---

### TASK 5.5: 🟢 GREEN — Implement SeverityFilter

**Action:** Create `PatchGuard/patchguard/utils/severity.py`.

Implement `SeverityFilter` class with:
- Default severity configs per tool (matching `severity.txt` files)
- `filter(findings, tool)` method that filters findings by allowed severities
- Support for custom severity overrides

**Verify (G3):** Run `pytest tests/unit/test_severity_filter.py` → ALL PASS.

**✅ Phase 5 Complete — Run Deviation Check.**

---

## Final Verification

Run full test suite with coverage:

```powershell
cd PatchGuard
python -m pytest tests/ -v --tb=short --cov=patchguard --cov-report=term-missing
```

**Expected results:**
- ✅ All tests pass (0 failures)
- ✅ Coverage ≥ 80% on `patchguard/` package
- ✅ No "CodeSentinel" or "Verdent" references in new files
- ✅ All parsers match their respective prompt file JSON structures
- ✅ All severity filters match their `severity.txt` configs
