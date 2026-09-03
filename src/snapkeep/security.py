from fnmatch import fnmatch
from pathlib import Path
from typing import List


DEFAULT_EXCLUDE_PATTERNS: List[str] = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "build/",
    "dist/",
    "*.egg-info/",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.zip",
]


SECRET_EXCLUDE_PATTERNS: List[str] = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_ed25519",
    ".aws/credentials",
]


SECRET_ALLOW_PATTERNS: List[str] = [
    ".env.example",
    ".env.sample",
    ".env.template",
]


def build_default_patterns(
    include_secrets: bool = False,
) -> List[str]:
    """Return built-in exclusion patterns for a snapshot."""
    patterns = list(DEFAULT_EXCLUDE_PATTERNS)

    if not include_secrets:
        patterns.extend(SECRET_EXCLUDE_PATTERNS)

    return patterns


def is_allowed_secret_example(relative_path: Path) -> bool:
    """Return True for secret-template files that are safe to include."""
    path = relative_path.as_posix()
    name = relative_path.name

    return any(
        fnmatch(path, pattern) or fnmatch(name, pattern)
        for pattern in SECRET_ALLOW_PATTERNS
    )
