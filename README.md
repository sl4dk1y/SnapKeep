# SnapKeep

SnapKeep is a cross-platform project snapshot and backup CLI.

It creates timestamped snapshots of project directories while allowing files
and directories to be excluded through a `.backupignore` file.

> SnapKeep is currently under development. The v0.1 CLI and backup format are
> not yet considered stable.

## Goals

- Windows, macOS, and Linux support
- Configurable source and backup destination
- `.backupignore` support
- Safe handling of secrets
- Dry-run support
- ZIP integrity verification
- Optional file-manager integrations such as macOS Finder Quick Actions

## Status

Early development.

SnapKeep does not replace Git or production backup/disaster-recovery systems.
It is intended as a lightweight snapshot tool for project working directories.
