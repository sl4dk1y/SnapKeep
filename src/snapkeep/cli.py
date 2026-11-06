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


def verify_existing_archive(archive_name: str) -> int:
    archive_path = Path(archive_name).expanduser()

    try:
        if not archive_path.exists():
            raise OSError(f"archive does not exist: {archive_path}")

        if not archive_path.is_file():
            raise OSError(f"archive is not a file: {archive_path}")

        verify_archive(archive_path)
    except SnapKeepError as error:
        print(f"snapkeep: error: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError) as error:
        print(f"snapkeep: error: could not access archive: {error}", file=sys.stderr)
        return 1

    print(f"Archive:      {archive_path}")
    print("Verification: OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snapkeep",
        description="Create a timestamped ZIP snapshot of a project directory.",
    )

    parser.add_argument(
        "source",
        nargs="?",
        default=".",
        help="source project directory (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="archive destination directory (default: sibling archive directory)",
    )
    parser.add_argument(
        "--name",
        help="custom snapshot name",
    )
    parser.add_argument(
        "--ignore-file",
        type=Path,
        help="use a custom ignore file instead of SOURCE/.backupignore",
    )
    parser.add_argument(
        "--include-secrets",
        action="store_true",
        help="include files normally excluded as secrets",
    )
    parser.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="disable built-in technical exclusions",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show files that would be archived without creating a ZIP file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"SnapKeep {__version__}",
    )

    return parser


def _report_operational_error(error: BaseException) -> int:
    print(f"snapkeep: error: {error}", file=sys.stderr)
    return 1


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

    try:
        source = Path(args.source).expanduser().resolve(strict=True)
        source_stat = source.stat()
    except FileNotFoundError:
        parser.error(f"source does not exist: {Path(args.source).expanduser()}")
    except (OSError, RuntimeError, ValueError) as error:
        return _report_operational_error(
            f"could not access source directory: {error}"
        )

    if not stat_is_directory(source_stat.st_mode):
        parser.error(f"source is not a directory: {source}")

    if args.name is not None:
        if not args.name.strip():
            parser.error("snapshot name cannot be empty")

        if "/" in args.name or "\\" in args.name:
            parser.error("snapshot name cannot contain path separators")

    try:
        if args.output is None:
            output = source.parent / "archive"
        else:
            output = args.output.expanduser().resolve()
    except (OSError, RuntimeError, ValueError) as error:
        return _report_operational_error(
            f"could not access output destination: {error}"
        )

    if args.no_default_excludes:
        patterns = []
    else:
        patterns = list(DEFAULT_EXCLUDE_PATTERNS)

    if args.ignore_file is None:
        ignore_file = source / ".backupignore"
        missing_ignore_ok = True
    else:
        try:
            ignore_file = args.ignore_file.expanduser().resolve(strict=True)
            ignore_stat = ignore_file.stat()
        except FileNotFoundError:
            parser.error(
                f"ignore file does not exist: {args.ignore_file.expanduser()}"
            )
        except (OSError, RuntimeError, ValueError) as error:
            return _report_operational_error(
                f"could not access ignore file: {error}"
            )

        if not stat_is_regular_file(ignore_stat.st_mode):
            parser.error(f"ignore file is not a file: {ignore_file}")

        missing_ignore_ok = False

    try:
        patterns.extend(
            load_ignore_patterns(
                ignore_file,
                missing_ok=missing_ignore_ok,
            )
        )
        secret_patterns = (
            [] if args.include_secrets else list(SECRET_EXCLUDE_PATTERNS)
        )
        files = collect_files(
            source,
            patterns,
            secret_patterns=secret_patterns,
            excluded_directory=output,
        )
    except SnapKeepError as error:
        return _report_operational_error(error)
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        return _report_operational_error(
            f"could not collect project files: {error}"
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


def stat_is_directory(mode: int) -> bool:
    import stat
    return stat.S_ISDIR(mode)


def stat_is_regular_file(mode: int) -> bool:
    import stat
    return stat.S_ISREG(mode)
