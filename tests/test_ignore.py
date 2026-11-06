import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from snapkeep.errors import IgnoreFileError
from snapkeep.ignore import is_ignored, load_ignore_patterns


class IsIgnoredTests(unittest.TestCase):
    def test_regular_file_is_not_ignored(self):
        self.assertFalse(is_ignored(Path("src/main.py"), ["*.log"]))

    def test_file_wildcard_pattern(self):
        self.assertTrue(is_ignored(Path("src/debug.log"), ["*.log"]))

    def test_directory_pattern(self):
        self.assertTrue(is_ignored(Path("build/output.bin"), ["build/"]))

    def test_nested_directory_pattern(self):
        self.assertTrue(is_ignored(Path("src/generated/file.py"), ["generated/"]))

    def test_directory_wildcard_pattern(self):
        self.assertTrue(is_ignored(Path("src/cache-v2/file.bin"), ["cache-*/"]))


class LoadIgnorePatternsTests(unittest.TestCase):
    def test_comments_and_blank_lines_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ignore_file = Path(temp_dir) / ".backupignore"
            ignore_file.write_text("# comment\n\n*.log\n build/ \n", encoding="utf-8")
            self.assertEqual(load_ignore_patterns(ignore_file), ["*.log", "build/"])

    def test_missing_ignore_file_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(
                load_ignore_patterns(Path(temp_dir) / "missing"),
                [],
            )

    def test_required_missing_ignore_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(IgnoreFileError):
                load_ignore_patterns(
                    Path(temp_dir) / "missing",
                    missing_ok=False,
                )

    def test_unreadable_ignore_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ignore_file = Path(temp_dir) / "ignore"
            ignore_file.write_text("*.tmp\n", encoding="utf-8")
            with patch(
                "snapkeep.ignore.Path.open",
                side_effect=PermissionError("permission denied"),
            ):
                with self.assertRaisesRegex(IgnoreFileError, "could not read"):
                    load_ignore_patterns(ignore_file)

    def test_malformed_utf8_ignore_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ignore_file = Path(temp_dir) / "ignore"
            ignore_file.write_bytes(b"\xff")
            with self.assertRaisesRegex(IgnoreFileError, "could not read"):
                load_ignore_patterns(ignore_file)


if __name__ == "__main__":
    unittest.main()
