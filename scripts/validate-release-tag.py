#!/usr/bin/env python3
"""Reject a release tag that does not identify the package version."""
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^(\d+\.\d+\.\d+)(?:(a|b|rc)(\d+))?$")
TAG_RE = re.compile(
    r"^v(\d+\.\d+\.\d+)(?:(?:-?(alpha|beta|rc)\.?)(\d+)|(a|b|rc)(\d+))?$"
)


def canonical_tag_version(tag):
    match = TAG_RE.fullmatch(tag)
    if match is None:
        raise ValueError(
            "tag must be vMAJOR.MINOR.PATCH with optional aN, bN, rcN, "
            "or the legacy -alpha.N/-beta.N form"
        )
    release, long_name, long_number, short_name, short_number = match.groups()
    prerelease = long_name or short_name
    number = long_number or short_number
    if prerelease is None:
        return release
    marker = {"alpha": "a", "beta": "b", "a": "a", "b": "b", "rc": "rc"}[
        prerelease
    ]
    return f"{release}{marker}{number}"


def main(argv):
    if len(argv) != 2:
        print("usage: validate-release-tag.py TAG", file=sys.stderr)
        return 2

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
    if match is None:
        print("release validation: project version is missing", file=sys.stderr)
        return 1

    version = match.group(1)
    if VERSION_RE.fullmatch(version) is None:
        print(
            f"release validation: unsupported project version format: {version}",
            file=sys.stderr,
        )
        return 1
    try:
        tag_version = canonical_tag_version(argv[1])
    except ValueError as error:
        print(f"release validation: {error}", file=sys.stderr)
        return 1

    if tag_version != version:
        print(
            f"release validation: tag {argv[1]} does not match project version {version}",
            file=sys.stderr,
        )
        return 1
    print(f"release validation: {argv[1]} matches project version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
