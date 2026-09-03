import argparse
from pathlib import Path

from snapkeep.backup import collect_files
from snapkeep.ignore import load_ignore_patterns


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
        "--dry-run",
        action="store_true",
        help="Show which files would be included without creating a snapshot.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="SnapKeep 0.1.0",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()

    if not source.exists():
        parser.error(f"source does not exist: {source}")

    if not source.is_dir():
        parser.error(f"source is not a directory: {source}")

    if args.output is None:
        output = source.parent / "archive"
    else:
        output = args.output.expanduser().resolve()

    ignore_file = source / ".backupignore"
    patterns = load_ignore_patterns(ignore_file)
    files = collect_files(source, patterns)

    print(f"Source:      {source}")
    print(f"Destination: {output}")

    if args.dry_run:
        print()
        print("Files to include:")

        for path in files:
            print(f"  {path.relative_to(source).as_posix()}")

        print()
        print(f"Total files: {len(files)}")
        print("Dry run: no snapshot was created.")
        return 0

    print()
    print("Snapshot creation is not implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
