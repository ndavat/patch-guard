# Phase 7: Context Retriever Implementation Plan

## Overview

**Goal**: Implement Loop 3 (Context Retriever) that fetches ±50 lines of code around affected locations and extracts relevant imports/dependencies to build context for LLM fix generation.

**Status**: Planning Phase
**Prerequisites**: ✅ Phases 1-6 Complete (Parsers + Models + Risk Classifier)

## Architecture

```
Finding (risk_level: LOW) → Context Retriever → Finding (context: CodeContext)
                                    ↓
                            File System Access
                            (read source files)
```

## Context Structure

```python
@dataclass
class CodeContext:
    file_path: str
    language: str              # "csharp", "python", "javascript", "dockerfile"
    affected_lines: str        # The specific lines with the issue
    surrounding_code: str      # ±50 lines around the issue
    imports: List[str]         # Import/using statements
    class_name: str | None     # Containing class (if applicable)
    method_name: str | None    # Containing method (if applicable)
    full_file: str | None      # Full file content (for small files)
```

## Implementation Tasks (TDD)

### Task 7.1: Create CodeContext Model
**Action**: Create `patchguard/models/code_context.py`

```python
@dataclass
class CodeContext:
    file_path: str
    language: str
    affected_lines: str
    surrounding_code: str
    imports: List[str]
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    full_file: Optional[str] = None
```

---

### Task 7.2: 🔴 RED - Write `test_context_retriever.py`
**Action**: Create `PatchGuard/tests/unit/test_context_retriever.py`

**Test cases**:
- `test_retrieve_context_with_line_numbers` - SonarQube finding with line → extract ±50 lines
- `test_extract_imports_csharp` - C# file → extract using statements
- `test_extract_imports_python` - Python file → extract import statements
- `test_extract_class_and_method` - Find containing class/method
- `test_handle_file_not_found` - Missing file → graceful error
- `test_handle_line_out_of_bounds` - Line > file length → return available lines
- `test_small_file_returns_full_content` - File < 100 lines → return full file
- `test_detect_language_from_extension` - .cs → csharp, .py → python, etc.
- `test_dependency_finding_no_file_access` - Mend/Trivy → no file to read
- `test_context_caching` - Same file read multiple times → cache result

**Verify**: All tests FAIL (no implementation exists)

---

### Task 7.3: Create Language Detector
**Action**: Create `PatchGuard/patchguard/utils/language_detector.py`

```python
class LanguageDetector:
    EXTENSIONS = {
        ".cs": "csharp",
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".dockerfile": "dockerfile",
        "Dockerfile": "dockerfile",
    }

    @staticmethod
    def detect(file_path: str) -> str:
        """Detect language from file extension."""
```

---

### Task 7.4: 🟢 GREEN - Implement ContextRetriever
**Action**: Create `PatchGuard/patchguard/retrievers/context_retriever.py`

```python
class ContextRetriever:
    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root
        self._file_cache = {}

    def retrieve(self, finding: Finding) -> CodeContext:
        """Retrieve code context for a finding."""
        # For dependency findings, return minimal context
        if finding.category == "DEPENDENCY":
            return self._dependency_context(finding)

        # For code findings, read file and extract context
        return self._code_context(finding)

    def _code_context(self, finding: Finding) -> CodeContext:
        """Extract context from source file."""
        file_path = os.path.join(self.repo_root, finding.file_path)
        lines = self._read_file(file_path)

        # Extract ±50 lines around affected line
        start = max(0, finding.line_start - 50)
        end = min(len(lines), finding.line_start + 50)
        surrounding = lines[start:end]

        # Extract imports
        imports = self._extract_imports(lines, language)

        return CodeContext(...)
```

**Verify**: All tests PASS

---

### Task 7.5: 🔵 REFACTOR - Add Import Extractors
**Action**: Create language-specific import extractors

**Extractors**:
- `CSharpImportExtractor` - Extract `using` statements
- `PythonImportExtractor` - Extract `import` and `from ... import`
- `JavaScriptImportExtractor` - Extract `import` and `require`
- `DockerfileImportExtractor` - Extract `FROM` statements

**Verify**: All tests STILL PASS

---

### Task 7.6: Create Test Fixtures
**Action**: Create sample source files for testing

```
tests/fixtures/source_files/
├── UserController.cs       # C# with SQL injection
├── helper.py               # Python with imports
├── api.js                  # JavaScript with requires
└── Dockerfile              # Dockerfile with FROM
```

---

### Task 7.7: Integration Test
**Action**: Create `tests/integration/test_classifier_to_retriever.py`

**Test flow**:
```python
def test_end_to_end_with_context():
    # Parse → Classify → Retrieve Context
    parser = SonarQubeParser()
    findings = parser.parse(sonarqube_json)

    classifier = RiskClassifier()
    classified = classifier.classify_batch(findings)

    retriever = ContextRetriever(repo_root="tests/fixtures/source_files")
    for finding in classified:
        if finding.risk_level == "LOW":
            context = retriever.retrieve(finding)
            assert context.surrounding_code is not None
```

---

## File Structure

```
PatchGuard/
├── patchguard/
│   ├── models/
│   │   └── code_context.py           # CodeContext dataclass
│   ├── retrievers/
│   │   ├── __init__.py
│   │   └── context_retriever.py      # ContextRetriever implementation
│   └── utils/
│       ├── language_detector.py      # Language detection
│       └── import_extractors.py      # Language-specific import extraction
├── tests/
│   ├── unit/
│   │   └── test_context_retriever.py # Unit tests
│   ├── integration/
│   │   └── test_classifier_to_retriever.py  # Integration tests
│   └── fixtures/
│       └── source_files/             # Sample source files
│           ├── UserController.cs
│           ├── helper.py
│           ├── api.js
│           └── Dockerfile
```

## Success Criteria

- ✅ All tests pass (RED → GREEN → REFACTOR)
- ✅ Coverage ≥ 80% on retriever code
- ✅ Handles missing files gracefully
- ✅ Supports C#, Python, JavaScript, Dockerfile
- ✅ Caches file reads for performance
- ✅ Extracts imports correctly per language

## Design Considerations

### 1. File Access Strategy
- Read files from repository root
- Cache file contents to avoid repeated reads
- Handle missing files gracefully (return error context)

### 2. Context Window Size
- Default: ±50 lines around affected line
- For small files (<100 lines): return full file
- For large files: return window + imports

### 3. Language Support
- Start with: C#, Python, JavaScript, Dockerfile
- Extensible design for adding more languages
- Language-specific import extraction

### 4. Dependency Findings
- Mend/Trivy findings don't have source files
- Return minimal context (package name, version, fix hint)
- No file system access needed

### 5. Performance
- Cache file contents in memory
- Lazy loading (only read when needed)
- Consider file size limits (skip files >10MB)

## Next Phase After This

**Phase 8: LLM Fix Generator (Loop 4)**
- Build prompts with security context
- Generate unified diffs
- Validate with linters
- Self-correction on failures

---

**Status**: Ready to implement
**Estimated Tasks**: 7 (following TDD)
**Dependencies**: Phases 1-6 complete ✅
