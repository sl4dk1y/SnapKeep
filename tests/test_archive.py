import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from snapkeep.archive import (
    build_archive_name,
    choose_archive_path,
    create_archive,
    verify_archive,
)
from snapkeep.errors import ArchiveError, ArchiveVerificationError


class BuildArchiveNameTests(unittest.TestCase):
    def test_builds_expected_archive_name(self):
        source = Path("/tmp/MyProject")
        timestamp = datetime(2026, 9, 3, 20, 15, 30)
        name = build_archive_name(source, timestamp=timestamp)
        self.assertEqual(name, "MyProject_BACKUP_20260903-201530.zip")

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
    def setUp(self):
        self.timestamp = datetime(2026, 9, 3, 20, 37, 0)

    def _source(self, root):
        source = root / "project"
        source.mkdir()
        file_path = source / "file.txt"
        file_path.write_text("snapshot", encoding="utf-8")
        return source, file_path

    def test_creates_zip_with_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            nested = source / "src"
            nested.mkdir()
            (nested / "main.py").write_text("print('hello')", encoding="utf-8")

            archive_path = create_archive(
                source,
                [file_path, nested / "main.py"],
                root / "archive",
                timestamp=self.timestamp,
            )

            self.assertTrue(archive_path.exists())
            with ZipFile(archive_path, "r") as archive:
                self.assertEqual(
                    sorted(archive.namelist()),
                    ["file.txt", "src/main.py"],
                )

    def test_creates_destination_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            destination = root / "missing" / "archive"
            create_archive(source, [file_path], destination)
            self.assertTrue(destination.is_dir())

    def test_does_not_overwrite_archive_with_same_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            first = create_archive(
                source, [file_path], root / "archive", timestamp=self.timestamp
            )
            file_path.write_text("second", encoding="utf-8")
            second = create_archive(
                source, [file_path], root / "archive", timestamp=self.timestamp
            )
            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())

    def test_existing_base_and_suffix_collisions_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            destination = root / "archive"
            destination.mkdir()
            base = build_archive_name(source, timestamp=self.timestamp)
            existing = [
                destination / base,
                destination / base.replace(".zip", "-1.zip"),
            ]
            for path in existing:
                path.write_text("keep me", encoding="utf-8")

            created = create_archive(
                source, [file_path], destination, timestamp=self.timestamp
            )

            self.assertEqual(created.name, base.replace(".zip", "-2.zip"))
            self.assertEqual(
                [path.read_text(encoding="utf-8") for path in existing],
                ["keep me", "keep me"],
            )

    def test_concurrent_creations_reserve_distinct_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            destination = root / "archive"

            def create():
                return create_archive(
                    source, [file_path], destination, timestamp=self.timestamp
                )

            with ThreadPoolExecutor(max_workers=8) as executor:
                paths = list(executor.map(lambda _: create(), range(8)))

            self.assertEqual(len(set(paths)), 8)
            self.assertEqual(len(list(destination.glob("*.zip"))), 8)
            for path in paths:
                verify_archive(path)

    def test_retries_when_another_process_occupies_chosen_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            destination = root / "archive"
            original_open = __import__("os").open
            occupied = []

            def create_collision_then_open(path, flags, mode=0o777):
                candidate = Path(path)
                if not occupied:
                    candidate.parent.mkdir(parents=True, exist_ok=True)
                    candidate.write_text("other process", encoding="utf-8")
                    occupied.append(candidate)
                    raise FileExistsError(str(candidate))
                return original_open(path, flags, mode)

            with patch("snapkeep.archive.os.open", side_effect=create_collision_then_open):
                created = create_archive(
                    source, [file_path], destination, timestamp=self.timestamp
                )

            self.assertNotEqual(created, occupied[0])
            self.assertEqual(occupied[0].read_text(encoding="utf-8"), "other process")
            verify_archive(created)

    def test_creation_failure_removes_only_owned_partial_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            destination = root / "archive"
            file_path.unlink()

            with self.assertRaises(ArchiveError):
                create_archive(
                    source, [file_path], destination, timestamp=self.timestamp
                )

            self.assertEqual(list(destination.iterdir()), [])

    def test_cleanup_does_not_remove_replacement_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            destination = root / "archive"

            def replace_and_fail(archive_path):
                replacement = archive_path.with_suffix(".replacement")
                replacement.write_text("created by another process", encoding="utf-8")
                replacement.replace(archive_path)
                raise ArchiveVerificationError("simulated verification failure")

            with patch(
                "snapkeep.archive.verify_archive",
                side_effect=replace_and_fail,
            ):
                with self.assertRaises(ArchiveVerificationError):
                    create_archive(
                        source, [file_path], destination, timestamp=self.timestamp
                    )

            archive_path = destination / build_archive_name(
                source, timestamp=self.timestamp
            )
            self.assertEqual(
                archive_path.read_text(encoding="utf-8"),
                "created by another process",
            )

    def test_verification_failure_removes_partial_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, file_path = self._source(root)
            destination = root / "archive"

            with patch(
                "snapkeep.archive.verify_archive",
                side_effect=ArchiveVerificationError("simulated verification failure"),
            ):
                with self.assertRaises(ArchiveVerificationError):
                    create_archive(
                        source, [file_path], destination, timestamp=self.timestamp
                    )

            self.assertEqual(list(destination.iterdir()), [])


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
            archive_path.write_text("not a zip archive", encoding="utf-8")
            with self.assertRaises(ArchiveVerificationError):
                verify_archive(archive_path)


class ChooseArchivePathTests(unittest.TestCase):
    def test_returns_original_name_when_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = choose_archive_path(Path(temp_dir), "project_BACKUP.zip")
            self.assertEqual(path.name, "project_BACKUP.zip")

    def test_adds_counter_when_archive_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir)
            first = destination / "project_BACKUP.zip"
            first.write_text("existing", encoding="utf-8")
            path = choose_archive_path(destination, first.name)
            self.assertEqual(path.name, "project_BACKUP-1.zip")

    def test_increments_counter_until_name_is_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir)
            base = "project_BACKUP.zip"
            (destination / base).write_text("existing", encoding="utf-8")
            (destination / "project_BACKUP-1.zip").write_text(
                "existing", encoding="utf-8"
            )
            path = choose_archive_path(destination, base)
            self.assertEqual(path.name, "project_BACKUP-2.zip")


if __name__ == "__main__":
    unittest.main()
