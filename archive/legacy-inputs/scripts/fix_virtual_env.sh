#!/bin/bash
# Fix Virtual Environment for USB Keypad Control
# Run this on your Raspberry Pi

set -e  # Exit on any error

echo "🔧 Fixing Virtual Environment"
echo "============================="

# Check if we're in the right directory
if [ ! -f "usb_keypad_control_headless.py" ]; then
    echo "❌ Please run this script from the projector control directory"
    echo "   Current directory: $(pwd)"
    echo "   Looking for: usb_keypad_control_headless.py"
    exit 1
fi

# Remove existing venv if it's broken
if [ -d "venv" ]; then
    echo "🗑️  Removing broken virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "📦 Creating new virtual environment..."
python3 -m venv venv

# Verify venv was created
if [ ! -f "venv/bin/pip" ]; then
    echo "❌ Virtual environment creation failed"
    echo "   Trying alternative method..."
    
    # Try with --system-site-packages
    python3 -m venv --system-site-packages venv
    
    if [ ! -f "venv/bin/pip" ]; then
        echo "❌ Virtual environment creation still failed"
        echo "   Installing packages system-wide instead..."
        
        # Install packages system-wide as fallback
        sudo apt install -y python3-pip
        pip3 install --user pynput evdev
        
        echo "✅ Installed packages system-wide"
        echo "   You can now run: python3 usb_keypad_control_headless.py"
        exit 0
    fi
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Verify pip is working
if ! venv/bin/pip --version > /dev/null 2>&1; then
    echo "❌ pip not working in virtual environment"
    echo "   Installing packages system-wide instead..."
    
    # Install packages system-wide as fallback
    sudo apt install -y python3-pip
    pip3 install --user pynput evdev
    
    echo "✅ Installed packages system-wide"
    echo "   You can now run: python3 usb_keypad_control_headless.py"
    exit 0
fi

# Install packages in virtual environment
echo "📦 Installing packages in virtual environment..."
venv/bin/pip install --upgrade pip
venv/bin/pip install pynput evdev

# Set up permissions
echo "🔧 Setting up permissions..."
sudo usermod -a -G input $(whoami)

# Create udev rule
echo "📝 Creating udev rule..."
sudo tee /etc/udev/rules.d/99-usb-keypad.rules > /dev/null << 'EOF'
# USB Keypad permissions
SUBSYSTEM=="input", ATTRS{idVendor}=="*", ATTRS{idProduct}=="*", MODE="0666", GROUP="input"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Create systemd service
echo "🔧 Creating systemd service..."
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
echo "Test the setup:"
echo "  source venv/bin/activate"
echo "  python3 usb_keypad_control_headless.py"
echo ""
echo "Or enable the service:"
echo "  sudo systemctl enable usb-keypad-control.service"
echo "  sudo systemctl start usb-keypad-control.service"
