import tempfile
import unittest
from pathlib import Path

from snapkeep.ignore import is_ignored, load_ignore_patterns


class LoadIgnorePatternsTests(unittest.TestCase):
    def test_missing_ignore_file_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ignore_file = Path(temp_dir) / ".backupignore"

            self.assertEqual(load_ignore_patterns(ignore_file), [])

    def test_comments_and_blank_lines_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ignore_file = Path(temp_dir) / ".backupignore"
            ignore_file.write_text(
                "# Comment\n"
                "\n"
                ".git/\n"
                "*.zip\n",
                encoding="utf-8",
            )

            self.assertEqual(
                load_ignore_patterns(ignore_file),
                [".git/", "*.zip"],
            )


class IsIgnoredTests(unittest.TestCase):
    def test_directory_pattern(self):
        patterns = [".git/"]

        self.assertTrue(
            is_ignored(Path(".git/config"), patterns)
        )

    def test_nested_directory_pattern(self):
        patterns = ["__pycache__/"]

        self.assertTrue(
            is_ignored(
                Path("src/snapkeep/__pycache__/cli.pyc"),
                patterns,
            )
        )

    def test_directory_wildcard_pattern(self):
        patterns = ["*.egg-info/"]

        self.assertTrue(
            is_ignored(
                Path("src/snapkeep.egg-info/PKG-INFO"),
                patterns,
            )
        )

    def test_file_wildcard_pattern(self):
        patterns = ["*.zip"]

        self.assertTrue(
            is_ignored(Path("archive/project.zip"), patterns)
        )

    def test_regular_file_is_not_ignored(self):
        patterns = [".git/", "*.zip", "__pycache__/"]

        self.assertFalse(
            is_ignored(Path("src/snapkeep/cli.py"), patterns)
        )


if __name__ == "__main__":
    unittest.main()
