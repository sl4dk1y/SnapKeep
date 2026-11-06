import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-release-tag.py"


class ReleaseTagTests(unittest.TestCase):
    def run_validator(self, tag):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), tag],
            cwd=str(ROOT), text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )

    def test_current_pep440_tag_matches_project_version(self):
        result = self.run_validator("v0.1.0a2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("matches project version 0.1.0a2", result.stdout)

    def test_historical_alpha_tag_normalizes_to_project_version(self):
        result = self.run_validator("v0.1.0-alpha.2")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mismatched_tag_is_rejected(self):
        result = self.run_validator("v0.1.0a1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not match project version", result.stderr)

    def test_tag_without_v_prefix_is_rejected(self):
        result = self.run_validator("0.1.0a2")
        self.assertEqual(result.returncode, 1)
        self.assertIn("tag must be", result.stderr)


if __name__ == "__main__":
    unittest.main()
