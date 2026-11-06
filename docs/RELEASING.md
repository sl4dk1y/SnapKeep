# Release preparation

SnapKeep releases are published from a GitHub Release. The repository workflow
builds distributions from the release tag, checks the tag against the version
in pyproject.toml, checks package metadata, and publishes through PyPI Trusted
Publishing. It does not run from workflow_dispatch.

## Before a release

1. Run the validation commands listed in the README.
2. Update project.version in pyproject.toml.
3. Use a version such as MAJOR.MINOR.PATCH, optionally with a PEP 440
   prerelease suffix such as a2, b1, or rc1.
4. Create a matching immutable tag such as v0.1.0a2. The validator also
   accepts the historical alpha spelling v0.1.0-alpha.2.
5. Inspect the built wheel and source archive before creating a GitHub Release.

Do not move or reuse a published version tag. PyPI does not allow replacing an
uploaded version. If a release has a defect, prepare a new version and tag.

## Build and inspect locally

    python -m unittest discover -s tests -v
    python -m compileall -q src tests
    python -m pip check
    python -m build
    python -m twine check dist/*

Check archive contents as well as metadata. dist/ is build output; do not add
unrelated local artifacts to the release.

## Configure PyPI Trusted Publishing

A PyPI project owner must configure the publisher on PyPI before the first
publication. In PyPI project settings, add a Trusted Publisher with:

- Owner: sl4dk1y
- Repository: SnapKeep
- Workflow filename: release.yml
- Environment name: pypi

The publisher is configured at the PyPI account level and cannot be verified
from this local checkout. Confirm the package name is available and configure
the publisher before publishing. PyPI's project JSON endpoint is
https://pypi.org/pypi/snapkeep/json; a not-found response indicates the name
is not currently registered, but only PyPI can reserve it.

## Configure the GitHub environment

In repository settings, create the GitHub Actions environment named pypi.
Optionally add required reviewers and deployment branch restrictions. The
publisher name must match the workflow environment exactly. The publishing job
requests only id-token: write and contents: read; no PyPI password or
long-lived token is stored in GitHub secrets.

## Publish safely

After the matching tag is pushed manually, create a GitHub Release for that
tag. Publishing starts only after the release is marked published. Review the
workflow tag validation, built distributions, and Twine check before relying
on the package. This repository work does not create tags, releases, or
publish distributions.

For a failed or defective publication, do not attempt to overwrite the PyPI
version or move the tag. Yank the affected version through PyPI if appropriate,
then prepare a corrected version with a new version number and tag.
