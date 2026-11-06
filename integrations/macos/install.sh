#!/bin/bash
# Install the SnapKeep CLI and its Finder Quick Action for the current user.
set -euo pipefail
[[ "$(uname -s)" == "Darwin" ]] || { printf 'Finder integration can only be installed on macOS.\n' >&2; exit 1; }

script_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
repo_root="$(cd -- "$script_dir/../.." && pwd -P)"
workflow_source="$script_dir/Create Project Snapshot.workflow"
workflow_target="$HOME/Library/Services/Create Project Snapshot.workflow"
support_dir="$HOME/Library/Application Support/SnapKeep"
wrapper_source="$script_dir/snapkeep-finder.sh"
wrapper_target="$support_dir/snapkeep-finder.sh"
marker="com.snapkeep.finder-quick-action"
cli_source="${SNAPKEEP_CLI_SOURCE:-local}"
pipx_list_file=""
temporary_wrapper=""

pipx_bin="${PIPX_BIN:-}"
[[ -n "$pipx_bin" ]] || pipx_bin="$(command -v pipx 2>/dev/null || true)"
[[ -n "$pipx_bin" ]] || { [[ ! -x /opt/homebrew/bin/pipx ]] || pipx_bin=/opt/homebrew/bin/pipx; }
[[ -n "$pipx_bin" ]] || { [[ ! -x /usr/local/bin/pipx ]] || pipx_bin=/usr/local/bin/pipx; }
if [[ -z "$pipx_bin" || ! -x "$pipx_bin" ]]; then
    printf 'pipx is required. Install pipx, then run this installer again.\n' >&2
    exit 1
fi

if [[ -e "$workflow_target" ]]; then
    if [[ ! -f "$workflow_target/Contents/document.wflow" ]] || \
       ! /usr/bin/grep -Fq '/Library/Application Support/SnapKeep/snapkeep-finder.sh' \
           "$workflow_target/Contents/document.wflow"; then
        printf 'Refusing to replace an unrecognized workflow: %s\n' "$workflow_target" >&2
        exit 1
    fi
fi
if [[ -e "$wrapper_target" ]] && \
   ! /usr/bin/grep -Fq 'Managed by SnapKeep Finder integration installer.' "$wrapper_target"; then
    printf 'Refusing to replace an unrecognized wrapper: %s\n' "$wrapper_target" >&2
    exit 1
fi

case "$cli_source" in
    local)
        pipx_spec="$repo_root"
        ;;
    github)
        pipx_spec="git+https://github.com/sl4dk1y/SnapKeep.git@main"
        ;;
    pypi)
        pipx_spec="snapkeep"
        ;;
    *)
        printf 'SNAPKEEP_CLI_SOURCE must be local, github, or pypi.\n' >&2
        exit 2
        ;;
esac

# pipx --force replaces the managed environment for this app. Validate that
# the current install is pipx-managed before replacing it, so a conflicting
# executable from another installer is left untouched.
pipx_list_file="$(/usr/bin/mktemp /tmp/snapkeep-pipx-list.XXXXXX)"
if "$pipx_bin" list --json > "$pipx_list_file"; then
    trap '[[ -z "${temporary_wrapper:-}" ]] || /bin/rm -f "$temporary_wrapper"; [[ -z "${pipx_list_file:-}" ]] || /bin/rm -f "$pipx_list_file"' EXIT
    if ! /usr/bin/grep -Eq '"snapkeep"[[:space:]]*:' "$pipx_list_file" && \
       ! /usr/bin/grep -Eq '"package_name"[[:space:]]*:[[:space:]]*"snapkeep"' "$pipx_list_file" && \
       ! /usr/bin/grep -Eq '"app"[[:space:]]*:[[:space:]]*"snapkeep"' "$pipx_list_file" && \
       { command -v snapkeep >/dev/null 2>&1 || [[ -x "$HOME/.local/bin/snapkeep" ]]; }; then
        printf 'A snapkeep executable exists outside pipx. Refusing to replace it; inspect it and remove the conflict first.\n' >&2
        exit 1
    fi
else
    printf 'Could not inspect pipx applications; refusing to replace an installation.\n' >&2
    exit 1
fi

"$pipx_bin" install --force "$pipx_spec"
mkdir -p "$support_dir" "$HOME/Library/Services"
temporary_wrapper="$(/usr/bin/mktemp "$support_dir/.snapkeep-finder.XXXXXX")"
/bin/cp "$wrapper_source" "$temporary_wrapper"
/bin/chmod 755 "$temporary_wrapper"
/bin/mv -f "$temporary_wrapper" "$wrapper_target"
temporary_wrapper=""

[[ -e "$workflow_target" ]] || /bin/mkdir "$workflow_target"
/bin/mkdir -p "$workflow_target/Contents"
/usr/bin/ditto "$workflow_source/Contents/Info.plist" "$workflow_target/Contents/Info.plist"
/usr/bin/ditto "$workflow_source/Contents/document.wflow" "$workflow_target/Contents/document.wflow"
[[ -z "$pipx_list_file" ]] || /bin/rm -f "$pipx_list_file"
pipx_list_file=""
trap - EXIT
printf 'Installed SnapKeep CLI and Finder Quick Action: Create Project Snapshot\n'
printf 'If it does not appear in Finder, enable it under System Settings > Privacy & Security > Extensions > Finder.\n'
