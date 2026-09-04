import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from snapkeep import __version__
from snapkeep.cli import main
from snapkeep.errors import ArchiveError


class CliTests(unittest.TestCase):
    def test_dry_run_does_not_create_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            output = root / "archive"

            source.mkdir()
            (source / "file.txt").write_text(
                "hello",
                encoding="utf-8",
            )

            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(source),
                        "--output",
                        str(output),
                        "--dry-run",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertFalse(output.exists())
            self.assertIn("file.txt", stdout.getvalue())
            self.assertIn(
                "Dry run: no snapshot was created.",
                stdout.getvalue(),
            )

    def test_creates_snapshot_successfully(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            output = root / "archive"

            source.mkdir()
            (source / "file.txt").write_text(
                "hello",
                encoding="utf-8",
            )

            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(source),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                len(list(output.glob("*.zip"))),
                1,
            )
            self.assertIn(
                "Verification:     OK",
                stdout.getvalue(),
            )

    def test_archive_error_returns_exit_code_one_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "project"
            source.mkdir()

            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch(
                "snapkeep.cli.create_archive",
                side_effect=ArchiveError("simulated failure"),
            ):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main([str(source)])

            error_output = stderr.getvalue()

            self.assertEqual(exit_code, 1)
            self.assertIn(
                "snapkeep: error: simulated failure",
                error_output,
            )
            self.assertNotIn("Traceback", error_output)

    def test_missing_source_uses_argparse_exit_code_two(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as context:
                main(["/path/that/does/not/exist"])

        self.assertEqual(context.exception.code, 2)
        self.assertIn(
            "source does not exist",
            stderr.getvalue(),
        )

    def test_version_reports_package_version(self):
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as context:
                main(["--version"])

        self.assertEqual(context.exception.code, 0)
        self.assertEqual(
            stdout.getvalue().strip(),
            f"SnapKeep {__version__}",
        )

    def test_custom_ignore_file_replaces_default_backupignore(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            source.mkdir()

            (source / "keep.txt").write_text(
                "keep\n",
                encoding="utf-8",
            )
            (source / "remove.txt").write_text(
                "remove\n",
                encoding="utf-8",
            )
            (source / ".backupignore").write_text(
                "keep.txt\n",
                encoding="utf-8",
            )

            custom_ignore = root / "custom.ignore"
            custom_ignore.write_text(
                "remove.txt\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(source),
                        "--ignore-file",
                        str(custom_ignore),
                        "--dry-run",
                    ]
                )

            output = stdout.getvalue()

            self.assertEqual(exit_code, 0)
            self.assertIn("keep.txt", output)
            self.assertIn(".backupignore", output)
            self.assertNotIn("  remove.txt", output)

    def test_missing_custom_ignore_file_uses_argparse_exit_code_two(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "project"
            source.mkdir()

            missing_ignore = Path(temp_dir) / "missing.ignore"

            stderr = io.StringIO()

            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main(
                        [
                            str(source),
                            "--ignore-file",
                            str(missing_ignore),
                            "--dry-run",
                        ]
                    )

            self.assertEqual(context.exception.code, 2)
            self.assertIn(
                "ignore file does not exist",
                stderr.getvalue(),
            )

    def test_custom_ignore_path_must_be_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            source.mkdir()

            stderr = io.StringIO()

            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main(
                        [
                            str(source),
                            "--ignore-file",
                            str(root),
                            "--dry-run",
                        ]
                    )

            self.assertEqual(context.exception.code, 2)
            self.assertIn(
                "ignore file is not a file",
                stderr.getvalue(),
            )

    def test_empty_snapshot_name_uses_argparse_exit_code_two(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "project"
            source.mkdir()

            stderr = io.StringIO()

            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main(
                        [
                            str(source),
                            "--name",
                            "",
                            "--dry-run",
                        ]
                    )

            self.assertEqual(context.exception.code, 2)
            self.assertIn(
                "snapshot name cannot be empty",
                stderr.getvalue(),
            )

    def test_snapshot_name_cannot_contain_forward_slash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "project"
            source.mkdir()

            stderr = io.StringIO()

            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main(
                        [
                            str(source),
                            "--name",
                            "foo/bar",
                            "--dry-run",
                        ]
                    )

            self.assertEqual(context.exception.code, 2)
            self.assertIn(
                "snapshot name cannot contain path separators",
                stderr.getvalue(),
            )

    def test_snapshot_name_cannot_contain_backslash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "project"
            source.mkdir()

            stderr = io.StringIO()

            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main(
                        [
                            str(source),
                            "--name",
                            r"foo\bar",
                            "--dry-run",
                        ]
                    )

            self.assertEqual(context.exception.code, 2)
            self.assertIn(
                "snapshot name cannot contain path separators",
                stderr.getvalue(),
            )

    def test_creates_snapshot_with_custom_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            output = root / "archive"

            source.mkdir()
            (source / "file.txt").write_text(
                "hello",
                encoding="utf-8",
            )

            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(source),
                        "--output",
                        str(output),
                        "--name",
                        "before-refactor",
                    ]
                )

            archives = list(
                output.glob("before-refactor_BACKUP_*.zip")
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(archives), 1)
            self.assertIn(
                "Verification:     OK",
                stdout.getvalue(),
            )

    def test_verify_existing_archive_successfully(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "valid.zip"

            with ZipFile(archive_path, "w") as archive:
                archive.writestr("file.txt", "hello")

            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(["verify", str(archive_path)])

            self.assertEqual(exit_code, 0)
            self.assertIn(
                "Verification: OK",
                stdout.getvalue(),
            )

    def test_verify_broken_archive_returns_exit_code_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "broken.zip"
            archive_path.write_text(
                "not a zip archive",
                encoding="utf-8",
            )

            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(["verify", str(archive_path)])

            self.assertEqual(exit_code, 1)
            self.assertIn(
                "archive verification failed",
                stderr.getvalue(),
            )
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_verify_missing_archive_returns_exit_code_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "missing.zip"
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(["verify", str(archive_path)])

            self.assertEqual(exit_code, 1)
            self.assertIn(
                "archive does not exist",
                stderr.getvalue(),
            )

    def test_verify_without_archive_returns_exit_code_two(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = main(["verify"])

        self.assertEqual(exit_code, 2)
        self.assertIn(
            "usage: snapkeep verify ARCHIVE",
            stderr.getvalue(),
        )

    def test_verify_directory_returns_exit_code_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(["verify", temp_dir])

            self.assertEqual(exit_code, 1)
            self.assertIn(
                "archive is not a file",
                stderr.getvalue(),
            )

if __name__ == "__main__":
    unittest.main()
