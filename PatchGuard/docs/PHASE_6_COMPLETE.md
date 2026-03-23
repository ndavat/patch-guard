# Phase 6: Risk Classifier - COMPLETE ✅

**Completion Date**: 2026-03-23
**Status**: All tasks complete, following strict TDD methodology

## Summary

Phase 6 successfully implemented Loop 2 (Risk Classifier) that evaluates findings against a Safe-to-Fix policy and classifies them as LOW (auto-fixable) or HIGH (flag-only) risk.

## What Was Built

### Core Components

**1. Risk Policy Configuration** (`patchguard/config/risk_policy.py`)
- `RiskRule` dataclass for defining classification rules
- `SafeToFixPolicy` class with configurable rule engine
- 5 default rules covering common scenarios
- First-match-wins evaluation strategy
- Safe default: HIGH risk when no rules match

**2. Risk Classifier** (`patchguard/classifiers/risk_classifier.py`)
- `RiskClassifier` class for evaluating findings
- `classify()` method for single finding evaluation
- `classify_batch()` method for bulk processing
- Sets `risk_level` and `risk_reason` fields on Finding objects

**3. Finding Model Enhancement**
- Added `risk_reason` field to Finding dataclass
- Provides explanation for risk classification decisions

### Default Risk Rules

| Rule | Condition | Risk Level | Reason |
|------|-----------|------------|--------|
| Direct Dependency Upgrade | Mend/Trivy with fix_hint | LOW | Known fixed version available |
| No Fix Available | Missing fix_hint | HIGH | No patch available yet |
| SQL Injection Pattern | SonarQube S3649 | LOW | Known fix pattern (parameterized queries) |
| Auth Flow Change | File path contains auth/login/session | HIGH | Security-critical code path |
| Single File Simple Fix | SonarQube with line + fix_hint | LOW | Clear location and fix hint |
| Default | No match | HIGH | Safe default for unknown patterns |

## Test Coverage

### Unit Tests (`tests/unit/test_risk_classifier.py`)
- 11 test cases covering all classification scenarios
- Tests for LOW risk: dependency upgrades, SQL injection patterns, simple fixes
- Tests for HIGH risk: no fix available, auth files, unknown patterns
- Tests for custom policy overrides
- Tests for batch classification

### Integration Tests (`tests/integration/test_parser_to_classifier.py`)
- 5 end-to-end tests from parser to classifier
- Tests for all three parsers (SonarQube, Mend, Trivy)
- Verifies data preservation through pipeline
- Tests mixed-source classification

### Test Fixtures (`tests/fixtures/risk_classifier_samples.py`)
- 4 LOW risk samples
- 5 HIGH risk samples
- Realistic test data based on actual findings

## Files Created

```
PatchGuard/
├── patchguard/
│   ├── classifiers/
│   │   ├── __init__.py
│   │   └── risk_classifier.py          # 45 lines
│   └── config/
│       ├── __init__.py
│       └── risk_policy.py               # 120 lines
├── tests/
│   ├── unit/
│   │   └── test_risk_classifier.py      # 220 lines - 11 tests
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_parser_to_classifier.py # 140 lines - 5 tests
│   └── fixtures/
│       └── risk_classifier_samples.py   # 110 lines
└── docs/
    └── PHASE_6_RISK_CLASSIFIER_PLAN.md
```

## Statistics

- **New Python files**: 7 (5 implementation + 2 __init__.py)
- **Total Python files**: 36 (was 29, now 36)
- **New test cases**: 16 (11 unit + 5 integration)
- **Total test cases**: 77 (was 61, now 77)
- **Lines of code added**: ~635
- **TDD Compliance**: 100% ✅

## TDD Methodology Compliance

✅ **Task 6.1**: Created risk policy configuration
✅ **Task 6.2**: 🔴 RED - Wrote failing tests first
✅ **Task 6.3**: 🟢 GREEN - Implemented minimal code to pass
✅ **Task 6.4**: 🔵 REFACTOR - Added policy rules
✅ **Task 6.5**: Created test fixtures
✅ **Task 6.6**: Integration tests for full pipeline

## Usage Example

```python
from patchguard.parsers.sonarqube.parser import SonarQubeParser
from patchguard.classifiers.risk_classifier import RiskClassifier

# Parse findings
parser = SonarQubeParser()
findings = parser.parse(sonarqube_json)

# Classify findings
classifier = RiskClassifier()
classified = classifier.classify_batch(findings)

# Filter by risk level
low_risk = [f for f in classified if f.risk_level == "LOW"]
high_risk = [f for f in classified if f.risk_level == "HIGH"]

print(f"Auto-fixable: {len(low_risk)}")
print(f"Manual review: {len(high_risk)}")

for finding in low_risk:
    print(f"{finding.finding_id}: {finding.risk_reason}")
```

## Custom Policy Example

```python
from patchguard.config.risk_policy import SafeToFixPolicy, RiskRule
from patchguard.classifiers.risk_classifier import RiskClassifier

# Define custom rules
custom_rules = [
    RiskRule(
        name="Allow All Dependencies",
        condition=lambda f: f.category == "DEPENDENCY",
        risk_level="LOW",
        reason="All dependency updates approved"
    ),
    # ... more rules
]

# Use custom policy
policy = SafeToFixPolicy(rules=custom_rules)
classifier = RiskClassifier(policy=policy)
```

## Key Design Decisions

### 1. Rule-Based Classification
- Configurable rules instead of hardcoded logic
- Easy to add new rules without changing classifier code
- First-match-wins for predictable behavior

### 2. Safe Default
- Unknown patterns default to HIGH risk
- Prevents accidental auto-fixing of risky changes
- Explicit opt-in for LOW risk patterns

### 3. Transparent Reasoning
- Every classification includes a reason
- Helps users understand why a finding was classified
- Enables audit trails and debugging

### 4. Extensible Design
- Custom policies can override defaults
- Rules are simple callables (easy to test)
- Policy can be swapped at runtime

## Next Phase

**Phase 7: Context Retriever (Loop 3)**
- Fetch ±50 lines around affected code
- Extract imports and dependencies
- Build context for LLM fix generation
- Handle different file types (C#, Python, JavaScript, Dockerfile)

---

**Status**: ✅ Phase 6 Complete
**Total Phases Complete**: 6 of 11
**Next Milestone**: Context Retrieval for LLM Fix Generation
