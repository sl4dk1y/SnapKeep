#!/bin/bash
# Remove only the SnapKeep-owned Finder Quick Action and wrapper.
set -euo pipefail
workflow="$HOME/Library/Services/Create Project Snapshot.workflow"
wrapper="$HOME/Library/Application Support/SnapKeep/snapkeep-finder.sh"
marker_comment="Managed by SnapKeep Finder integration installer."

if [[ -e "$workflow" ]]; then
    if [[ ! -f "$workflow/Contents/document.wflow" ]] || \
       ! /usr/bin/grep -Fq '/Library/Application Support/SnapKeep/snapkeep-finder.sh' \
           "$workflow/Contents/document.wflow"; then
        printf 'Refusing to remove an unrecognized workflow: %s\n' "$workflow" >&2
        exit 1
    fi
    for entry in "$workflow"/* "$workflow"/Contents/*; do
        [[ -e "$entry" ]] || continue
        case "$entry" in
            "$workflow/Contents"|"$workflow/Contents/Info.plist"|"$workflow/Contents/document.wflow") ;;
            *) printf 'Workflow contains unrecognized content; leaving it in place: %s\n' "$entry" >&2; exit 1 ;;
        esac
    done
fi
if [[ -e "$wrapper" ]] && ! /usr/bin/grep -Fq "$marker_comment" "$wrapper"; then
    printf 'Refusing to remove an unrecognized wrapper: %s\n' "$wrapper" >&2
    exit 1
fi

if [[ -e "$workflow" ]]; then
    /bin/rm -f "$workflow/Contents/Info.plist" "$workflow/Contents/document.wflow"
    /bin/rmdir "$workflow/Contents" "$workflow"
fi
[[ ! -e "$wrapper" ]] || /bin/rm -f "$wrapper"
rmdir "$HOME/Library/Application Support/SnapKeep" 2>/dev/null || true
rmdir "$HOME/Library/Services" 2>/dev/null || true
printf 'Removed SnapKeep Finder integration. The pipx CLI remains installed.\n'
