from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable


def load_ignore_patterns(ignore_file: Path) -> list[str]:
    """Load active patterns from a .backupignore file."""
    if not ignore_file.exists():
        return []

    patterns: list[str] = []

    with ignore_file.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            patterns.append(line)

    return patterns


def is_ignored(relative_path: Path, patterns: Iterable[str]) -> bool:
    """Return True when a relative path matches an ignore pattern."""
    path = relative_path.as_posix()
    parts = relative_path.parts

    for pattern in patterns:
        pattern = pattern.replace("\\", "/")

        if pattern.endswith("/"):
            directory_pattern = pattern.rstrip("/")

            if "/" in directory_pattern:
                prefixes = [
                    "/".join(parts[:index])
                    for index in range(1, len(parts) + 1)
                ]

                if any(fnmatch(prefix, directory_pattern) for prefix in prefixes):
                    return True
            else:
                if any(fnmatch(part, directory_pattern) for part in parts):
                    return True

            continue

        if "/" in pattern:
            if fnmatch(path, pattern):
                return True
        else:
            if any(fnmatch(part, pattern) for part in parts):
                return True

    return False
