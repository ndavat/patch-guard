# Testing PatchGuard with Sample Vulnerable Data

This guide shows how to test the PatchGuard autonomous security remediation agent using the sample vulnerable data provided.

## Sample Files Created

1. **sample_vulnerable_app.py** - Python application with security issues:
   - Unused import (`hashlib`)
   - Hardcoded secrets (API_KEY, DB_PASSWORD)
   - SQL injection vulnerability
   - Command injection vulnerability
   - Weak cryptography (MD5)
   - Other code quality issues

2. **requirements_vulnerable.txt** - Dependencies with known CVEs:
   - requests==2.25.1 (CVE-2021-22576)
   - urllib3==1.26.5 (CVE-2020-26137)
   - pyjwt==1.7.1 (CVE-2020-15157)
   - cryptography==2.8 (CVE-2020-06018)

3. **Dockerfile.vulnerable** - Dockerfile with OS vulnerabilities:
   - Ubuntu 18.04 with various package vulnerabilities

4. **Sample Scan Reports**:
   - `sample_sonarqube_scan.json` - SonarQube issues
   - `sample_mend_scan.json` - Mend dependency vulnerabilities
   - `sample_trivy_scan.json` - Trivy OS/package vulnerabilities

## How to Test

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test SonarQube Parser

```bash
python -c "
import json
from patchguard.parsers.sonarqube.parser import SonarQubeParser

with open('sample_sonarqube_scan.json') as f:
    data = json.load(f)

parser = SonarQubeParser()
findings = parser.parse(json.dumps(data))

print(f'Found {len(findings)} SonarQube findings:')
for finding in findings:
    print(f'  - {finding.finding_id}: {finding.message} [{finding.severity.value}]')
"
```

### 3. Test Mend Parser

```bash
python -c "
import json
from patchguard.parsers.mend.parser import MendParser

with open('sample_mend_scan.json') as f:
    data = json.load(f)

parser = MendParser()
findings = parser.parse(json.dumps(data))

print(f'Found {len(findings)} Mend findings:')
for finding in findings:
    print(f'  - {finding.finding_id}: {finding.message} [{finding.severity.value}] Fix: {finding.fix_hint}')
"
```

### 4. Test Trivy Parser

```bash
python -c "
import json
from patchguard.parsers.trivy.parser import TrivyParser

with open('sample_trivy_scan.json') as f:
    data = json.load(f)

parser = TrivyParser()
findings = parser.parse(json.dumps(data))

print(f'Found {len(findings)} Trivy findings:')
for finding in findings:
    print(f'  - {finding.finding_id}: {finding.message} [{finding.severity.value}] Fix: {finding.fix_hint}')
"
```

### 5. Test Severity Filtering

```bash
python -c "
import json
from patchguard.parsers.sonarqube.parser import SonarQubeParser
from patchguard.parsers.mend.parser import MendParser
from patchguard.parsers.trivy.parser import TrivyParser
from patchguard.utils.severity import SeverityFilter

# Parse all samples
with open('sample_sonarqube_scan.json') as f:
    sonar_data = json.load(f)
with open('sample_mend_scan.json') as f:
    mend_data = json.load(f)
with open('sample_trivy_scan.json') as f:
    trivy_data = json.load(f)

sonar_parser = SonarQubeParser()
mend_parser = MendParser()
trivy_parser = TrivyParser()

sonar_findings = sonar_parser.parse(json.dumps(sonar_data))
mend_findings = mend_parser.parse(json.dumps(mend_data))
trivy_findings = trivy_parser.parse(json.dumps(trivy_data))

all_findings = sonar_findings + mend_findings + trivy_findings
print(f'Total findings before filtering: {len(all_findings)}')

# Apply severity filtering
filter = SeverityFilter()
critical_findings = filter.filter(all_findings, 'sonarqube') + \
                   filter.filter(all_findings, 'mend') + \
                   filter.filter(all_findings, 'trivy')

print(f'Findings after severity filtering: {len(critical_findings)}')
for finding in critical_findings:
    print(f'  - {finding.finding_id}: {finding.message} [{finding.severity.value}]')
"
```

### 6. Test Risk Classification (Conceptual)

The risk classifier would evaluate findings like:
- **LOW RISK**: Unused imports, version upgrades with direct fix paths
- **HIGH RISK**: Hardcoded secrets, SQL injection, command injection (require manual review)

### 7. Expected Results

**SonarQube Findings:**
- 1 unused import (MINOR) → Filtered out by default severity settings
- 2 hardcoded secrets (BLOCKER) → Included
- 1 SQL injection (CRITICAL) → Included
- 1 command injection (CRITICAL) → Included
- 1 weak cryptography (HIGH) → Included

**Mend Findings:**
- 4 dependency vulnerabilities (HIGH/MEDIUM) → All included (Mend allows all severities)

**Trivy Findings:**
- 4 OS/package vulnerabilities (HIGH/MEDIUM) → All included (Trivy excludes LOW only)

## Next Steps for Full Pipeline

To test the full PatchGuard pipeline, you would need to:

1. Set up a GitHub repository with the vulnerable code
2. Configure PatchGuard with GitHub credentials
3. Run the ingestion loops to fetch scan data
4. Let the agentic loops process findings through:
   - Risk classification
   - Context retrieval
   - LLM fix generation
   - Validation
   - PR creation
5. Review the generated Pull Requests

## Security Notes

⚠️ **WARNING**: The sample code contains intentional security vulnerabilities:
- Hardcoded secrets (do not use in real applications)
- SQL injection vulnerabilities
- Command injection vulnerabilities
- Weak cryptography

These samples are for TESTING ONLY and should never be used in production.