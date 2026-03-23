# Phase 7: Context Retriever - COMPLETE ✅

**Completion Date**: 2026-03-23
**Status**: All tasks complete, following strict TDD methodology

## Summary

Phase 7 successfully implemented Loop 3 (Context Retriever) that fetches ±50 lines of code around affected locations and extracts relevant imports/dependencies to build context for LLM fix generation.

## What Was Built

### Core Components

**1. CodeContext Model** (`patchguard/models/code_context.py`)
- `CodeContext` dataclass for representing extracted code context
- Fields: file_path, language, affected_lines, surrounding_code, imports, class_name, method_name, full_file
- `to_dict()` method for serialization

**2. ContextRetriever** (`patchguard/retrievers/context_retriever.py`)
- `ContextRetriever` class for extracting code context from source files
- `retrieve()` method that handles both code and dependency findings
- File caching for performance (avoids repeated reads)
- Graceful error handling for missing files
- ±50 lines extraction around affected line
- Full file content for small files (<100 lines)

**3. Language Detector** (`patchguard/utils/language_detector.py`)
- `LanguageDetector` class for detecting language from file extensions
- Supports: C#, Python, JavaScript, TypeScript, Dockerfile, Java, Go, Ruby, PHP
- Handles special cases (Dockerfile without extension)

**4. Import Extractors** (`patchguard/utils/import_extractors.py`)
- Abstract `ImportExtractor` base class
- `CSharpImportExtractor` - Extracts `using` statements
- `PythonImportExtractor` - Extracts `import` and `from...import`
- `JavaScriptImportExtractor` - Extracts `import` and `require()`
- `DockerfileImportExtractor` - Extracts `FROM` statements
- `ImportExtractorFactory` for creating language-specific extractors

### Language Support

| Language | Extension | Import Pattern |
|----------|-----------|----------------|
| C# | .cs | `using System;` |
| Python | .py | `import os`, `from x import y` |
| JavaScript | .js, .jsx | `import x from 'y'`, `require('x')` |
| TypeScript | .ts, .tsx | `import x from 'y'` |
| Dockerfile | Dockerfile | `FROM node:18` |

## Test Coverage

### Unit Tests (`tests/unit/test_context_retriever.py`)
- 10 test cases covering all retrieval scenarios
- Tests for: line number extraction, import extraction (C#/Python), class/method detection
- Tests for: file not found, line out of bounds, small files, language detection
- Tests for: dependency findings, context caching

### Integration Tests (`tests/integration/test_classifier_to_retriever.py`)
- 5 end-to-end tests from classifier to retriever
- Tests full pipeline: parse → classify → retrieve context
- Verifies data preservation through pipeline
- Tests mixed risk levels and dependency handling

### Test Fixtures (`tests/fixtures/source_files/`)
- 4 realistic source files for testing
- `UserController.cs` - C# with SQL injection on line 42
- `helper.py` - Python with imports and functions
- `api.js` - JavaScript with Express API
- `Dockerfile` - Multi-stage Docker build

## Files Created

```
PatchGuard/
├── patchguard/
│   ├── models/
│   │   └── code_context.py              # 40 lines
│   ├── retrievers/
│   │   ├── __init__.py
│   │   └── context_retriever.py         # 180 lines
│   └── utils/
│       ├── language_detector.py         # 45 lines
│       └── import_extractors.py         # 130 lines
├── tests/
│   ├── unit/
│   │   └── test_context_retriever.py    # 240 lines - 10 tests
│   ├── integration/
│   │   └── test_classifier_to_retriever.py  # 150 lines - 5 tests
│   └── fixtures/
│       └── source_files/
│           ├── UserController.cs        # 58 lines
│           ├── helper.py                # 35 lines
│           ├── api.js                   # 42 lines
│           └── Dockerfile               # 13 lines
└── docs/
    └── PHASE_7_CONTEXT_RETRIEVER_PLAN.md
```

## Statistics

- **New Python files**: 8 (5 implementation + 1 __init__ + 2 tests)
- **Total Python files**: 44 (was 36, now 44)
- **New test cases**: 15 (10 unit + 5 integration)
- **Total test cases**: 92 (was 77, now 92)
- **Lines of code added**: ~933
- **TDD Compliance**: 100% ✅

## TDD Methodology Compliance

✅ **Task 7.1**: Created CodeContext model
✅ **Task 7.2**: 🔴 RED - Wrote failing tests first
✅ **Task 7.3**: Created Language Detector
✅ **Task 7.4**: 🟢 GREEN - Implemented ContextRetriever
✅ **Task 7.5**: 🔵 REFACTOR - Added import extractors
✅ **Task 7.6**: Created test fixtures (source files)
✅ **Task 7.7**: Integration tests for full pipeline

## Usage Example

```python
from patchguard.parsers.sonarqube.parser import SonarQubeParser
from patchguard.classifiers.risk_classifier import RiskClassifier
from patchguard.retrievers.context_retriever import ContextRetriever

# Parse findings
parser = SonarQubeParser()
findings = parser.parse(sonarqube_json)

# Classify risk
classifier = RiskClassifier()
classified = classifier.classify_batch(findings)

# Retrieve context for LOW risk findings
retriever = ContextRetriever(repo_root=".")

for finding in classified:
    if finding.risk_level == "LOW":
        context = retriever.retrieve(finding)

        print(f"File: {context.file_path}")
        print(f"Language: {context.language}")
        print(f"Imports: {len(context.imports)}")
        print(f"Context:\n{context.surrounding_code}")
```

## Key Design Decisions

### 1. File Caching
- Cache file contents in memory after first read
- Avoids repeated disk I/O for same file
- Significant performance improvement for batch processing

### 2. Context Window Size
- Default: ±50 lines around affected line
- Small files (<100 lines): return full file
- Configurable via line_start parameter

### 3. Graceful Degradation
- Missing files: return error context (no exception)
- Line out of bounds: return available lines
- Unknown language: return "unknown" (still processes)

### 4. Dependency Handling
- Mend/Trivy findings don't have source files
- Return minimal context with package info
- No file system access needed

### 5. Language-Specific Import Extraction
- Extensible factory pattern
- Easy to add new languages
- Language-specific parsing rules

## Pipeline Flow (Phases 1-7)

```
1. Scan JSON → Parser (SonarQube/Mend/Trivy)
2. Parser → Normalized Finding (status: QUEUED)
3. Finding → SeverityFilter (tool-specific thresholds)
4. Finding → RiskClassifier (LOW/HIGH risk)
5. Finding → ContextRetriever (extract code context)
6. Finding + Context → Ready for LLM Fix Generation (Phase 8)
```

## Next Phase

**Phase 8: LLM Fix Generator (Loop 4)**
- Build prompts with security context
- Generate unified diffs using LLM
- Validate fixes with linters (flake8, eslint, checkstyle)
- Self-correction on linter failures
- Support for multiple LLM providers (GPT-4o, Claude 3.5 Sonnet)

---

**Status**: ✅ Phase 7 Complete
**Total Phases Complete**: 7 of 11 (64%)
**Next Milestone**: LLM-Powered Fix Generation
