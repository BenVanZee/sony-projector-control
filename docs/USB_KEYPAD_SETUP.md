# USB Keypad Setup Guide

## Overview
This guide covers setting up your USB keypad to control your Sony projector system, including initial setup and auto-start configuration for Raspberry Pi.

## Button Functions
- **Button 1**: Turn projectors OFF
- **Button 2**: Turn projectors ON  
- **Button 3**: Toggle screen blanking
- **Button 4**: Toggle screen freezing

## Hardware Requirements
- 4-button USB-C keypad (Amazon purchase)
- USB-C cable
- Computer (Mac, Linux, or Windows)

## Initial Setup

### Platform Setup

#### macOS Setup
1. **Install Python dependencies:**
   ```bash
   pip3 install evdev
   ```

2. **Install evdev (if the above doesn't work):**
   ```bash
   brew install python-evdev
   # or
   pip3 install --user evdev
   ```

3. **Note:** macOS may require additional setup for USB device access. If you encounter permission issues, you may need to run with sudo or adjust security settings.

#### Linux Setup
1. **Install Python dependencies:**
   ```bash
   sudo apt-get install python3-evdev
   # or
   pip3 install evdev
   ```

2. **Set device permissions:**
   ```bash
   sudo chmod 666 /dev/input/event*
   ```

#### Windows Setup
1. **Install Python dependencies:**
   ```bash
   pip install evdev
   ```

2. **Note:** Windows support for evdev may be limited. Consider using the console mode for testing.

### Testing Your Keypad

#### Step 1: Connect Your Keypad
1. Connect your USB-C keypad to your computer
2. Ensure it's recognized as an input device

#### Step 2: Run the Test Script
```bash
# Test the keypad
python3 macropad/usb_keypad_control_specific.py /dev/input/event0
```

#### Step 3: Test Each Button
- Press each button and verify the output
- Check that the correct key codes are detected
- Verify the button count increases

### Key Mapping

The script automatically maps common key codes:
- **Number keys**: 1, 2, 3, 4
- **Function keys**: F1, F2, F3, F4  
- **Letter keys**: A, B, C, D

If your keypad uses different keys, the script will show you what keys are detected, and you can modify the `key_mappings` dictionary in the code.

### Custom Key Mapping
You can modify the key mappings in `macropad/usb_keypad_control_specific.py`:
```python
self.key_mappings = {
    45: 1,           # X key (Cut) - Turn projectors OFF
    46: 2,           # C key (Copy) - Turn projectors ON
    47: 3,           # V key (Paste) - Toggle screen blanking
    28: 4,           # Enter key - Toggle screen freezing
    # Add your custom mappings here
}
```

### Button Function Customization
Once you know your key codes, you can customize the button functions in `macropad/macropad_4button.py` or `macropad/usb_keypad_control_specific.py`.

## Auto-Start Setup (Raspberry Pi)

### Problem
When the Raspberry Pi boots, it starts at a login prompt instead of automatically running the USB keypad control script. The script works when manually run with:
```bash
python3 macropad/usb_keypad_control_specific.py /dev/input/event0
```

### Solution
This fix creates an auto-start system that:
1. Automatically detects the USB keypad device path
2. Configures the Pi to auto-login on boot
3. Creates a systemd service that starts the USB keypad control automatically

### Quick Fix

#### 1. Copy the fix script to your Pi
```bash
# From your computer, copy the fix script to your Pi
scp scripts/fix_usb_keypad_pi.sh macropad/usb_keypad_auto_start.py your-username@your-pi-ip:/home/your-username/
```

#### 2. Run the fix script on your Pi
```bash
# SSH into your Pi
ssh your-username@your-pi-ip

# Make the script executable and run it
chmod +x fix_usb_keypad_pi.sh
./fix_usb_keypad_pi.sh
```

#### 3. Reboot your Pi
```bash
sudo reboot
```

### What the Fix Does

#### 1. Auto-Start Script (`macropad/usb_keypad_auto_start.py`)
- Automatically detects USB keypad devices
- Waits up to 60 seconds for the keypad to be detected
- Starts the USB keypad control with the correct device path
- Handles errors and logging

#### 2. Systemd Service (`usb-keypad-control.service`)
The service file should reference the correct path:
- Runs the auto-start script as a system service
- Automatically restarts if it fails
- Starts after network is available
- Logs all output to systemd journal

#### 3. Auto-Login Configuration
- Configures the Pi to automatically log in the current user
- Uses both raspi-config and manual systemd configuration
- Ensures the service can run without manual login

### Verification

#### Check Service Status
```bash
sudo systemctl status usb-keypad-control.service
```

#### View Service Logs
```bash
# View recent logs
sudo journalctl -u usb-keypad-control.service -n 20

# Follow logs in real-time
sudo journalctl -u usb-keypad-control.service -f
```

#### Test the Service
```bash
# Restart the service
sudo systemctl restart usb-keypad-control.service

# Check if it's running
sudo systemctl is-active usb-keypad-control.service
```

### Service Management

#### Enable/Disable Service
```bash
# Enable service to start on boot
sudo systemctl enable usb-keypad-control.service

# Disable service
sudo systemctl disable usb-keypad-control.service
```

#### Start/Stop Service
```bash
# Start service now
sudo systemctl start usb-keypad-control.service

# Stop service
sudo systemctl stop usb-keypad-control.service

# Restart service
sudo systemctl restart usb-keypad-control.service
```

## Troubleshooting

### Keypad Not Detected
- Check USB connection
- Try different USB ports
- Restart the test script
- Check if the keypad appears in System Preferences > Keyboard (Mac)

### Permission Errors
- On macOS: Try running with `sudo python3 macropad/usb_keypad_control_specific.py`
- On Linux: Check device permissions with `ls -la /dev/input/event*`

### Unknown Key Codes
- The script will show you what keys are detected
- Add custom mappings in the `key_mappings` dictionary
- Common alternatives: arrow keys, page up/down, home/end

### Service Not Starting
1. Check if the USB keypad is connected
2. Verify the device path exists: `ls /dev/input/event*`
3. Check service logs: `sudo journalctl -u usb-keypad-control.service -n 50`

### Auto-Login Not Working
1. Check if auto-login is enabled: `sudo systemctl status getty@tty1.service`
2. Verify user permissions: `groups $USER`
3. Check if the user is in the correct groups

### USB Keypad Not Detected (Service)
1. Check if evdev is installed: `python3 -c "import evdev; print('OK')"`
2. List input devices: `python3 -c "import evdev; [print(d) for d in evdev.list_devices()]"`
3. Check USB device: `lsusb`

### Manual Device Detection

If the auto-detection doesn't work, you can manually specify the device:

1. Find your USB keypad device:
```bash
python3 -c "
import evdev
for path in evdev.list_devices():
    device = evdev.InputDevice(path)
    print(f'{device.path}: {device.name}')
"
```

2. Edit the auto-start script to use a specific device:
```python
# In macropad/usb_keypad_auto_start.py, replace the device detection with:
device_path = "/dev/input/event0"  # Replace with your device path
```

## Files Created/Modified

- `/opt/projector-control/macropad/usb_keypad_auto_start.py` - Auto-start script
- `/etc/systemd/system/usb-keypad-control.service` - Systemd service
- `/etc/systemd/system/getty@tty1.service.d/autologin.conf` - Auto-login config

## Notes

- The service will automatically restart if it fails
- The service waits up to 60 seconds for the USB keypad to be detected
- All output is logged to the systemd journal
- The service runs as the current user, not root
- Make sure your USB keypad is connected before rebooting

## Mac-Specific Notes

- USB devices are typically plug-and-play on macOS
- If you get permission errors, check System Settings > Security & Privacy
- Some USB keypads may require drivers (check manufacturer website)
- The script will automatically detect your keypad and show available devices

## Next Steps

1. **Test the keypad** with `macropad/usb_keypad_control_specific.py`
2. **Verify all buttons work** and note the key codes
3. **Customize key mappings** if needed
4. **Test the full projector control** system
5. **Set up auto-start** (if using Raspberry Pi)
6. **Deploy to your projector control system**

