#!/bin/bash
# Fix USB Keypad Control for Raspberry Pi
# This script sets up auto-login and creates a proper systemd service

set -e  # Exit on any error

echo "🔧 Fixing USB Keypad Control for Raspberry Pi"
echo "============================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root. It will use sudo when needed."
    exit 1
fi

CURRENT_USER=$(whoami)
PROJECT_DIR="/opt/projector-control"

echo "Current user: $CURRENT_USER"
echo "Project directory: $PROJECT_DIR"

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    echo "   Please run the setup script first: ./setup_pi_fast.sh"
    exit 1
fi

# Install evdev if not already installed
echo "📦 Installing evdev package..."
sudo apt update
sudo apt install -y python3-evdev

# Create the auto-start script if it doesn't exist
if [ ! -f "$PROJECT_DIR/usb_keypad_auto_start.py" ]; then
    echo "📝 Creating auto-start script..."
    # Copy the auto-start script to the project directory
    if [ -f "./usb_keypad_auto_start.py" ]; then
        cp ./usb_keypad_auto_start.py "$PROJECT_DIR/"
    else
        echo "❌ usb_keypad_auto_start.py not found in current directory"
        exit 1
    fi
fi

# Make the auto-start script executable
chmod +x "$PROJECT_DIR/usb_keypad_auto_start.py"

# Create systemd service for USB keypad control
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/usb-keypad-control.service > /dev/null << EOF
[Unit]
Description=Sony Projector USB Keypad Control System
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/usb_keypad_auto_start.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Give the service time to start
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
EOF

# Configure auto-login for the current user
echo "🔐 Configuring auto-login..."
sudo systemctl set-default multi-user.target

# Create autologin configuration
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $CURRENT_USER --noclear %I \$TERM
EOF

# Alternative: Configure auto-login using raspi-config method
echo "🔧 Configuring auto-login using raspi-config..."
if command -v raspi-config >/dev/null 2>&1; then
    echo "   Using raspi-config to enable auto-login..."
    # This will enable auto-login for the current user
    sudo raspi-config nonint do_boot_behaviour B2
else
    echo "   raspi-config not found, using manual configuration..."
    # Manual configuration for auto-login
    sudo systemctl enable getty@tty1.service
fi

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable the service
echo "🚀 Enabling USB keypad control service..."
sudo systemctl enable usb-keypad-control.service

# Start the service
echo "▶️  Starting USB keypad control service..."
sudo systemctl start usb-keypad-control.service

# Wait a moment for the service to start
sleep 3

# Check service status
echo "📊 Checking service status..."
if sudo systemctl is-active --quiet usb-keypad-control.service; then
    echo "✅ USB keypad control service is running"
else
    echo "❌ USB keypad control service failed to start"
    echo "   Checking logs..."
    sudo journalctl -u usb-keypad-control.service -n 20 --no-pager
fi

echo ""
echo "🎉 USB Keypad Control Fix Complete!"
echo "=================================="
echo ""
echo "Service status:"
sudo systemctl status usb-keypad-control.service --no-pager -l
echo ""
echo "To check logs:"
echo "  sudo journalctl -u usb-keypad-control.service -f"
echo ""
echo "To restart the service:"
echo "  sudo systemctl restart usb-keypad-control.service"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop usb-keypad-control.service"
echo ""
echo "To disable the service:"
echo "  sudo systemctl disable usb-keypad-control.service"
echo ""
echo "The Pi will now auto-login and start the USB keypad control service on boot."
echo "Make sure your USB keypad is connected before rebooting."