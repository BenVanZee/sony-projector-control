# 4-Button USB-C Keypad Setup Guide

## Overview
This guide will help you set up your 4-button USB-C keypad to control your Sony projector system.

## Button Functions
- **Button 1**: Turn projectors OFF
- **Button 2**: Turn projectors ON  
- **Button 3**: Toggle screen blanking
- **Button 4**: Toggle screen freezing

## Hardware Requirements
- 4-button USB-C keypad (Amazon purchase)
- USB-C cable
- Computer (Mac, Linux, or Windows)

## Platform Setup

### macOS Setup
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

### Linux Setup
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

### Windows Setup
1. **Install Python dependencies:**
   ```bash
   pip install evdev
   ```

2. **Note:** Windows support for evdev may be limited. Consider using the console mode for testing.

## Testing Your Keypad

### Step 1: Connect Your Keypad
1. Connect your USB-C keypad to your computer
2. Ensure it's recognized as an input device

### Step 2: Run the Test Script
```bash
python3 test_keypad.py
```

### Step 3: Test Each Button
- Press each button and verify the output
- Check that the correct key codes are detected
- Verify the button count increases

## Key Mapping

The script automatically maps common key codes:
- **Number keys**: 1, 2, 3, 4
- **Function keys**: F1, F2, F3, F4  
- **Letter keys**: A, B, C, D

If your keypad uses different keys, the script will show you what keys are detected, and you can modify the `key_mappings` dictionary in the code.

## Troubleshooting

### Keypad Not Detected
- Check USB connection
- Try different USB ports
- Restart the test script
- Check if the keypad appears in System Preferences > Keyboard (Mac)

### Permission Errors
- On macOS: Try running with `sudo python3 test_keypad.py`
- On Linux: Check device permissions with `ls -la /dev/input/event*`

### Unknown Key Codes
- The script will show you what keys are detected
- Add custom mappings in the `key_mappings` dictionary
- Common alternatives: arrow keys, page up/down, home/end

## Advanced Features

### Custom Key Mapping
You can modify the key mappings in `test_keypad.py`:
```python
self.key_mappings = {
    'KEY_1': 1,           # Number 1 key
    'KEY_F1': 1,          # Function key F1
    'KEY_A': 1,           # Letter A
    'KEY_UP': 1,          # Up arrow
    # Add your custom mappings here
}
```

### Button Function Customization
Once you know your key codes, you can customize the button functions in `macropad_4button.py`.

## Next Steps
1. **Test the keypad** with `test_keypad.py`
2. **Verify all buttons work** and note the key codes
3. **Customize key mappings** if needed
4. **Test the full projector control** system
5. **Deploy to your projector control system**

## Mac-Specific Notes
- USB devices are typically plug-and-play on macOS
- If you get permission errors, check System Preferences > Security & Privacy
- Some USB keypads may require drivers (check manufacturer website)
- The script will automatically detect your keypad and show available devices
