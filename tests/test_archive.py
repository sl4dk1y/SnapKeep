import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from snapkeep.errors import ArchiveVerificationError
from snapkeep.archive import (
    build_archive_name,
    choose_archive_path,
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

    def test_uses_custom_snapshot_name(self):
        source = Path("/tmp/project")
        timestamp = datetime(2026, 9, 3, 22, 30, 0)

        archive_name = build_archive_name(
            source,
            timestamp=timestamp,
            name="before-refactor",
        )

        self.assertEqual(
            archive_name,
            "before-refactor_BACKUP_20260903-223000.zip",
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

    def test_does_not_overwrite_archive_with_same_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            destination = root / "archive"

            source.mkdir()
            file_path = source / "file.txt"
            file_path.write_text("first", encoding="utf-8")

            timestamp = datetime(2026, 9, 3, 20, 37, 0)

            first_archive = create_archive(
                source,
                [file_path],
                destination,
                timestamp=timestamp,
            )

            file_path.write_text("second", encoding="utf-8")

            second_archive = create_archive(
                source,
                [file_path],
                destination,
                timestamp=timestamp,
            )

            self.assertNotEqual(
                first_archive,
                second_archive,
            )

            self.assertTrue(first_archive.exists())
            self.assertTrue(second_archive.exists())

class VerifyArchiveTests(unittest.TestCase):
    def test_valid_archive_passes_verification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "test.zip"

            with ZipFile(archive_path, "w") as archive:
                archive.writestr("file.txt", "hello")

            verify_archive(archive_path)

    def test_invalid_archive_fails_verification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "broken.zip"
            archive_path.write_text(
                "this is not a zip archive",
                encoding="utf-8",
            )

            with self.assertRaises(ArchiveVerificationError):
                verify_archive(archive_path)

class ChooseArchivePathTests(unittest.TestCase):
    def test_returns_original_name_when_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir)

            path = choose_archive_path(
                destination,
                "project_BACKUP_20260903-203700.zip",
            )

            self.assertEqual(
                path.name,
                "project_BACKUP_20260903-203700.zip",
            )

    def test_adds_counter_when_archive_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir)

            first = destination / "project_BACKUP_20260903-203700.zip"
            first.write_text("existing", encoding="utf-8")

            path = choose_archive_path(
                destination,
                first.name,
            )

            self.assertEqual(
                path.name,
                "project_BACKUP_20260903-203700-1.zip",
            )

    def test_increments_counter_until_name_is_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir)

            base = "project_BACKUP_20260903-203700.zip"

            (destination / base).write_text(
                "existing",
                encoding="utf-8",
            )
            (destination / "project_BACKUP_20260903-203700-1.zip").write_text(
                "existing",
                encoding="utf-8",
            )

            path = choose_archive_path(
                destination,
                base,
            )

            self.assertEqual(
                path.name,
                "project_BACKUP_20260903-203700-2.zip",
            )

if __name__ == "__main__":
    unittest.main()
