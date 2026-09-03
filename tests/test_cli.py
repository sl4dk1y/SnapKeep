import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
