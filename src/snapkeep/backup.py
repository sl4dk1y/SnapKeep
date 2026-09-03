from pathlib import Path
from typing import Iterable, Optional

from snapkeep.ignore import is_ignored
from snapkeep.security import is_allowed_secret_example


def collect_files(
    source: Path,
    patterns: Iterable[str],
    *,
    secret_patterns: Iterable[str] = (),
    excluded_directory: Optional[Path] = None,
) -> list[Path]:
    """Collect files that should be included in a snapshot."""
    files: list[Path] = []

    excluded_directory_resolved = None

    if excluded_directory is not None:
        excluded_directory_resolved = excluded_directory.resolve()

    for path in source.rglob("*"):
        if path.is_symlink():
            continue

        if excluded_directory_resolved is not None:
            try:
                path.resolve().relative_to(excluded_directory_resolved)
            except ValueError:
                pass
            else:
                continue

        relative_path = path.relative_to(source)

        if is_ignored(relative_path, patterns):
            continue

        if (
            not is_allowed_secret_example(relative_path)
            and is_ignored(relative_path, secret_patterns)
        ):
            continue

        if path.is_file():
            files.append(path)

    return sorted(files, key=lambda item: item.as_posix())
