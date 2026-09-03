# SnapKeep

SnapKeep is a cross-platform project snapshot and backup CLI.

It creates timestamped ZIP snapshots of project directories while allowing
files and directories to be excluded through a `.backupignore` file.

> SnapKeep is currently in alpha development. The CLI behavior and backup
> format may still change before the first stable release.

## Features

- Snapshot any project or directory
- Timestamped ZIP archives
- Custom output directory with `--output`
- Custom ignore file with `--ignore-file`
- Custom snapshot archive name with `--name`
- `.backupignore` exclusion rules
- Built-in exclusions for common development artifacts
- Secure-by-default exclusions for common secret files
- `--include-secrets` override for secret exclusions
- `--no-default-excludes` override for technical exclusions
- `--dry-run` preview mode
- Automatic ZIP integrity verification after creation
- Collision-safe archive naming
- Protection against including the output directory in its own snapshot
- Symbolic links are skipped and their targets are never followed

## Requirements

- Python 3.9 or newer

SnapKeep currently uses only the Python standard library at runtime.

## Installation for development

Clone the repository, create a virtual environment, and install SnapKeep in
editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows, activate the virtual environment with the appropriate PowerShell
or Command Prompt command instead.

## Usage

Create a snapshot of the current directory:

```bash
snapkeep
```

Create a snapshot of another directory:

```bash
snapkeep /path/to/project
```

By default, SnapKeep stores the archive in an `archive` directory next to the
source directory.

Example:

```text
project/
archive/
    project_BACKUP_20260903-205005.zip
```

Choose another destination:

```bash
snapkeep /path/to/project --output /path/to/backups
```

Use a custom ignore file instead of `SOURCE/.backupignore`:

```bash
snapkeep /path/to/project --ignore-file /path/to/custom.ignore
```

Use a custom snapshot name:

```bash
snapkeep /path/to/project --name before-refactor
```

This creates an archive such as:

```text
before-refactor_BACKUP_20260903-223000.zip
```

Preview which files would be included without creating an archive:

```bash
snapkeep /path/to/project --dry-run
```

Show the installed version:

```bash
snapkeep --version
```

## `.backupignore`

If a `.backupignore` file exists in the source directory, SnapKeep uses it to exclude matching files and directories.

By default, SnapKeep reads ignore patterns from `SOURCE/.backupignore`.

You can replace it with another file by using `--ignore-file FILE`. The custom ignore file replaces `SOURCE/.backupignore`; built-in technical exclusions and secret protection still apply independently.

Example:

```text
.git/
.venv/
__pycache__/
build/
dist/
*.zip
```

Blank lines and lines beginning with `#` are ignored.

The current alpha implementation supports basic glob-style exclusions but
does not claim full `.gitignore` compatibility. Negation rules such as `!file`
are not currently supported.

## Secure defaults

SnapKeep excludes common secret files by default, including patterns such as:

```text
.env
.env.*
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519
.aws/credentials
```

Common example/template files such as `.env.example`, `.env.sample`, and
`.env.template` may still be included.

User-defined `.backupignore` rules take precedence over this template
allow-list.

Secret protection can be disabled explicitly:

```bash
snapkeep --include-secrets
```

SnapKeep prints a warning when this option is used.

This protection is based on file paths and names. SnapKeep does not currently
scan file contents for credentials or other secrets.

## Built-in technical exclusions

SnapKeep excludes common development and generated files such as:

```text
.git/
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
build/
dist/
*.egg-info/
.DS_Store
*.pyc
*.pyo
*.zip
```

These exclusions can be disabled with:

```bash
snapkeep --no-default-excludes
```

Secret protection remains enabled unless `--include-secrets` is also used.

## Archive safety

Every created ZIP archive is automatically checked for integrity before
SnapKeep reports the snapshot as successful.

If the generated filename already exists, SnapKeep does not overwrite it.
A numeric suffix is added instead:

```text
project_BACKUP_20260903-205005.zip
project_BACKUP_20260903-205005-1.zip
project_BACKUP_20260903-205005-2.zip
```

If the output directory is located inside the source directory, it is excluded
from collection so that existing snapshots and the archive being created
cannot recursively enter the new snapshot.

Symbolic links are skipped. SnapKeep does not follow symlink targets.

## Scope

SnapKeep is intended for quick snapshots of project working directories,
including uncommitted work that has not yet been stored in Git.

It is not a replacement for:

- Git or another version-control system
- Database backups
- Server or VPS disaster recovery
- Production backup infrastructure
- Encrypted secret storage

Restore automation is not included in the current alpha release. Archives
should be extracted to a separate directory, inspected, and restored manually.

## Roadmap

Planned areas include:

- Improved `.backupignore` functionality
- Standalone archive verification
- Windows, macOS, and Linux packaging
- macOS Finder Quick Action integration
- Windows Explorer integration
- Linux file-manager integrations
- Safer extraction and restore workflows

## Development

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

The current project targets Python 3.9 and newer.

## License

MIT
