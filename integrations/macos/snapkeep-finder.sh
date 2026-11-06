#!/bin/bash
# Managed by SnapKeep Finder integration installer.
find_snapkeep() {
    if [[ -n "${SNAPKEEP_BIN:-}" ]]; then
        printf '%s\n' "$SNAPKEEP_BIN"
        return
    fi
    local found
    found="$(command -v snapkeep 2>/dev/null || true)"
    if [[ -n "$found" ]]; then
        printf '%s\n' "$found"
        return
    fi
    for found in "$HOME/.local/bin/snapkeep" /opt/homebrew/bin/snapkeep /usr/local/bin/snapkeep; do
        if [[ -x "$found" ]]; then
            printf '%s\n' "$found"
            return
        fi
    done
    return 1
}

snapkeep_bin="$(find_snapkeep || true)"
if [[ -z "$snapkeep_bin" || ! -x "$snapkeep_bin" ]]; then
    printf 'Snapshot failed: SnapKeep CLI was not found. Install it with pipx and retry.\n'
    [[ "${SNAPKEEP_FINDER_STATUS_MODE:-0}" == 1 ]] && exit 127
    exit 0
fi
if [[ "$#" -eq 0 ]]; then
    printf 'Snapshot failed: Select one or more project folders in Finder and retry.\n'
    [[ "${SNAPKEEP_FINDER_STATUS_MODE:-0}" == 1 ]] && exit 2
    exit 0
fi

seen_paths=()
results=()
processed=0
failed=0
for selected in "$@"; do
    if [[ ! -d "$selected" ]]; then
        project_name="${selected##*/}"
        results[${#results[@]}]="$project_name: FAILED — selected item is not a folder."
        failed=$((failed + 1))
        processed=$((processed + 1))
        continue
    fi
    if ! project_path="$(cd -- "$selected" 2>/dev/null && pwd -P)"; then
        project_name="${selected##*/}"
        results[${#results[@]}]="$project_name: FAILED — could not resolve the selected folder."
        failed=$((failed + 1))
        processed=$((processed + 1))
        continue
    fi

    duplicate=0
    for seen in "${seen_paths[@]}"; do
        if [[ "$project_path" == "$seen" ]]; then
            duplicate=1
            break
        fi
    done
    [[ "$duplicate" -eq 1 ]] && continue
    seen_paths[${#seen_paths[@]}]="$project_path"

    project_name="${project_path##*/}"
    output="$("$snapkeep_bin" "$project_path" 2>&1)"
    status=$?
    processed=$((processed + 1))
    if [[ "$status" -eq 0 ]]; then
        results[${#results[@]}]="$project_name: snapshot created and ZIP verified."
    else
        first_line="$(printf '%s\n' "$output" | /usr/bin/sed -n '1p')"
        [[ -n "$first_line" ]] || first_line="SnapKeep exited with status $status."
        results[${#results[@]}]="$project_name: FAILED — $first_line"
        printf 'snapkeep-finder: error for %s:\n%s\n' "$project_path" "$output" >&2
        failed=$((failed + 1))
    fi
done

if [[ "$processed" -eq 0 ]]; then
    printf 'Snapshot failed: No project folders were processed.\n'
    [[ "${SNAPKEEP_FINDER_STATUS_MODE:-0}" == 1 ]] && exit 1
    exit 0
fi
if [[ "$failed" -eq 0 ]]; then
    printf '%s project snapshot(s) were created and verified.\n' "$processed"
else
    printf '%s of %s selected folder(s) failed.\n' "$failed" "$processed"
fi
for result in "${results[@]}"; do
    printf '%s\n' "$result"
done
# Automator's following Display Notification action presents the output. Keep
# its action successful so native notification delivery always runs. External
# callers can set SNAPKEEP_FINDER_STATUS_MODE=1 for nonzero failure statuses.
if [[ "${SNAPKEEP_FINDER_STATUS_MODE:-0}" == 1 ]]; then
    [[ "$failed" -eq 0 ]] && exit 0
    exit 1
fi
exit 0
