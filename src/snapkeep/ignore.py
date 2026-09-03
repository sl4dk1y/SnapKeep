from pathlib import Path


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
