"""Tests for DiffParser — written BEFORE implementation (TDD RED)."""
import pytest


class TestDiffParser:
    """Test the DiffParser."""

    def test_parse_unified_diff(self):
        from patchguard.generators.diff_parser import DiffParser

        diff_text = '''--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("hello")
+    print("Hello, World!")
     return True'''

        parser = DiffParser()
        parsed = parser.parse(diff_text)

        assert isinstance(parsed, dict)
        assert "file_path" in parsed
        assert "changes" in parsed
        assert parsed["file_path"] == "test.py"

    def test_apply_diff_to_file(self):
        from patchguard.generators.diff_parser import DiffParser

        original_code = '''def hello():
    print("hello")
    return True'''

        diff_text = '''--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("hello")
+    print("Hello, World!")
     return True'''

        parser = DiffParser()
        modified = parser.apply(original_code, diff_text)

        assert "Hello, World!" in modified
        assert 'print("hello")' not in modified
        assert "return True" in modified

    def test_handle_malformed_diff(self):
        from patchguard.generators.diff_parser import DiffParser, DiffError

        malformed_diff = "this is not a valid diff"

        parser = DiffParser()

        with pytest.raises(DiffError):
            parser.parse(malformed_diff)

    def test_extract_diff_from_markdown(self):
        from patchguard.generators.diff_parser import DiffParser

        markdown_response = '''Here's the fix for your SQL injection:

```diff
--- a/UserController.cs
+++ b/UserController.cs
@@ -39,2 +39,3 @@
-var query = "SELECT * FROM Users WHERE Id = '" + id + "'";
+var query = "SELECT * FROM Users WHERE Id = @id";
+command.Parameters.Add(new SqlParameter("@id", id));
```

This fix uses parameterized queries to prevent SQL injection.'''

        parser = DiffParser()
        extracted = parser.extract_from_markdown(markdown_response)

        assert "--- a/UserController.cs" in extracted
        assert "+++ b/UserController.cs" in extracted
        assert "@id" in extracted

    def test_handle_multiple_files(self):
        from patchguard.generators.diff_parser import DiffParser

        multi_file_diff = '''--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-print("old")
+print("new")
--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,1 @@
-x = 1
+x = 2'''

        parser = DiffParser()
        parsed = parser.parse(multi_file_diff)

        # Should handle multiple files
        assert isinstance(parsed, dict)
        # For now, just verify it doesn't crash

    def test_apply_diff_preserves_formatting(self):
        from patchguard.generators.diff_parser import DiffParser

        original_code = '''class Test:
    def method(self):
        print("original")
        return True'''

        diff_text = '''--- a/test.py
+++ b/test.py
@@ -2,2 +2,2 @@
     def method(self):
-        print("original")
+        print("modified")
         return True'''

        parser = DiffParser()
        modified = parser.apply(original_code, diff_text)

        # Should preserve indentation and structure
        assert "class Test:" in modified
        assert "    def method(self):" in modified
        assert "        print(\"modified\")" in modified
        assert "        return True" in modified