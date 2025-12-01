#!/bin/bash
# Setup HID device permissions for Raspberry Pi
# This allows non-root users to access HID devices like the Adafruit Macropad

echo "🔧 Setting up HID device permissions for Raspberry Pi..."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Please run this script as a normal user (without sudo)"
    echo "   The script will prompt for sudo when needed"
    exit 1
fi

# Create udev rule
echo "📝 Creating udev rule..."
sudo tee /etc/udev/rules.d/99-hidraw-permissions.rules > /dev/null << 'EOF'
# Allow access to HID devices for all users
# This is needed for devices like Adafruit Macropad, Stream Deck, etc.
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0666", TAG+="uaccess"
EOF

if [ $? -eq 0 ]; then
    echo "✅ Udev rule created: /etc/udev/rules.d/99-hidraw-permissions.rules"
else
    echo "❌ Failed to create udev rule"
    exit 1
fi

# Reload udev rules
echo ""
echo "🔄 Reloading udev rules..."
sudo udevadm control --reload-rules
if [ $? -eq 0 ]; then
    echo "✅ Udev rules reloaded"
else
    echo "❌ Failed to reload udev rules"
    exit 1
fi

# Trigger udev
echo ""
echo "⚡ Triggering udev..."
sudo udevadm trigger
if [ $? -eq 0 ]; then
    echo "✅ Udev triggered"
else
    echo "❌ Failed to trigger udev"
    exit 1
fi

echo ""
echo "✅ HID permissions setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Unplug your HID device (macropad)"
echo "   2. Plug it back in"
echo "   3. Run your script without sudo:"
echo "      python3 run_macropad_with_mocks.py hid-macropad"
echo ""
echo "💡 To verify the device is accessible, run:"
echo "   ls -l /dev/hidraw*"
echo "   You should see permissions like: crw-rw-rw-"
echo ""
