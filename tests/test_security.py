import unittest

from snapkeep.security import (
    DEFAULT_EXCLUDE_PATTERNS,
    SECRET_EXCLUDE_PATTERNS,
    build_default_patterns,
)


class BuildDefaultPatternsTests(unittest.TestCase):
    def test_defaults_include_technical_exclusions(self):
        patterns = build_default_patterns()

        for pattern in DEFAULT_EXCLUDE_PATTERNS:
            self.assertIn(pattern, patterns)

    def test_defaults_include_secret_exclusions(self):
        patterns = build_default_patterns()

        for pattern in SECRET_EXCLUDE_PATTERNS:
            self.assertIn(pattern, patterns)

    def test_include_secrets_disables_only_secret_exclusions(self):
        patterns = build_default_patterns(include_secrets=True)

        for pattern in DEFAULT_EXCLUDE_PATTERNS:
            self.assertIn(pattern, patterns)

        for pattern in SECRET_EXCLUDE_PATTERNS:
            self.assertNotIn(pattern, patterns)


if __name__ == "__main__":
    unittest.main()


class SecretAllowPatternsTests(unittest.TestCase):
    def test_env_example_is_allowed(self):
        from pathlib import Path
        from snapkeep.security import is_allowed_secret_example

        self.assertTrue(
            is_allowed_secret_example(Path(".env.example"))
        )

    def test_nested_env_sample_is_allowed(self):
        from pathlib import Path
        from snapkeep.security import is_allowed_secret_example

        self.assertTrue(
            is_allowed_secret_example(Path("config/.env.sample"))
        )

    def test_real_env_is_not_allowlisted(self):
        from pathlib import Path
        from snapkeep.security import is_allowed_secret_example

        self.assertFalse(
            is_allowed_secret_example(Path(".env"))
        )
