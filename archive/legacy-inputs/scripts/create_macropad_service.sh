#!/bin/bash
# Create systemd service for Adafruit Macropad RP2040
# Uses raw HID access (works headless on Raspberry Pi)

set -e

echo "🔧 Creating systemd service for Adafruit Macropad RP2040"
echo "========================================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root. It will use sudo when needed."
    exit 1
fi

CURRENT_USER=$(whoami)
PROJECT_DIR="/opt/projector-control"

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "⚠️  Project directory not found: $PROJECT_DIR"
    echo "   Using current directory instead"
    PROJECT_DIR=$(pwd)
fi

echo "Current user: $CURRENT_USER"
echo "Project directory: $PROJECT_DIR"

# Install dependencies
echo "📦 Checking for dependencies..."
if ! python3 -c "import evdev" 2>/dev/null; then
    echo "   Installing python3-evdev..."
    sudo apt update
    sudo apt install -y python3-evdev
else
    echo "   ✅ evdev already installed"
fi

if ! python3 -c "import hid" 2>/dev/null; then
    echo "   Installing python3-hidapi..."
    sudo apt install -y python3-hidapi
else
    echo "   ✅ hidapi already installed"
fi

# Setup udev rules for HID access
echo "🔧 Setting up HID permissions..."
if [ ! -f /etc/udev/rules.d/99-hidraw-permissions.rules ]; then
    echo 'KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0666"' | sudo tee /etc/udev/rules.d/99-hidraw-permissions.rules > /dev/null
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "   ✅ udev rules created"
else
    echo "   ✅ udev rules already exist"
fi

# Create systemd service for HID macropad control
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/macropad-control.service > /dev/null << EOF
[Unit]
Description=Adafruit Macropad RP2040 Control for Sony Projectors
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 $PROJECT_DIR/macropad/macropad_service_control.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Give the service time to start
TimeoutStartSec=60

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable the service
echo "🚀 Enabling macropad control service..."
sudo systemctl enable macropad-control.service

echo ""
echo "✅ Service created successfully!"
echo ""
echo "To start the service:"
echo "  sudo systemctl start macropad-control.service"
echo ""
echo "To check service status:"
echo "  sudo systemctl status macropad-control.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u macropad-control.service -f"
echo ""
echo "To restart the service:"
echo "  sudo systemctl restart macropad-control.service"
echo ""
echo "The service will automatically start on boot."

