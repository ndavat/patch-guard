#!/usr/bin/env python3
"""
Sample vulnerable application for testing PatchGuard.
Contains various security issues and code quality problems.
"""

import os
import sys
import subprocess
import hashlib  # This import is unused - should trigger SonarQube S1481
import json

# Hardcoded secret - should trigger security scanning
API_KEY = "sk_live_1234567890abcdef1234567890abcdef"
DB_PASSWORD = "admin123"

def vulnerable_sql_query(user_input):
    """SQL injection vulnerability - concatenates user input directly."""
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    return query

def command_injection(filename):
    """Command injection vulnerability - unsanitized input to subprocess."""
    # This is dangerous - user input goes directly to shell
    result = subprocess.run(f"cat {filename}", shell=True, capture_output=True, text=True)
    return result.stdout

def weak_hash_cryptography(data):
    """Weak cryptography - using MD5 for security purposes."""
    # MD5 is cryptographically broken and should not be used for security
    return hashlib.md5(data.encode()).hexdigest()

def process_file_unsafe(filepath):
    """Path traversal vulnerability - no validation of file path."""
    # User could provide ../../etc/passwd
    with open(filepath, 'r') as f:
        return f.read()

def unused_function():
    """This function is never called - dead code."""
    x = 1
    y = 2
    return x + y

class UserProcessor:
    """Class with some issues."""

    def __init__(self, user_data):
        self.user_data = user_data
        # Unused instance variable
        self._internal_cache = {}

    def get_user_name(self):
        """Method that could be simplified."""
        if self.user_data is not None:
            if 'name' in self.user_data:
                return self.user_data['name']
            else:
                return "Unknown"
        else:
            return "Unknown"

    def potential_xss(self, user_input):
        """Potential XSS vulnerability - returns unsanitized user input."""
        # In a web context, this could be dangerous
        return f"<div>{user_input}</div>"

if __name__ == "__main__":
    # Example usage
    print("Sample vulnerable application")
    # This would normally be called from a web framework