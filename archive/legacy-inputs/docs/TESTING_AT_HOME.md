# Testing RP2040 Macropad at Home

This guide explains how to test your RP2040 macropad at home using the Raspberry Pi from church, without needing access to the actual projectors.

## Quick Reference

```bash
# 1. Connect macropad to Pi via USB
# 2. Navigate to project directory
cd /opt/projector-control

# 3. Run with mock projectors
python3 run_macropad_with_mocks.py hid-macropad

# 4. Press buttons and watch the output!
```

**That's it!** The script will:
- Start mock projector servers automatically
- Connect your macropad
- Show you what happens when you press buttons
- Display all commands and responses in the terminal

## Overview

When testing at home, you'll use **mock projectors** - software servers that simulate real PJLink projectors. This allows you to:
- ✅ Test all macropad buttons and functions
- ✅ Verify button mappings work correctly
- ✅ Test power on/off, mute, freeze commands
- ✅ See status responses and state changes
- ✅ Debug any issues before going to church

## Prerequisites

1. **Raspberry Pi** - The Pi from church with the projector control software installed
2. **RP2040 Macropad** - Your Adafruit Macropad RP2040 (or compatible HID macropad)
3. **USB Cable** - To connect the macropad to the Pi
4. **SSH Access** - Or direct access to the Pi (keyboard/monitor)

## Quick Start

### Step 1: Connect Your Macropad

Connect your RP2040 macropad to the Raspberry Pi via USB.

Verify it's detected:
```bash
# Check if device is recognized
lsusb | grep -i "adafruit\|rp2040\|239a"

# Or check all HID devices
ls /dev/input/by-id/ | grep -i keyboard
```

### Step 2: Navigate to Project Directory

```bash
cd /opt/projector-control
# Or wherever you cloned the repository
```

### Step 3: Run with Mock Projectors

The easiest way is to use the built-in mock testing script:

```bash
# For HID macropad (RP2040 in HID mode)
python3 run_macropad_with_mocks.py hid-macropad

# If your macropad acts as a keyboard, use:
python3 run_macropad_with_mocks.py usb-keypad
```

### Step 4: Test Your Buttons

Once running, you should see:
```
🎭 Starting HID Macropad Control with MOCK PROJECTORS
============================================================
✅ Created 2 mock projectors:
   Projector 1: 127.0.0.1:54321 (Power: ON)
   Projector 2: 127.0.0.1:54322 (Power: ON)

🎹 HID Macropad Control Ready!
   Press buttons on your macropad to test
   (All commands will go to mock projectors)
```

Now press buttons on your macropad and watch the terminal for responses!

## Customizing Test Scenarios

### Start with Projectors OFF

```bash
python3 run_macropad_with_mocks.py hid-macropad --power OFF
```

### Test with 3 Mock Projectors (Front + Rear)

```bash
python3 run_macropad_with_mocks.py hid-macropad --num-projectors 3
```

### Test Different Initial States

```bash
# Projectors ON but MUTED and FROZEN
python3 run_macropad_with_mocks.py hid-macropad --power ON --mute MUTED --freeze FROZEN
```

## Understanding the Output

When you press a button, you'll see output like:

```
🎯 BUTTON 1 PRESSED: All On
   Time: 14:32:15
🔌 Turning ON all projectors...
✅ All projectors turned ON successfully
```

This shows:
- **Which button** was pressed
- **What function** it triggered
- **The result** of the command

## Button Mappings

The RP2040 macropad uses these button mappings (from `hid_macropad_control.py`):

- **Button 1**: All On - Turn on all projectors
- **Button 2**: All Off - Turn off all projectors
- **Button 3**: Blank Front - Mute front projectors
- **Button 4**: Unblank Front - Unmute front projectors
- **Button 5**: Freeze Front - Freeze front projectors
- **Button 6**: Unfreeze Front - Unfreeze front projectors

## Troubleshooting

### Macropad Not Detected

If you see "❌ No HID macropad found":

1. **Check USB connection**
   ```bash
   lsusb
   # Look for your device
   ```

2. **Check if device needs VID/PID added**
   - The script searches for common macropad IDs
   - Your RP2040 might have a different VID/PID
   - Check `macropad/hid_macropad_control.py` and add your device's VID/PID

3. **Try keyboard mode instead**
   ```bash
   python3 run_macropad_with_mocks.py usb-keypad
   ```

### Escape Sequences in Terminal (^[OP, ^[OQ, etc.)

If you see escape sequences instead of button presses:

- Your device is acting as a **keyboard**, not raw HID
- **Solution**: Use the keyboard listener approach:
  ```bash
  python3 run_macropad_with_mocks.py usb-keypad
  ```

### Buttons Not Working

1. **Check button mapping**
   - The script expects buttons numbered 1-6
   - Your macropad might send different codes
   - Check the debug output: `🔍 Raw HID data: ...`

2. **Enable debug mode** (already enabled by default in mock mode)
   - Look for raw HID data in the output
   - This shows what your macropad is actually sending

3. **Verify macropad firmware**
   - Make sure your RP2040 is programmed to send HID button codes
   - Check CircuitPython code or firmware settings

### Connection Errors

If you see connection errors to mock projectors:

- The mock servers start automatically
- If errors persist, check that ports aren't blocked:
  ```bash
  netstat -tuln | grep 127.0.0.1
  ```

## Advanced: Manual Testing

If you want more control, you can create a custom test script:

```python
#!/usr/bin/env python3
from tests.mock_macropad_integration import MockMacropadEnvironment
from macropad.hid_macropad_control import HIDMacropadController

# Create mock environment with 2 projectors, starting OFF
mock_env = MockMacropadEnvironment(num_projectors=2, power="OFF")
projectors = mock_env.start()

try:
    # Convert to config format
    mock_projector_config = [
        {'ip': ip, 'port': port} for ip, port in projectors
    ]
    
    # Create controller
    controller = HIDMacropadController(
        projectors=mock_projector_config,
        debug_mode=True
    )
    
    print("✅ Ready! Press buttons on your macropad...")
    controller.run()
    
finally:
    mock_env.stop()
```

Save as `test_macropad_home.py` and run:
```bash
python3 test_macropad_home.py
```

## What Gets Tested

✅ **Button detection** - All buttons are recognized  
✅ **Command execution** - Power, mute, freeze commands work  
✅ **State changes** - Mock projectors change state correctly  
✅ **Status queries** - Getting power/mute/freeze status works  
✅ **Multiple projectors** - Commands affect all projectors  
✅ **Error handling** - Script handles various states gracefully  

## Next Steps

Once testing at home works:

1. **Verify all buttons work** - Test each button multiple times
2. **Test edge cases** - Try rapid button presses, different states
3. **Check logs** - Review `hid_macropad_control.log` for any errors
4. **Take to church** - When ready, test with real projectors!

## Differences: Home vs Church

| Aspect | Home (Mock) | Church (Real) |
|--------|-------------|---------------|
| Projectors | Mock servers on 127.0.0.1 | Real projectors on 10.10.10.x |
| Network | Local only | Requires church network |
| Response time | Instant | Network delay possible |
| State changes | Immediate | May take 1-2 seconds |
| Errors | Simulated | Real network/hardware issues |

## See Also

- `docs/MOCK_TESTING.md` - General mock testing guide
- `docs/MACROPAD_SETUP.md` - Macropad setup and configuration
- `tests/README_MOCKING.md` - Detailed mocking API docs
- `macropad/hid_macropad_control.py` - HID macropad control implementation

