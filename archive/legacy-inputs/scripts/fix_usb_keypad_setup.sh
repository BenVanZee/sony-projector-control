#!/bin/bash
# Fix USB Keypad Setup - Resolve Python environment issues
# Run this script to fix the externally-managed-environment error

set -e  # Exit on any error

echo "🔧 Fixing USB Keypad Setup"
echo "=========================="

# Check if we're in the right directory
if [ ! -f "usb_keypad_control_headless.py" ]; then
    echo "❌ Please run this script from the projector control directory"
    echo "   Current directory: $(pwd)"
    echo "   Looking for: usb_keypad_control_headless.py"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install packages
echo "🐍 Activating virtual environment and installing packages..."
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install required packages in virtual environment
echo "📦 Installing Python packages in virtual environment..."
pip install pynput evdev

# Set up device permissions for USB keypad
echo "🔧 Setting up USB device permissions..."
sudo usermod -a -G input $(whoami)

# Create udev rule for USB keypad access
echo "📝 Creating udev rule for USB keypad..."
sudo tee /etc/udev/rules.d/99-usb-keypad.rules > /dev/null << 'EOF'
# USB Keypad permissions
SUBSYSTEM=="input", ATTRS{idVendor}=="*", ATTRS{idProduct}=="*", MODE="0666", GROUP="input"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Update systemd service to use virtual environment
echo "🔧 Updating systemd service..."
CURRENT_USER=$(whoami)
sudo tee /etc/systemd/system/usb-keypad-control.service > /dev/null << EOF
[Unit]
Description=Sony Projector USB Keypad Control System
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python3 usb_keypad_control_headless.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "✅ Fix Complete!"
echo "================"
echo ""
echo "Next steps:"
echo "1. Test the USB keypad:"
echo "   source venv/bin/activate"
echo "   python3 usb_keypad_control_headless.py"
echo ""
echo "2. Enable and start the service:"
echo "   sudo systemctl enable usb-keypad-control.service"
echo "   sudo systemctl start usb-keypad-control.service"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status usb-keypad-control.service"
echo ""
echo "4. View logs:"
echo "   journalctl -u usb-keypad-control.service -f"
echo ""
echo "🔌 Connect your USB keypad and test the buttons!"
