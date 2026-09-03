# Security

SnapKeep creates archives from local directories. Snapshot archives may contain
sensitive information, so they should be treated with the same care as the
source files they contain.

## Default secret protection

SnapKeep excludes several common secret-file patterns by default, including
environment files, private-key formats, SSH private-key names, and AWS
credentials.

Common template files such as `.env.example`, `.env.sample`, and
`.env.template` are allowed unless excluded by another rule.

This protection is path-based. SnapKeep does not currently scan file contents
for credentials, tokens, API keys, passwords, or other secrets.

## `--include-secrets`

The `--include-secrets` option explicitly disables SnapKeep's built-in secret
exclusions.

Use it only when you understand that sensitive files may be written into the
snapshot archive.

User-defined `.backupignore` rules still apply.

## Symbolic links

SnapKeep skips symbolic links and does not follow their targets. This prevents
a symlink inside the source directory from causing files outside the intended
snapshot tree to be archived.

## Archive destinations

SnapKeep excludes its output directory when that directory is located inside
the source tree. This prevents recursive inclusion of existing or newly created
snapshot archives.

Existing archives are not silently overwritten when filename collisions occur.

## Sharing snapshots

Before sharing, publishing, uploading, or attaching a SnapKeep archive, inspect
its contents and verify that it does not contain:

- credentials
- API keys
- access tokens
- passwords
- private keys
- private configuration
- personal or otherwise sensitive data

SnapKeep's built-in exclusions are a safety layer, not a guarantee that every
possible secret will be detected.

## Reporting security issues

Do not publish sensitive vulnerability details or real credentials in public
issues.

If a security issue is discovered, report it privately to the project
maintainers when a private reporting channel is available.
