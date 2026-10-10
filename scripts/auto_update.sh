#!/bin/bash
# Auto-update the projector control system from origin/main.
#
# Run as root by projector-auto-update.timer (see scripts/setup_auto_update.sh).
# Checks whether origin/main has moved; if it has, syncs the working tree,
# restarts the service, and verifies it came back healthy. An unhealthy update
# is rolled back to the previous commit automatically.
#
# Usage:
#   sudo ./auto_update.sh              # check and update
#   sudo ./auto_update.sh --dry-run    # report what it would do, change nothing
#
# WHY EVERYTHING IS INSIDE main():
# This script lives in the repository it rewrites. Bash reads a script
# incrementally as it executes, so a `git reset --hard` partway through could
# swap the file out from under the interpreter and splice a different script
# into the middle of the run. Bash parses a function body as a single unit
# before executing it, so wrapping the logic in main() and calling it on the
# very last line makes the rewrite harmless.

set -uo pipefail

# Overridable from the environment so you can point a single run somewhere else
# without editing this file, e.g. testing a rollback against a scratch branch:
#   sudo TARGET_REF=origin/test-bad-commit ./auto_update.sh
PROJECT_DIR="${PROJECT_DIR:-/opt/projector-control}"
SERVICE="${SERVICE:-macropad-control.service}"
TARGET_REF="${TARGET_REF:-origin/main}"
HEALTH_WAIT="${HEALTH_WAIT:-30}"
LOG_FILE="$PROJECT_DIR/logs/auto_update.log"
FREEZE_FILE="$PROJECT_DIR/.no-update"

# Log to stdout (captured by journald) and to a file. The file matters because
# Raspberry Pi OS ships journald in volatile mode - there is no
# /var/log/journal, so the journal lives in /run and is wiped on reboot. Since
# this script can trigger a reboot, journal-only logging would destroy the
# record of why it rebooted.
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg"
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

# Hand the tree back to the service user. We run as root, so both `git fetch`
# (new objects under .git/) and `git reset --hard` (working tree files) leave
# root-owned files behind. Left alone these accumulate and eventually break
# ordinary user-run git commands, so this is called after every git operation,
# not just after an update.
fix_ownership() {
    local owner
    owner=$(stat -c '%U:%G' "$PROJECT_DIR" 2>/dev/null)
    [ -z "$owner" ] && return 0
    chown -R "$owner" "$PROJECT_DIR" || log "  WARN: chown to $owner failed"
}

# Point the working tree at a specific commit.
sync_to() {
    local sha="$1"

    if ! git reset --hard --quiet "$sha"; then
        log "  ERROR: git reset --hard $sha failed"
        return 1
    fi
    fix_ownership
    log "  working tree now at $(git rev-parse --short HEAD)"
}

# Restart the service and decide whether it is actually running.
#
# `systemctl is-active` alone is not enough: macropad-control.service is
# Restart=always/RestartSec=10, so a service that starts, crashes, and gets
# resurrected reports "active" most of the time you poll it. The honest signal
# is whether the restart counter climbed during the observation window.
restart_and_check() {
    local n0 n1 state

    if ! systemctl restart "$SERVICE"; then
        log "  ERROR: systemctl restart $SERVICE failed"
        return 1
    fi

    n0=$(systemctl show -p NRestarts --value "$SERVICE" 2>/dev/null)
    [[ "$n0" =~ ^[0-9]+$ ]] || n0=0

    log "  restarted $SERVICE, observing for ${HEALTH_WAIT}s"
    sleep "$HEALTH_WAIT"

    n1=$(systemctl show -p NRestarts --value "$SERVICE" 2>/dev/null)
    [[ "$n1" =~ ^[0-9]+$ ]] || n1=0
    state=$(systemctl is-active "$SERVICE" 2>/dev/null || true)

    if [ "$state" = "active" ] && [ "$n1" -le "$n0" ]; then
        log "  healthy (state=$state, restarts $n0 -> $n1)"
        return 0
    fi

    log "  UNHEALTHY (state=$state, restarts $n0 -> $n1)"
    return 1
}

main() {
    local dry_run=0
    if [ "${1:-}" = "--dry-run" ]; then
        dry_run=1
    fi

    if ! cd "$PROJECT_DIR"; then
        log "ERROR: $PROJECT_DIR not found"
        exit 1
    fi

    if [ -f "$FREEZE_FILE" ]; then
        log "Freeze switch present ($FREEZE_FILE) - skipping update"
        exit 0
    fi

    local remote="${TARGET_REF%%/*}"
    local branch="${TARGET_REF#*/}"
    local fetch_err
    if ! fetch_err=$(git fetch "$remote" "$branch" 2>&1); then
        log "WARN: git fetch $remote $branch failed - nothing changed: $fetch_err"
        exit 1
    fi
    fix_ownership

    local old new
    old=$(git rev-parse HEAD)
    if ! new=$(git rev-parse --verify --quiet "$TARGET_REF^{commit}"); then
        log "ERROR: $TARGET_REF does not resolve to a commit - check the branch name"
        exit 1
    fi

    if [ "$old" = "$new" ]; then
        # Logged every run on purpose. On an unattended box, "nothing to update"
        # and "the timer stopped firing" otherwise look identical.
        log "Up to date at ${old:0:7} - nothing to do"
        exit 0
    fi

    log "New commit on $TARGET_REF: ${old:0:7} -> ${new:0:7}"
    while IFS= read -r line; do
        log "    $line"
    done < <(git --no-pager log --oneline "$old..$new" 2>/dev/null)

    if [ "$dry_run" -eq 1 ]; then
        log "DRY RUN - would sync to ${new:0:7} and restart $SERVICE. Nothing changed."
        exit 0
    fi

    if ! sync_to "$new"; then
        log "ERROR: could not sync to ${new:0:7} - leaving system as-is"
        exit 1
    fi

    if restart_and_check; then
        log "UPDATED to ${new:0:7} successfully"
        exit 0
    fi

    log "Update to ${new:0:7} is unhealthy - rolling back to ${old:0:7}"
    if ! sync_to "$old"; then
        log "ERROR: rollback to ${old:0:7} failed. Rebooting to recover."
        systemctl reboot
        exit 1
    fi

    if restart_and_check; then
        log "ROLLED BACK to ${old:0:7}. Commit ${new:0:7} is bad - fix it and push again."
        exit 1
    fi

    # Known-good code is also unhealthy, so the problem is not the commit.
    # Usually a wedged USB/hidraw device - the one thing a reboot actually fixes.
    log "Still unhealthy on known-good ${old:0:7}. Not a code problem. Rebooting."
    systemctl reboot
    # Normally unreachable - the reboot kills this process. If we do get here,
    # the reboot did not happen, and the unit should be marked failed.
    exit 1
}

main "$@"
