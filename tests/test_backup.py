import tempfile
import unittest
from pathlib import Path

from snapkeep.backup import collect_files


class CollectFilesTests(unittest.TestCase):
    def test_collects_regular_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)

            (source / "README.md").write_text("test", encoding="utf-8")
            (source / "src").mkdir()
            (source / "src" / "main.py").write_text(
                "print('hello')",
                encoding="utf-8",
            )

            files = collect_files(source, [])

            relative_files = [
                path.relative_to(source).as_posix()
                for path in files
            ]

            self.assertEqual(
                relative_files,
                ["README.md", "src/main.py"],
            )

    def test_excludes_ignored_files_and_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)

            (source / "keep.txt").write_text("keep", encoding="utf-8")
            (source / "archive.zip").write_text("ignore", encoding="utf-8")

            cache = source / "__pycache__"
            cache.mkdir()
            (cache / "module.pyc").write_text("ignore", encoding="utf-8")

            files = collect_files(
                source,
                ["*.zip", "__pycache__/"],
            )

            relative_files = [
                path.relative_to(source).as_posix()
                for path in files
            ]

            self.assertEqual(relative_files, ["keep.txt"])


if __name__ == "__main__":
    unittest.main()
