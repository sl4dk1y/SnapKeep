import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from snapkeep.archive import (
    build_archive_name,
    create_archive,
    verify_archive,
)


class BuildArchiveNameTests(unittest.TestCase):
    def test_builds_expected_archive_name(self):
        source = Path("/tmp/MyProject")
        timestamp = datetime(2026, 9, 3, 20, 15, 30)

        name = build_archive_name(
            source,
            timestamp=timestamp,
        )

        self.assertEqual(
            name,
            "MyProject_BACKUP_20260903-201530.zip",
        )


class CreateArchiveTests(unittest.TestCase):
    def test_creates_zip_with_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            destination = root / "archive"

            source.mkdir()
            (source / "README.md").write_text(
                "hello",
                encoding="utf-8",
            )

            nested = source / "src"
            nested.mkdir()
            (nested / "main.py").write_text(
                "print('hello')",
                encoding="utf-8",
            )

            files = [
                source / "README.md",
                source / "src" / "main.py",
            ]

            archive_path = create_archive(
                source,
                files,
                destination,
                timestamp=datetime(2026, 9, 3, 20, 15, 30),
            )

            self.assertTrue(archive_path.exists())

            with ZipFile(archive_path, "r") as archive:
                self.assertEqual(
                    sorted(archive.namelist()),
                    [
                        "README.md",
                        "src/main.py",
                    ],
                )

    def test_creates_destination_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            destination = root / "missing" / "archive"

            source.mkdir()
            file_path = source / "file.txt"
            file_path.write_text(
                "test",
                encoding="utf-8",
            )

            create_archive(
                source,
                [file_path],
                destination,
            )

            self.assertTrue(destination.is_dir())


class VerifyArchiveTests(unittest.TestCase):
    def test_valid_archive_passes_verification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "test.zip"

            with ZipFile(archive_path, "w") as archive:
                archive.writestr("file.txt", "hello")

            verify_archive(archive_path)


if __name__ == "__main__":
    unittest.main()
