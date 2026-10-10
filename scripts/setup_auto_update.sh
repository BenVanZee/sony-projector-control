#!/bin/bash
# Install the nightly auto-update timer for the projector control system.
#
# Creates projector-auto-update.service (oneshot) and .timer (nightly 03:00),
# which run scripts/auto_update.sh to pull new commits from origin/main.

set -e

echo "🔧 Installing auto-update timer for projector control"
echo "====================================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root. It will use sudo when needed."
    exit 1
fi

PROJECT_DIR="/opt/projector-control"
UPDATE_SCRIPT="$PROJECT_DIR/scripts/auto_update.sh"
CONTROL_SERVICE="macropad-control.service"

if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "❌ $PROJECT_DIR is not a git repository."
    echo "   Auto-update works by fetching from origin/main, so the install"
    echo "   must be a git clone. See docs/PI_SETUP_GUIDE.md."
    exit 1
fi

if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo "❌ Not found: $UPDATE_SCRIPT"
    echo "   Pull the latest code first: cd $PROJECT_DIR && git pull origin main"
    exit 1
fi

echo "Project directory: $PROJECT_DIR"

# Pre-flight: refuse to arm an unattended `git reset --hard` over local edits.
#
# --untracked-files=no is deliberate. Untracked files (config_local.py, logs/)
# survive a hard reset untouched, so they are not a problem. Modified *tracked*
# files are - they get silently destroyed at 03:00 with nobody watching.
echo ""
echo "🔍 Checking for local modifications..."
DIRTY=$(git -C "$PROJECT_DIR" status --porcelain --untracked-files=no)
if [ -n "$DIRTY" ]; then
    echo "❌ $PROJECT_DIR has locally modified files:"
    echo ""
    echo "$DIRTY" | sed 's/^/     /'
    echo ""
    echo "   Auto-update runs 'git reset --hard origin/main', which would erase"
    echo "   these edits overnight with nobody watching. Reconcile them first:"
    echo ""
    echo "   1. Review what changed:"
    echo "        git -C $PROJECT_DIR diff"
    echo "   2. Move any site-specific values (projector IPs, aliases, groups)"
    echo "      into $PROJECT_DIR/config_local.py - that file is gitignored and"
    echo "      is never touched by the updater."
    echo "   3. Discard the rest:"
    echo "        git -C $PROJECT_DIR checkout -- ."
    echo "   4. Re-run this script."
    echo ""
    echo "   Timer NOT installed."
    exit 1
fi
echo "   ✅ Working tree is clean"

# The timer runs as root, but $PROJECT_DIR is owned by the service user. Git
# refuses to operate across that ownership boundary ("detected dubious
# ownership") unless the path is explicitly trusted.
echo "🔧 Trusting $PROJECT_DIR for root git operations..."
if sudo git config --system --get-all safe.directory 2>/dev/null | grep -qx "$PROJECT_DIR"; then
    echo "   ✅ Already trusted"
else
    sudo git config --system --add safe.directory "$PROJECT_DIR"
    echo "   ✅ Added to system safe.directory"
fi

chmod +x "$UPDATE_SCRIPT"

# Create logs/ now, as the normal user. The updater runs as root and would
# otherwise create it root-owned on first run, which would break the service's
# own logging (projector_control.py writes logs/projector_control.log).
mkdir -p "$PROJECT_DIR/logs"

# Warn if the service being managed isn't installed - the updater's health
# check would fail on every run.
if ! systemctl list-unit-files "$CONTROL_SERVICE" --no-legend 2>/dev/null | grep -q .; then
    echo ""
    echo "⚠️  $CONTROL_SERVICE is not installed."
    echo "   Run scripts/create_macropad_service.sh first, or the update"
    echo "   health check will fail and roll back every time."
    echo ""
fi

# Create the oneshot update service
echo "🔧 Creating projector-auto-update.service..."
sudo tee /etc/systemd/system/projector-auto-update.service > /dev/null << EOF
[Unit]
Description=Auto-update projector control from origin/main
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$UPDATE_SCRIPT
EOF

# Create the nightly timer
#
# Persistent=false is deliberate: if the Pi was powered off at 03:00, the missed
# run is skipped rather than replayed at boot. Replaying it would fire an update
# and service restart the moment someone powers the Pi up for an event, which is
# exactly what the overnight window exists to avoid.
echo "🔧 Creating projector-auto-update.timer..."
sudo tee /etc/systemd/system/projector-auto-update.timer > /dev/null << 'EOF'
[Unit]
Description=Nightly check for projector control updates

[Timer]
OnCalendar=*-*-* 03:00:00
RandomizedDelaySec=600
Persistent=false

[Install]
WantedBy=timers.target
EOF

echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

echo "🚀 Enabling nightly update timer..."
sudo systemctl enable --now projector-auto-update.timer

echo ""
echo "✅ Auto-update installed!"
echo ""
systemctl list-timers projector-auto-update.timer --no-pager || true
echo ""
echo "To see what it would do right now (changes nothing):"
echo "  sudo $UPDATE_SCRIPT --dry-run"
echo ""
echo "To force an update check immediately:"
echo "  sudo systemctl start projector-auto-update.service"
echo ""
echo "To view update history:"
echo "  sudo journalctl -u projector-auto-update.service"
echo "  cat $PROJECT_DIR/logs/auto_update.log"
echo ""
echo "To pause updates before an event (and resume after):"
echo "  touch $PROJECT_DIR/.no-update"
echo "  rm $PROJECT_DIR/.no-update"
echo ""
echo "Site-specific settings belong in $PROJECT_DIR/config_local.py,"
echo "which is gitignored and never overwritten by an update."
