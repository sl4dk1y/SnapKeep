import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "integrations/macos/snapkeep-finder.sh"


@unittest.skipUnless(os.name == "posix" and sys.platform == "darwin",
                     "Finder wrapper tests require macOS")
class FinderWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.snapkeep_log = self.root / "snapkeep.log"
        self.fake_snapkeep = self.bin_dir / "snapkeep"
        self.fake_snapkeep.write_text(
            "#!/bin/bash\n"
            "printf '%s\\n' \"$1\" >> \"$SNAPKEEP_LOG\"\n"
            "if [[ \"$1\" == \"${FAIL_PATH:-}\" ]]; then\n"
            "  printf 'snapkeep: error: simulated failure\\n'\n"
            "  exit 7\n"
            "fi\n"
            "printf 'Snapshot created: test.zip\\n'\n",
            encoding="utf-8",
        )
        self.fake_snapkeep.chmod(0o755)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run(self, *paths, fail_path=None, snapkeep_bin=None, status_mode=False):
        env = os.environ.copy()
        env.update({
            "HOME": str(self.root),
            "PATH": str(self.bin_dir) + ":/usr/bin:/bin",
            "SNAPKEEP_LOG": str(self.snapkeep_log),
        })
        if fail_path is not None:
            env["FAIL_PATH"] = str(Path(fail_path).resolve())
        if snapkeep_bin is not None:
            env["SNAPKEEP_BIN"] = str(snapkeep_bin)
        if status_mode:
            env["SNAPKEEP_FINDER_STATUS_MODE"] = "1"
        return subprocess.run(
            ["/bin/bash", str(WRAPPER), *(str(path) for path in paths)],
            env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )

    def test_processes_multiple_unique_projects_and_reports_success(self):
        first = self.root / "first project"
        second = self.root / "other parent" / "second"
        first.mkdir()
        second.mkdir(parents=True)
        result = self._run(first, first, second)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.snapkeep_log.read_text(encoding="utf-8").splitlines(),
            [str(first.resolve()), str(second.resolve())],
        )
        self.assertIn("2 project snapshot(s) were created and verified", result.stdout)
        self.assertIn("first project: snapshot created and ZIP verified", result.stdout)
        self.assertIn("second: snapshot created and ZIP verified", result.stdout)

    def test_reports_individual_failure_without_claiming_complete_success(self):
        good = self.root / "good"
        bad = self.root / "bad"
        good.mkdir()
        bad.mkdir()
        result = self._run(good, bad, fail_path=bad)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.snapkeep_log.read_text(encoding="utf-8").splitlines(),
            [str(good.resolve()), str(bad.resolve())],
        )
        self.assertIn("1 of 2 selected folder(s) failed", result.stdout)
        self.assertIn("good: snapshot created and ZIP verified", result.stdout)
        self.assertIn("bad: FAILED — snapkeep: error: simulated failure", result.stdout)
        self.assertIn("simulated failure", result.stderr)

    def test_rejects_non_directory_selection(self):
        selected_file = self.root / "file.txt"
        selected_file.write_text("x", encoding="utf-8")
        result = self._run(selected_file)
        self.assertEqual(result.returncode, 0)
        self.assertIn("1 of 1 selected folder(s) failed", result.stdout)
        self.assertIn("file.txt: FAILED — selected item is not a folder", result.stdout)
        self.assertFalse(self.snapkeep_log.exists())

    def test_missing_snapkeep_executable_reports_failure(self):
        project = self.root / "project"
        project.mkdir()
        result = self._run(project, snapkeep_bin=self.root / "missing-snapkeep")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Snapshot failed: SnapKeep CLI was not found", result.stdout)

    def test_no_selected_paths_reports_failure(self):
        result = self._run()
        self.assertEqual(result.returncode, 0)
        self.assertIn("Snapshot failed: Select one or more project folders", result.stdout)

    def test_status_mode_returns_nonzero_for_project_failure(self):
        project = self.root / "failure"
        project.mkdir()
        result = self._run(project, fail_path=project, status_mode=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("1 of 1 selected folder(s) failed", result.stdout)

    def test_status_mode_uses_127_when_cli_is_missing(self):
        project = self.root / "project"
        project.mkdir()
        result = self._run(project, snapkeep_bin=self.root / "missing", status_mode=True)
        self.assertEqual(result.returncode, 127)

    def test_status_mode_uses_2_when_no_paths_are_selected(self):
        result = self._run(status_mode=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
