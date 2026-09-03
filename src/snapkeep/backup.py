from pathlib import Path
from typing import Iterable

from snapkeep.ignore import is_ignored


def collect_files(source: Path, patterns: Iterable[str]) -> list[Path]:
    """Collect files that should be included in a snapshot."""
    files: list[Path] = []

    for path in source.rglob("*"):
        relative_path = path.relative_to(source)

        if is_ignored(relative_path, patterns):
            continue

        if path.is_file():
            files.append(path)

    return sorted(files, key=lambda item: item.as_posix())
