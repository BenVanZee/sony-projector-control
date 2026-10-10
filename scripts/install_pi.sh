#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd -P)

ACTION=${1:-}
if [[ -z "$ACTION" ]]; then
    echo "Usage: $0 install|rollback [--root PATH] [--firmware-mount PATH]" >&2
    exit 2
fi
shift

ROOT_PREFIX=""
SERVICE_USER="benvanzee"
FIRMWARE_MOUNT=""
while (($#)); do
    case "$1" in
        --root)
            ROOT_PREFIX=${2:?Missing value for --root}
            shift 2
            ;;
        --firmware-mount)
            FIRMWARE_MOUNT=${2:?Missing value for --firmware-mount}
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if [[ -n "$ROOT_PREFIX" ]]; then
    if [[ "$ROOT_PREFIX" != /* ]]; then
        echo "--root must be an absolute path" >&2
        exit 2
    fi
    # Canonicalize before anything derives a path from it. Without this, a
    # value containing .. or a symlinked component points the sandboxed rm -rf
    # at the live tree while still skipping every systemd and udev step.
    if ! ROOT_PREFIX=$(cd "$ROOT_PREFIX" 2>/dev/null && pwd -P); then
        echo "--root does not exist: $ROOT_PREFIX" >&2
        exit 2
    fi
    if [[ "$ROOT_PREFIX" == "/" ]]; then
        echo "--root / targets the live system; run without --root instead" >&2
        exit 2
    fi
fi
if [[ -n "$FIRMWARE_MOUNT" && ! -d "$FIRMWARE_MOUNT" ]]; then
    echo "--firmware-mount is not a directory: $FIRMWARE_MOUNT" >&2
    exit 2
fi
# Rollback removes and rewrites three fixed filenames under this path. Require
# proof it is a CircuitPython volume so a mistyped path cannot be overwritten.
if [[ -n "$FIRMWARE_MOUNT" && ! -f "$FIRMWARE_MOUNT/boot_out.txt" ]]; then
    echo "--firmware-mount has no boot_out.txt, so it is not a CIRCUITPY volume: $FIRMWARE_MOUNT" >&2
    exit 2
fi
if [[ -z "$ROOT_PREFIX" && ${EUID:-$(id -u)} -ne 0 ]]; then
    echo "Run the live installer with sudo, or use --root for a sandbox." >&2
    exit 1
fi

DEST="$ROOT_PREFIX/opt/projector-control"
UNIT_DIR="$ROOT_PREFIX/etc/systemd/system"
RULE_DIR="$ROOT_PREFIX/etc/udev/rules.d"
BACKUP_ROOT="$ROOT_PREFIX/var/backups/sony-projector-control"
PRODUCTION_UNIT="$UNIT_DIR/macropad-control.service"
LEGACY_UNITS=(
    "$UNIT_DIR/projector-control.service"
    "$UNIT_DIR/usb-keypad-control.service"
)
MANAGED_RULES=(
    "$RULE_DIR/99-hidraw-permissions.rules"
    "$RULE_DIR/99-sony-macropad.rules"
)
# Host state that lives inside the deployment tree but is not ours to replace.
# The tree is wiped rather than merged so archived code cannot survive an
# upgrade, which would otherwise take the git checkout and any site-local
# override down with it.
PRESERVED_PATHS=(.git config_local.py)
KEEP_BACKUPS=5
INSTALL_COMPLETE=false
BACKUP_DIR=""

safe_remove_deployment() {
    local resolved
    case "$DEST" in
        */opt/projector-control) ;;
        *)
            echo "Refusing unsafe deployment removal: $DEST" >&2
            exit 1
            ;;
    esac

    # The literal path can look right while a symlinked component sends the
    # wipe somewhere else. Resolve it and confirm where it actually lands.
    if [[ -d "$DEST" ]]; then
        resolved=$(cd "$DEST" && pwd -P)
        if [[ -n "$ROOT_PREFIX" ]]; then
            if [[ "$resolved" != "$ROOT_PREFIX"/* ]]; then
                echo "Refusing removal outside the sandbox root: $resolved" >&2
                exit 1
            fi
        elif [[ "$resolved" != "/opt/projector-control" ]]; then
            echo "Refusing removal of a redirected live path: $resolved" >&2
            exit 1
        fi
    fi

    rm -rf -- "$DEST"
}

stash_host_state() {
    local stash=$1 item
    for item in "${PRESERVED_PATHS[@]}"; do
        if [[ -e "$DEST/$item" ]]; then
            cp -a "$DEST/$item" "$stash/$item"
            echo "Preserving $item across the tree replacement"
        fi
    done
}

restore_host_state() {
    local stash=$1 item
    for item in "${PRESERVED_PATHS[@]}"; do
        if [[ -e "$stash/$item" ]]; then
            cp -a "$stash/$item" "$DEST/$item"
        fi
    done
}

cleanup_stash() {
    # The tree is already deleted by the time this can matter. Discarding the
    # only other copy of .git on a failed run would turn a recoverable install
    # into a lost checkout.
    local stash=$1
    if [[ "$INSTALL_COMPLETE" != true && -n "$(ls -A "$stash" 2>/dev/null)" ]]; then
        echo "Preserved host state left at $stash for manual recovery" >&2
        return
    fi
    rm -rf -- "$stash"
}

report_unmanaged_units() {
    local path name
    shopt -s nullglob
    for path in "$UNIT_DIR"/*.service "$UNIT_DIR"/*.timer; do
        name=$(basename "$path")
        case "$name" in
            macropad-control.service|projector-control.service|usb-keypad-control.service)
                continue
                ;;
        esac
        if grep -q "opt/projector-control" "$path" 2>/dev/null; then
            echo "⚠️  $name references the deployment tree but is not managed by this installer." >&2
            echo "⚠️  Review it before relying on this install." >&2
        fi
    done
    shopt -u nullglob
}

prune_backups() {
    local -a stamps
    local index
    shopt -s nullglob
    stamps=("$BACKUP_ROOT"/[0-9]*Z-*)
    shopt -u nullglob
    ((${#stamps[@]} > KEEP_BACKUPS)) || return 0
    for ((index = 0; index < ${#stamps[@]} - KEEP_BACKUPS; index++)); do
        case "${stamps[index]}" in
            "$BACKUP_ROOT"/*) rm -rf -- "${stamps[index]}" ;;
        esac
    done
}

backup_file() {
    local source=$1
    local destination_dir=$2
    local name
    name=$(basename "$source")
    mkdir -p "$destination_dir"
    if [[ -e "$source" ]]; then
        cp -a "$source" "$destination_dir/$name"
    else
        : > "$destination_dir/$name.missing"
    fi
}

create_backup() {
    # Sets BACKUP_DIR rather than printing it. Called through $(...) this would
    # run in a subshell where bash disables errexit and ignores the ERR trap, so
    # a failed tar or cp would be swallowed and the tree wiped anyway with
    # "latest" pointing at an incomplete backup.
    local stamp backup_dir
    stamp=$(date -u +%Y%m%dT%H%M%SZ)-$$
    backup_dir="$BACKUP_ROOT/$stamp"
    mkdir -p "$backup_dir"

    if [[ -d "$DEST" ]]; then
        tar -czf "$backup_dir/projector-control.tgz" \
            -C "$(dirname "$DEST")" "$(basename "$DEST")"
    else
        : > "$backup_dir/projector-control.missing"
    fi

    backup_file "$PRODUCTION_UNIT" "$backup_dir/units"
    local path
    for path in "${LEGACY_UNITS[@]}"; do
        backup_file "$path" "$backup_dir/units"
    done
    for path in "${MANAGED_RULES[@]}"; do
        backup_file "$path" "$backup_dir/rules"
    done

    if [[ -n "$FIRMWARE_MOUNT" && -d "$FIRMWARE_MOUNT" ]]; then
        mkdir -p "$backup_dir/firmware"
        for path in boot.py code.py hid_send.py; do
            backup_file "$FIRMWARE_MOUNT/$path" "$backup_dir/firmware"
        done
    fi

    printf 'created_utc=%s\nservice_user=%s\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SERVICE_USER" \
        > "$backup_dir/BACKUP_INFO"
    ln -sfn "$stamp" "$BACKUP_ROOT/latest"
    prune_backups
    BACKUP_DIR="$backup_dir"
}

file_hash() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}

write_manifest() {
    local manifest="$DEST/DEPLOYED_MANIFEST"
    local commit dirty relative path
    # A git failure must not read as a clean tree. Running under sudo against a
    # user-owned repo, or from a copy made without .git, is the common case.
    if ! commit=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null); then
        commit=unknown
        dirty=unknown
    elif [[ -n "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=normal 2>/dev/null)" ]]; then
        dirty=true
    else
        dirty=false
    fi
    {
        printf 'deployed_utc=%s\nsource_commit=%s\nsource_dirty=%s\n' \
            "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$commit" "$dirty"
        for relative in \
            config.py projector_control.py \
            macropad/hid_macropad_control.py \
            macropad/macropad_service_control.py \
            macropad/systemd_notify.py \
            firmware/boot.py firmware/code.py firmware/hid_send.py; do
            path="$DEST/$relative"
            printf 'sha256=%s  %s\n' "$(file_hash "$path")" "$relative"
        done
        printf 'sha256=%s  %s\n' \
            "$(file_hash "$PRODUCTION_UNIT")" "systemd/macropad-control.service"
        printf 'sha256=%s  %s\n' \
            "$(file_hash "$RULE_DIR/99-sony-macropad.rules")" \
            "udev/99-sony-macropad.rules"
    } > "$manifest"
}

install_files() {
    local stash
    local prior_service_active=false

    report_unmanaged_units

    if [[ -z "$ROOT_PREFIX" ]]; then
        if ! id "$SERVICE_USER" >/dev/null 2>&1; then
            echo "Service user does not exist: $SERVICE_USER" >&2
            exit 1
        fi
        if systemctl is-active --quiet macropad-control.service; then
            systemctl stop macropad-control.service
            prior_service_active=true
        fi
    fi

    # Before the backup exists, the only safe recovery is to put the old service
    # back. After it exists, restarting a service whose files are gone is worse
    # than leaving it down, so the trap switches to pointing at rollback.
    if [[ "$prior_service_active" == true ]]; then
        trap 'systemctl start macropad-control.service >/dev/null 2>&1 || true' ERR
    fi
    create_backup
    trap 'echo "Install failed. Recover with: sudo bash $0 rollback" >&2' ERR

    stash=$(mktemp -d)
    # shellcheck disable=SC2064  # expand $stash now, not at trap time
    trap "cleanup_stash '$stash'" EXIT
    stash_host_state "$stash"

    if [[ -z "$ROOT_PREFIX" ]]; then
        groupadd --force sony-projector
        usermod --append --groups sony-projector "$SERVICE_USER"
        systemctl disable --now projector-control.service usb-keypad-control.service \
            >/dev/null 2>&1 || true
    fi

    # The backup above is complete, so replace rather than merge the live tree.
    # This guarantees that archived input implementations cannot remain active.
    safe_remove_deployment
    install -d -m 0755 "$DEST/macropad" "$DEST/firmware" "$DEST/logs"
    restore_host_state "$stash"
    install -m 0644 "$REPO_ROOT/config.py" "$DEST/config.py"
    install -m 0644 "$REPO_ROOT/projector_control.py" "$DEST/projector_control.py"
    install -m 0644 "$REPO_ROOT/macropad/hid_macropad_control.py" \
        "$DEST/macropad/hid_macropad_control.py"
    install -m 0644 "$REPO_ROOT/macropad/macropad_service_control.py" \
        "$DEST/macropad/macropad_service_control.py"
    install -m 0644 "$REPO_ROOT/macropad/systemd_notify.py" \
        "$DEST/macropad/systemd_notify.py"
    install -m 0644 "$REPO_ROOT/macropad/boot.py" "$DEST/firmware/boot.py"
    install -m 0644 "$REPO_ROOT/macropad/code.py" "$DEST/firmware/code.py"
    install -m 0644 "$REPO_ROOT/macropad/hid_send.py" "$DEST/firmware/hid_send.py"

    install -d -m 0755 "$UNIT_DIR" "$RULE_DIR"
    install -m 0644 "$REPO_ROOT/systemd/macropad-control.service" "$PRODUCTION_UNIT"
    install -m 0644 "$REPO_ROOT/udev/99-sony-macropad.rules" \
        "$RULE_DIR/99-sony-macropad.rules"
    rm -f -- "${LEGACY_UNITS[@]}" "$RULE_DIR/99-hidraw-permissions.rules"
    write_manifest

    if [[ -z "$ROOT_PREFIX" ]]; then
        udevadm control --reload-rules
        udevadm trigger --subsystem-match=hidraw
        systemctl daemon-reload
        systemctl enable --now macropad-control.service
    fi

    INSTALL_COMPLETE=true
    echo "Installed Sony projector controller"
    echo "Backup: $BACKUP_DIR"
}

restore_file() {
    local backup_dir=$1
    local target=$2
    local name source
    name=$(basename "$target")
    source="$backup_dir/$name"
    rm -f -- "$target"
    if [[ -e "$source" ]]; then
        install -d -m 0755 "$(dirname "$target")"
        cp -a "$source" "$target"
    fi
}

rollback_files() {
    local backup_dir="$BACKUP_ROOT/latest"
    local backup_root_real
    if [[ ! -e "$backup_dir" ]]; then
        echo "No backup is available at $backup_dir" >&2
        exit 1
    fi
    backup_dir=$(cd "$backup_dir" && pwd -P)
    backup_root_real=$(cd "$BACKUP_ROOT" && pwd -P)
    case "$backup_dir" in
        "$backup_root_real"/*) ;;
        *)
            echo "Refusing backup outside $backup_root_real" >&2
            exit 1
            ;;
    esac

    if [[ -z "$ROOT_PREFIX" ]]; then
        systemctl stop macropad-control.service >/dev/null 2>&1 || true
    fi

    safe_remove_deployment
    if [[ -f "$backup_dir/projector-control.tgz" ]]; then
        install -d -m 0755 "$(dirname "$DEST")"
        tar -xzf "$backup_dir/projector-control.tgz" -C "$(dirname "$DEST")"
    fi

    restore_file "$backup_dir/units" "$PRODUCTION_UNIT"
    local path
    for path in "${LEGACY_UNITS[@]}"; do
        restore_file "$backup_dir/units" "$path"
    done
    for path in "${MANAGED_RULES[@]}"; do
        restore_file "$backup_dir/rules" "$path"
    done
    if [[ -n "$FIRMWARE_MOUNT" && -d "$backup_dir/firmware" ]]; then
        for path in boot.py code.py hid_send.py; do
            restore_file "$backup_dir/firmware" "$FIRMWARE_MOUNT/$path"
        done
    fi

    if [[ -z "$ROOT_PREFIX" ]]; then
        udevadm control --reload-rules
        udevadm trigger --subsystem-match=hidraw
        systemctl daemon-reload
        if [[ -f "$PRODUCTION_UNIT" ]]; then
            systemctl enable --now macropad-control.service
        fi
    fi
    echo "Rolled back from $backup_dir"
}

case "$ACTION" in
    install) install_files ;;
    rollback) rollback_files ;;
    *)
        echo "Unknown action: $ACTION" >&2
        exit 2
        ;;
esac
