import os
import stat
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
    """Collect regular files, failing on traversal errors and skipping links."""
    files: list[Path] = []
    patterns = tuple(patterns)
    secret_patterns = tuple(secret_patterns)
    excluded_directory_resolved = (
        excluded_directory.resolve()
        if excluded_directory is not None
        else None
    )

    def visit(directory: Path) -> None:
        with os.scandir(str(directory)) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative_path = path.relative_to(source)

                try:
                    metadata = entry.stat(follow_symlinks=False)
                except OSError:
                    # A disappearing or unreadable entry must not produce an
                    # apparently complete snapshot.
                    raise

                if stat.S_ISLNK(metadata.st_mode):
                    continue

                if excluded_directory_resolved is not None:
                    try:
                        path.resolve(strict=True).relative_to(
                            excluded_directory_resolved
                        )
                    except ValueError:
                        pass
                    else:
                        continue

                ignored = is_ignored(relative_path, patterns)
                secret_ignored = (
                    not is_allowed_secret_example(relative_path)
                    and is_ignored(relative_path, secret_patterns)
                )

                if stat.S_ISDIR(metadata.st_mode):
                    # A directory-wide match also matches every descendant
                    # under is_ignored's path/prefix rules, so it is safe to
                    # prune that tree. File-only patterns (for example
                    # ``*.pyc``) do not match the directory and still allow
                    # traversal to collect any permitted children.
                    if ignored or secret_ignored:
                        continue
                    visit(path)
                elif (
                    stat.S_ISREG(metadata.st_mode)
                    and not ignored
                    and not secret_ignored
                ):
                    files.append(path)

    visit(source)
    return sorted(files, key=lambda item: item.as_posix())
