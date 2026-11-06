# SnapKeep Finder integration

Install SnapKeep and the Finder Quick Action from a checked-out repository:

```bash
./integrations/macos/install.sh
```

This upgrades the current user's pipx installation from the checkout and adds
**Create Project Snapshot** under Finder's **Quick Actions** menu. Select one or
more folders, right-click, and choose the action. Each selected folder is
processed once through the existing SnapKeep CLI; its verified archive is
placed in a sibling `archive/` directory.

The workflow displays a native macOS notification after processing. macOS
notifications for Automator must be enabled in **System Settings → Notifications**.
If the Quick Action does not appear, enable it in
**System Settings → Privacy & Security → Extensions → Finder**. Access to
selected folders may be controlled by macOS privacy settings.

To upgrade, rerun `install.sh` from the desired checkout. To remove only the
Finder action and wrapper, run:

```bash
./integrations/macos/uninstall.sh
```

The pipx CLI and created archives remain in place. The uninstaller removes only
the workflow and wrapper it recognizes as SnapKeep-managed.

## CLI installation source

By default the installer runs `pipx install --force <local-checkout>`. This
replaces the existing pipx-managed SnapKeep environment with the code in this
checkout; it does not fetch GitHub or PyPI. The installer refuses to replace an
existing `snapkeep` command unless pipx reports a managed SnapKeep application.
Rerunning it is idempotent for the integration, but the installed CLI version
follows the checkout you run it from.

Set `SNAPKEEP_CLI_SOURCE=github` to have this installer install
`git+https://github.com/sl4dk1y/SnapKeep.git@main`, or set it to `pypi` to
install `snapkeep` from PyPI. These source modes also replace the current pipx
environment. Once PyPI releases are available, `pipx upgrade snapkeep` can
upgrade the published CLI independently; rerun the installer from a checkout
to update the Finder wrapper/workflow files.

The Automator Run Shell Script action intentionally exits successfully so its
following native Display Notification action runs even when a snapshot fails.
For scripts and automated checks that need a process status, execute the
wrapper with `SNAPKEEP_FINDER_STATUS_MODE=1`; it returns `1` for snapshot
failures, `2` when no paths are supplied, and `127` when SnapKeep cannot be
found. A successful run returns `0` in either mode.
