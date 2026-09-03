import argparse
from pathlib import Path


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

    print(f"Source:      {source}")
    print(f"Destination: {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
