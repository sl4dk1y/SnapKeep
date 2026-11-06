from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

from snapkeep.errors import IgnoreFileError


def load_ignore_patterns(
    ignore_file: Path,
    *,
    missing_ok: bool = True,
) -> list[str]:
    """Load active patterns from a .backupignore file."""
    patterns: list[str] = []

    try:
        with ignore_file.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue

                patterns.append(line)
    except FileNotFoundError:
        if missing_ok:
            return []
        raise IgnoreFileError(
            f"ignore file does not exist: {ignore_file}"
        )
    except (OSError, UnicodeError) as error:
        raise IgnoreFileError(
            f"could not read ignore file {ignore_file}: {error}"
        ) from error

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
