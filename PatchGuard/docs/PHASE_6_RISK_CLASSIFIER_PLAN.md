# Phase 6: Risk Classifier Implementation Plan

## Overview

**Goal**: Implement Loop 2 (Risk Classifier) that evaluates findings against a Safe-to-Fix policy and classifies them as LOW (auto-fixable) or HIGH (flag-only) risk.

**Status**: Planning Phase
**Prerequisites**: ✅ Phases 1-5 Complete (Parsers + Models)

## Architecture

```
Finding (QUEUED) → Risk Classifier → Finding (risk_level: LOW|HIGH)
                         ↓
                  Safe-to-Fix Policy
                  (configurable rules)
```

## Safe-to-Fix Policy Rules

### LOW Risk (Auto-Fixable)
- Direct dependency upgrades with `FixedVersion` available
- Simple SQL injection fixes (parameterized queries)
- Missing input validation (known patterns)
- Cookie security flags (HttpOnly, Secure, SameSite)
- Single-file changes with clear fix patterns
- Deterministic fixes with no behavioral changes

### HIGH Risk (Flag-Only)
- Transitive dependency vulnerabilities requiring cascade changes
- Complex logic bugs (race conditions, null pointers in business logic)
- Authentication/authorization flow changes
- CVEs with no `FixedVersion` available
- Changes spanning 3+ files
- Core abstractions or architectural changes

## Implementation Tasks (TDD)

### Task 6.1: Create Risk Policy Configuration
**Action**: Create `patchguard/config/risk_policy.py` with configurable rules

```python
@dataclass
class RiskRule:
    name: str
    condition: Callable[[Finding], bool]
    risk_level: str  # "LOW" or "HIGH"
    reason: str

class SafeToFixPolicy:
    rules: List[RiskRule]

    def evaluate(self, finding: Finding) -> Tuple[str, str]:
        """Returns (risk_level, reason)"""
```

---

### Task 6.2: 🔴 RED - Write `test_risk_classifier.py`
**Action**: Create `PatchGuard/tests/unit/test_risk_classifier.py`

**Test cases**:
- `test_direct_dependency_upgrade_is_low_risk` - Mend finding with FixedVersion → LOW
- `test_no_fixed_version_is_high_risk` - Trivy finding without FixedVersion → HIGH
- `test_sql_injection_with_pattern_is_low_risk` - SonarQube SQL injection → LOW
- `test_auth_flow_change_is_high_risk` - Finding in auth-related file → HIGH
- `test_multi_file_change_is_high_risk` - Finding affecting 3+ files → HIGH
- `test_single_file_simple_fix_is_low_risk` - Single file, known pattern → LOW
- `test_transitive_dependency_is_high_risk` - Indirect dependency → HIGH
- `test_unknown_pattern_defaults_to_high_risk` - No matching rule → HIGH
- `test_classifier_returns_reason` - Returns explanation for classification
- `test_custom_policy_overrides_defaults` - Custom rules take precedence

**Verify**: All tests FAIL (no implementation exists)

---

### Task 6.3: 🟢 GREEN - Implement RiskClassifier
**Action**: Create `PatchGuard/patchguard/classifiers/risk_classifier.py`

```python
class RiskClassifier:
    def __init__(self, policy: SafeToFixPolicy = None):
        self.policy = policy or SafeToFixPolicy.default()

    def classify(self, finding: Finding) -> Finding:
        """Evaluate finding and set risk_level field."""
        risk_level, reason = self.policy.evaluate(finding)
        finding.risk_level = risk_level
        finding.risk_reason = reason  # Add new field
        return finding

    def classify_batch(self, findings: List[Finding]) -> List[Finding]:
        """Classify multiple findings."""
        return [self.classify(f) for f in findings]
```

**Verify**: All tests PASS

---

### Task 6.4: 🔵 REFACTOR - Add Policy Rules
**Action**: Implement specific risk rules in `risk_policy.py`

**Rules to implement**:
1. **Direct Dependency Rule**: Mend/Trivy with FixedVersion → LOW
2. **No Fix Available Rule**: Missing FixedVersion → HIGH
3. **SQL Injection Pattern Rule**: SonarQube S3649 → LOW
4. **Auth File Rule**: file_path contains "auth", "login", "session" → HIGH
5. **Multi-File Rule**: (future: requires context) → HIGH
6. **Transitive Dependency Rule**: (future: requires dependency graph) → HIGH
7. **Default Rule**: No match → HIGH (safe default)

**Verify**: All tests STILL PASS

---

### Task 6.5: Create Risk Classifier Test Fixtures
**Action**: Create `tests/fixtures/risk_classifier_samples.py`

```python
# Sample findings for risk classification testing
LOW_RISK_SAMPLES = [
    # Direct dependency upgrade
    Finding(finding_id="CVE-2024-1234", source="mend", ...),
    # SQL injection with known pattern
    Finding(finding_id="SONAR-42", source="sonarqube", rule_id="csharpsquid:S3649", ...),
]

HIGH_RISK_SAMPLES = [
    # No fixed version
    Finding(finding_id="CVE-2024-5678", source="trivy", fix_hint=None, ...),
    # Auth-related file
    Finding(finding_id="SONAR-99", file_path="auth/LoginController.cs", ...),
]
```

---

### Task 6.6: Integration Test
**Action**: Create `tests/integration/test_parser_to_classifier.py`

**Test flow**:
```python
def test_end_to_end_sonarqube_to_classifier():
    # Parse SonarQube JSON
    parser = SonarQubeParser()
    findings = parser.parse(sonarqube_json)

    # Classify findings
    classifier = RiskClassifier()
    classified = classifier.classify_batch(findings)

    # Verify risk levels set
    assert all(f.risk_level in ["LOW", "HIGH"] for f in classified)
```

---

## File Structure

```
PatchGuard/
├── patchguard/
│   ├── classifiers/
│   │   ├── __init__.py
│   │   └── risk_classifier.py       # RiskClassifier implementation
│   └── config/
│       ├── __init__.py
│       └── risk_policy.py            # SafeToFixPolicy + rules
├── tests/
│   ├── unit/
│   │   └── test_risk_classifier.py   # Unit tests
│   ├── integration/
│   │   └── test_parser_to_classifier.py  # Integration tests
│   └── fixtures/
│       └── risk_classifier_samples.py    # Test data
```

## Success Criteria

- ✅ All tests pass (RED → GREEN → REFACTOR)
- ✅ Coverage ≥ 80% on classifier code
- ✅ Policy is configurable and extensible
- ✅ Clear reasoning for each classification
- ✅ Safe default (HIGH risk when uncertain)

## Next Phase After This

**Phase 7: Context Retriever (Loop 3)**
- Fetch ±50 lines around affected code
- Extract imports and dependencies
- Build context for LLM fix generation

---

**Status**: Ready to implement
**Estimated Tasks**: 6 (following TDD)
**Dependencies**: Phases 1-5 complete ✅
