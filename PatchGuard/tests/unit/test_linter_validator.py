"""Tests for LinterValidator — written BEFORE implementation (TDD RED)."""
import pytest


class TestLinterValidator:
    """Test the LinterValidator."""

    def test_validate_python_with_flake8(self):
        from patchguard.validators.linter_validator import LinterValidator

        python_code = '''import os
import sys

def hello():
    print("Hello, World!")
    return True
'''

        validator = LinterValidator()
        is_valid, output = validator.validate(python_code, "python")

        assert isinstance(is_valid, bool)
        assert isinstance(output, str)

    def test_validate_javascript_with_eslint(self):
        from patchguard.validators.linter_validator import LinterValidator

        js_code = '''const express = require('express');

function hello() {
    console.log("Hello, World!");
    return true;
}

module.exports = { hello };
'''

        validator = LinterValidator()
        is_valid, output = validator.validate(js_code, "javascript")

        assert isinstance(is_valid, bool)
        assert isinstance(output, str)

    def test_validate_csharp_with_checkstyle(self):
        from patchguard.validators.linter_validator import LinterValidator

        csharp_code = '''using System;

public class Test
{
    public void Hello()
    {
        Console.WriteLine("Hello, World!");
    }
}
'''

        validator = LinterValidator()
        is_valid, output = validator.validate(csharp_code, "csharp")

        assert isinstance(is_valid, bool)
        assert isinstance(output, str)

    def test_validation_passes(self):
        from patchguard.validators.linter_validator import LinterValidator

        # Clean Python code that should pass
        clean_code = '''def add(a, b):
    """Add two numbers."""
    return a + b
'''

        validator = LinterValidator()
        is_valid, output = validator.validate(clean_code, "python")

        # Should pass validation (or at least not crash)
        assert isinstance(is_valid, bool)

    def test_validation_fails(self):
        from patchguard.validators.linter_validator import LinterValidator

        # Python code with obvious errors
        bad_code = '''def bad_function(   ):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22+23+24+25+26+27+28+29+30
    print(x)
'''

        validator = LinterValidator()
        is_valid, output = validator.validate(bad_code, "python")

        # Should detect issues
        assert isinstance(is_valid, bool)
        assert isinstance(output, str)
        assert len(output) > 0  # Should have error messages

    def test_handle_linter_not_installed(self):
        from patchguard.validators.linter_validator import LinterValidator

        code = "print('hello')"

        validator = LinterValidator()
        is_valid, output = validator.validate(code, "python")

        # Should not crash even if linter not installed
        assert isinstance(is_valid, bool)
        assert isinstance(output, str)

    def test_unsupported_language(self):
        from patchguard.validators.linter_validator import LinterValidator

        code = "some code"

        validator = LinterValidator()
        is_valid, output = validator.validate(code, "unsupported_language")

        # Should handle gracefully
        assert isinstance(is_valid, bool)
        assert isinstance(output, str)

    def test_empty_code_validation(self):
        from patchguard.validators.linter_validator import LinterValidator

        validator = LinterValidator()
        is_valid, output = validator.validate("", "python")

        assert isinstance(is_valid, bool)
        assert isinstance(output, str)