import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from snapkeep import __version__
from snapkeep.archive import create_archive, verify_archive
from snapkeep.backup import collect_files
from snapkeep.errors import SnapKeepError
from snapkeep.ignore import load_ignore_patterns
from snapkeep.security import (
    DEFAULT_EXCLUDE_PATTERNS,
    SECRET_EXCLUDE_PATTERNS,
)

def verify_existing_archive(archive_arg: str) -> int:
    archive_path = Path(archive_arg).expanduser().resolve()

    if not archive_path.exists():
        print(
            f"snapkeep: error: archive does not exist: {archive_path}",
            file=sys.stderr,
        )
        return 1

    if not archive_path.is_file():
        print(
            f"snapkeep: error: archive is not a file: {archive_path}",
            file=sys.stderr,
        )
        return 1

    try:
        verify_archive(archive_path)
    except SnapKeepError as error:
        print(f"snapkeep: error: {error}", file=sys.stderr)
        return 1

    print(f"Archive:      {archive_path}")
    print("Verification: OK")

    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snapkeep",
        description="Create safe snapshots of project directories.",
    )

    parser.add_argument(
        "source",
        nargs="?",
        default=".",
        help="Directory to snapshot (default: current directory).",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Directory where snapshots will be stored.",
    )

    parser.add_argument(
        "-i",
        "--ignore-file",
        type=Path,
        help="Use a custom ignore file instead of SOURCE/.backupignore.",
    )

    parser.add_argument(
        "-n",
        "--name",
        help="Use a custom name for the snapshot archive.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be included without creating a snapshot.",
    )

    parser.add_argument(
        "--include-secrets",
        action="store_true",
        help="Include files normally excluded as potential secrets.",
    )

    parser.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Disable SnapKeep built-in technical exclusions.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"SnapKeep {__version__}",
    )

    return parser

def main(argv: Optional[Sequence[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "verify":
        if len(argv) != 2:
            print(
                "usage: snapkeep verify ARCHIVE",
                file=sys.stderr,
            )
            return 2

        return verify_existing_archive(argv[1])

    parser = build_parser()
    args = parser.parse_args(argv)

    source = Path(args.source).expanduser().resolve()

    if not source.exists():
        parser.error(f"source does not exist: {source}")

    if not source.is_dir():
        parser.error(f"source is not a directory: {source}")

    if args.name is not None:
        if not args.name.strip():
            parser.error("snapshot name cannot be empty")

        if "/" in args.name or "\\" in args.name:
            parser.error("snapshot name cannot contain path separators")

    if args.output is None:
        output = source.parent / "archive"
    else:
        output = args.output.expanduser().resolve()

    patterns = []

    if not args.no_default_excludes:
        patterns.extend(DEFAULT_EXCLUDE_PATTERNS)

    if args.ignore_file is None:
        ignore_file = source / ".backupignore"
    else:
        ignore_file = args.ignore_file.expanduser().resolve()

        if not ignore_file.exists():
            parser.error(f"ignore file does not exist: {ignore_file}")

        if not ignore_file.is_file():
            parser.error(f"ignore file is not a file: {ignore_file}")

    patterns.extend(load_ignore_patterns(ignore_file))

    secret_patterns = []

    if not args.include_secrets:
        secret_patterns.extend(SECRET_EXCLUDE_PATTERNS)

    files = collect_files(
        source,
        patterns,
        secret_patterns=secret_patterns,
        excluded_directory=output,
    )

    print(f"Source:      {source}")
    print(f"Destination: {output}")

    if args.include_secrets:
        print("Warning: secret protection is disabled.")

    if args.no_default_excludes:
        print("Warning: built-in technical exclusions are disabled.")

    if args.dry_run:
        print()
        print("Files to include:")

        for path in files:
            print(f"  {path.relative_to(source).as_posix()}")

        print()
        print(f"Total files: {len(files)}")
        print("Dry run: no snapshot was created.")
        return 0

    try:
        archive_path = create_archive(
            source,
            files,
            output,
            name=args.name,
        )
    except SnapKeepError as error:
        print(f"snapkeep: error: {error}", file=sys.stderr)
        return 1

    print()
    print(f"Snapshot created: {archive_path}")
    print(f"Files archived:   {len(files)}")
    print("Verification:     OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
