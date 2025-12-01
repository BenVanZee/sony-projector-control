# HID Device Permissions on Raspberry Pi

## Problem

When trying to use HID devices (like the Adafruit RP2040 Macropad) on Raspberry Pi, you may encounter permission errors:

```text
❌ No HID macropad found
Permission denied
```

This happens because Linux restricts access to raw HID devices (`/dev/hidraw*`) to root by default.

## Solution Options

### Option 1: Setup udev Rules (Recommended)

This allows your user to access HID devices without sudo.

**Quick Setup:**

```bash
chmod +x setup_hid_permissions.sh
./setup_hid_permissions.sh
```

**Manual Setup:**

```bash
# Create udev rule
sudo tee /etc/udev/rules.d/99-hidraw-permissions.rules << EOF
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0666", TAG+="uaccess"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Unplug and replug your device
```

**Verify:**

```bash
ls -l /dev/hidraw*
# Should show: crw-rw-rw- (readable/writable by all)
```

### Option 2: Run with sudo (Quick Test)

For testing only, you can run the script with sudo:

```bash
sudo python3 run_macropad_with_mocks.py hid-macropad
```

**Note:** This is not recommended for production use.

### Option 3: Use Keyboard Listener Mode

If your macropad acts as a keyboard (sends keyboard events), use the keyboard listener instead:

```bash
python3 run_macropad_with_mocks.py usb-keypad
```

This doesn't require HID permissions since it listens to keyboard events.

## Troubleshooting

### Check if device is detected

```bash
# List USB devices
lsusb

# Look for Adafruit device (VID: 239a)
lsusb | grep 239a

# List HID devices
ls -l /dev/hidraw*
```

### Check Python HID module

```bash
# Verify hidapi is installed
python3 -c 'import hid; print("✅ HID module works")'

# List all HID devices (requires permissions)
python3 -c 'import hid; print([d["product_string"] for d in hid.enumerate()])'
```

### Common Issues

1. **"No module named 'hid'"**
   - Install: `sudo apt install python3-hidapi` or `pip3 install hidapi`

2. **"Permission denied" even after udev rules**
   - Unplug and replug the device
   - Check file permissions: `ls -l /dev/hidraw*`
   - Verify udev rule exists: `cat /etc/udev/rules.d/99-hidraw-permissions.rules`

3. **Device not found**
   - Check USB connection: `lsusb`
   - Try different USB port
   - Check if device is in bootloader mode (should be in normal mode)

## Adafruit RP2040 Macropad Specifics

The Adafruit Macropad can operate in different modes:

- **VID:PID 239a:8027** - Firmware/bootloader mode
- **VID:PID 239a:8107** - Alternative HID mode  
- **VID:PID 239a:8108** - Standard HID mode

Make sure your CircuitPython code on the macropad is configured to send HID reports properly.

## Security Note

The udev rule `MODE="0666"` makes HID devices accessible to all users. If you want more restrictive permissions:

```bash
# Only allow users in 'input' group
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0660", GROUP="input"

# Add your user to input group
sudo usermod -a -G input $USER
# Log out and back in for group change to take effect
```
