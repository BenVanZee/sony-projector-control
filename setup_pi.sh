#!/bin/bash
# Sony Projector Control - Raspberry Pi Setup Script
# This script automates the installation and configuration

set -e  # Exit on any error

echo "🎬 Sony Projector Control - Pi Setup Script"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root. It will use sudo when needed."
    exit 1
fi

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create project directory
echo "📁 Creating project directory..."
sudo mkdir -p /opt/projector-control
sudo chown $(whoami):$(whoami) /opt/projector-control
cd /opt/projector-control

# Update system
echo "🔄 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-rpi.gpio \
    python3-hidapi \
    python3-pynput \
    git \
    curl \
    wget \
    nano \
    htop \
    ufw

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Set up GPIO permissions
echo "🔧 Setting up GPIO permissions..."
sudo usermod -a -G gpio $(whoami)

# Create basic config if it doesn't exist
if [ ! -f config.py ]; then
    echo "⚙️  Creating default configuration..."
    cat > config.py << 'EOF'
# Sony Projector Control Configuration
# Update these IP addresses with your actual projector IPs

PROJECTORS = [
    {
        'ip': '10.10.10.2',      # Replace with your first projector IP
        'port': 4352,            # PJLink port (usually 4352)
        'name': 'Left',          # Friendly name
        'nickname': 'left',      # Short nickname for CLI
        'location': 'Main Hall - Left Side',
        'group': 'front'         # Group assignment
    },
    {
        'ip': '10.10.10.3',      # Replace with your second projector IP
        'port': 4352,
        'name': 'Right',
        'nickname': 'right',
        'location': 'Main Hall - Right Side',
        'group': 'front'
    }
]

# Nickname aliases for easy reference
PROJECTOR_ALIASES = {
    'left': '10.10.10.2',
    'right': '10.10.10.3',
    'l': '10.10.10.2',           # Shorthand
    'r': '10.10.10.3',           # Shorthand
}

# Group-based aliases for controlling multiple projectors
PROJECTOR_GROUPS = {
    'front': ['left', 'right'],      # Front projectors
    'all': ['left', 'right']         # All projectors
}

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'projector_control.log'
EOF
fi

# Create systemd service
echo "🔧 Creating systemd service..."
CURRENT_USER=$(whoami)
sudo tee /etc/systemd/system/projector-control.service > /dev/null << EOF
[Unit]
Description=Sony Projector Control System
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=/opt/projector-control
Environment=PATH=/opt/projector-control/venv/bin
ExecStart=/opt/projector-control/venv/bin/python3 macropad_control.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable SSH
echo "🔐 Enabling SSH..."
sudo systemctl enable ssh
sudo systemctl start ssh

# Set up basic firewall
echo "🛡️  Setting up firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow from 10.10.10.0/24

# Create test script
echo "🧪 Creating test script..."
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify the projector control setup
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import socket
        print("✅ socket module available")
    except ImportError as e:
        print(f"❌ socket module error: {e}")
        return False
    
    try:
        import RPi.GPIO as GPIO
        print("✅ RPi.GPIO module available")
    except ImportError as e:
        print(f"❌ RPi.GPIO module error: {e}")
        return False
    
    try:
        import hid
        print("✅ hid module available")
    except ImportError as e:
        print(f"❌ hid module error: {e}")
        return False
    
    return True

def test_config():
    """Test if configuration file exists and is valid"""
    print("\nTesting configuration...")
    
    if not os.path.exists('config.py'):
        print("❌ config.py not found")
        return False
    
    try:
        import config
        print("✅ config.py loaded successfully")
        print(f"   Found {len(config.PROJECTORS)} projectors configured")
        return True
    except Exception as e:
        print(f"❌ config.py error: {e}")
        return False

def test_network():
    """Test basic network connectivity"""
    print("\nTesting network...")
    
    try:
        import socket
        import config
        
        for projector in config.PROJECTORS:
            ip = projector['ip']
            port = projector['port']
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print(f"✅ {projector['name']} ({ip}:{port}) - Connected")
            else:
                print(f"❌ {projector['name']} ({ip}:{port}) - Connection failed")
        
        return True
    except Exception as e:
        print(f"❌ Network test error: {e}")
        return False

if __name__ == "__main__":
    print("🎬 Projector Control Setup Test")
    print("===============================")
    
    all_tests_passed = True
    
    all_tests_passed &= test_imports()
    all_tests_passed &= test_config()
    all_tests_passed &= test_network()
    
    print("\n" + "="*30)
    if all_tests_passed:
        print("✅ All tests passed! Setup looks good.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)
EOF

chmod +x test_setup.py

# Make all Python files executable
echo "🔧 Setting permissions..."
find . -name "*.py" -exec chmod +x {} \;

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Copy your projector control files to /opt/projector-control/"
echo "2. Edit config.py with your actual projector IP addresses:"
echo "   sudo nano /opt/projector-control/config.py"
echo ""
echo "3. Test the setup:"
echo "   cd /opt/projector-control"
echo "   python3 test_setup.py"
echo ""
echo "4. Test basic connectivity:"
echo "   python3 test_connection.py"
echo ""
echo "5. Enable auto-start service:"
echo "   sudo systemctl enable projector-control.service"
echo "   sudo systemctl start projector-control.service"
echo ""
echo "6. Check service status:"
echo "   sudo systemctl status projector-control.service"
echo ""
echo "For more help, see PI_SETUP_GUIDE.md"
echo ""
echo "🔧 To copy files from your computer, use:"
echo "   scp -r /path/to/sony-projector-control/* $(whoami)@your-pi-ip:/opt/projector-control/"
