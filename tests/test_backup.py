import tempfile
import unittest
from unittest.mock import patch
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

    def test_prunes_fully_ignored_directory_trees(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "keep.txt").write_text("keep", encoding="utf-8")
            for dirname in (".git", ".venv", "build", ".aws"):
                nested = source / dirname / "nested"
                nested.mkdir(parents=True)
                (nested / "secret.txt").write_text("skip", encoding="utf-8")

            original_scandir = __import__("os").scandir
            visited = []

            def recording_scandir(path):
                path = Path(path)
                visited.append(path.relative_to(source).as_posix() if path != source else ".")
                return original_scandir(path)

            with patch("snapkeep.backup.os.scandir", side_effect=recording_scandir):
                files = collect_files(
                    source,
                    [".git/", ".venv/", "build/", ".aws/"],
                    secret_patterns=[".aws/"],
                )

            self.assertEqual([p.relative_to(source).as_posix() for p in files], ["keep.txt"])
            self.assertEqual(visited, ["."])

    def test_nested_path_exclusions_prune_matched_subtree_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            excluded = source / "packages" / "vendor" / "nested"
            excluded.mkdir(parents=True)
            (excluded / "secret.py").write_text("skip", encoding="utf-8")
            permitted = source / "packages" / "app"
            permitted.mkdir()
            (permitted / "main.py").write_text("keep", encoding="utf-8")

            original_scandir = __import__("os").scandir
            visited = []

            def recording_scandir(path):
                path = Path(path)
                visited.append(path.relative_to(source).as_posix() if path != source else ".")
                return original_scandir(path)

            with patch("snapkeep.backup.os.scandir", side_effect=recording_scandir):
                files = collect_files(source, ["packages/vendor/"])

            self.assertEqual(
                [p.relative_to(source).as_posix() for p in files],
                ["packages/app/main.py"],
            )
            self.assertNotIn("packages/vendor", visited)
            self.assertNotIn("packages/vendor/nested", visited)

    def test_file_pattern_does_not_prune_directory_with_permitted_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            cache = source / "build"
            cache.mkdir()
            (cache / "keep.txt").write_text("keep", encoding="utf-8")
            (cache / "drop.pyc").write_text("skip", encoding="utf-8")

            files = collect_files(source, ["*.pyc"])

            self.assertEqual([p.relative_to(source).as_posix() for p in files], ["build/keep.txt"])

class OutputExclusionTests(unittest.TestCase):
    def test_output_directory_inside_source_is_excluded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)

            (source / "keep.txt").write_text(
                "keep",
                encoding="utf-8",
            )

            output = source / "archive"
            output.mkdir()
            (output / "old-snapshot.zip").write_text(
                "old archive",
                encoding="utf-8",
            )

            files = collect_files(
                source,
                [],
                excluded_directory=output,
            )

            relative_files = [
                path.relative_to(source).as_posix()
                for path in files
            ]

            self.assertEqual(relative_files, ["keep.txt"])

class SymlinkCollectionTests(unittest.TestCase):
    def test_symlink_to_file_is_not_collected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            outside = root / "outside.txt"

            source.mkdir()
            outside.write_text(
                "secret outside project",
                encoding="utf-8",
            )

            link = source / "outside-link.txt"
            link.symlink_to(outside)

            files = collect_files(
                source,
                [],
            )

            self.assertNotIn(link, files)

    def test_symlink_to_directory_is_not_traversed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "project"
            outside = root / "outside"

            source.mkdir()
            outside.mkdir()

            (outside / "secret.txt").write_text(
                "secret outside project",
                encoding="utf-8",
            )

            link = source / "outside-dir"
            link.symlink_to(
                outside,
                target_is_directory=True,
            )

            files = collect_files(
                source,
                [],
            )

            relative_files = [
                path.relative_to(source).as_posix()
                for path in files
            ]

            self.assertNotIn(
                "outside-dir/secret.txt",
                relative_files,
            )

if __name__ == "__main__":
    unittest.main()
class SecretExampleCollectionTests(unittest.TestCase):
    def test_secret_example_is_included(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)

            (source / ".env").write_text("SECRET=value", encoding="utf-8")
            (source / ".env.example").write_text(
                "SECRET=",
                encoding="utf-8",
            )

            files = collect_files(
                source,
                [],
                secret_patterns=[".env", ".env.*"],
            )

            relative_files = [
                path.relative_to(source).as_posix()
                for path in files
            ]

            self.assertEqual(relative_files, [".env.example"])

    def test_user_ignore_overrides_secret_example_allowlist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)

            (source / ".env.example").write_text(
                "SECRET=",
                encoding="utf-8",
            )

            files = collect_files(
                source,
                [".env.example"],
                secret_patterns=[".env", ".env.*"],
            )

            self.assertEqual(files, [])

    def test_technical_exclusion_overrides_secret_example_allowlist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)

            git_dir = source / ".git"
            git_dir.mkdir()
            (git_dir / ".env.example").write_text(
                "SECRET=",
                encoding="utf-8",
            )

            files = collect_files(
                source,
                [".git/"],
                secret_patterns=[".env", ".env.*"],
            )

            self.assertEqual(files, [])


class TraversalFailureTests(unittest.TestCase):
    def test_permission_error_during_directory_traversal_propagates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            with patch(
                "snapkeep.backup.os.scandir",
                side_effect=PermissionError("permission denied"),
            ):
                with self.assertRaises(PermissionError):
                    collect_files(source, [])

    def test_disappearing_file_during_collection_is_reported(self):
        class DisappearingEntry:
            def __init__(self, path):
                self.path = str(path)

            def stat(self, follow_symlinks=False):
                raise FileNotFoundError("file disappeared")

        class ScandirResult:
            def __init__(self, entry):
                self.entry = entry

            def __enter__(self):
                return [self.entry]

            def __exit__(self, exc_type, exc_value, traceback):
                return False

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            path = source / "vanishing.txt"
            path.write_text("data", encoding="utf-8")
            context = ScandirResult(DisappearingEntry(path))
            with patch("snapkeep.backup.os.scandir", return_value=context):
                with self.assertRaises(FileNotFoundError):
                    collect_files(source, [])
