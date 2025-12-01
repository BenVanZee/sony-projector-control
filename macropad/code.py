# CircuitPython code for Adafruit Macropad RP2040
# Uses RAW HID to send button presses - won't interfere with terminal
# The Raspberry Pi reads these reports directly via /dev/hidraw*

import board
import keypad
import usb_hid
import time

# Find the raw HID device (not keyboard/mouse)
raw_hid = None
for device in usb_hid.devices:
    # Look for a device with usage_page=0xFF00 (vendor-defined) or usage=0x01
    # The default CircuitPython includes a raw HID device
    if hasattr(device, 'usage_page') and device.usage_page == 0xFF00:
        raw_hid = device
        print(f"Found raw HID device: usage_page={hex(device.usage_page)}")
        break
    elif hasattr(device, 'usage') and device.usage == 0x01 and not hasattr(device, 'send_report'):
        # Fallback: try to find any suitable device
        pass

if raw_hid is None:
    # If no raw HID found, try to use first available that's not keyboard/mouse
    for device in usb_hid.devices:
        try:
            # Test if we can send reports
            if hasattr(device, 'send_report'):
                raw_hid = device
                print(f"Using HID device for raw reports")
                break
        except:
            continue

if raw_hid is None:
    print("ERROR: No raw HID device found!")
    print("You may need to add boot.py to enable raw HID")
    print("Available devices:")
    for d in usb_hid.devices:
        print(f"  - usage_page={getattr(d, 'usage_page', 'N/A')}, usage={getattr(d, 'usage', 'N/A')}")
    # Fall back to keyboard mode
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.keycode import Keycode
    USE_RAW_HID = False
    kbd = Keyboard(usb_hid.devices)
    print("Falling back to keyboard mode (F1-F12)")
else:
    USE_RAW_HID = True
    print("Raw HID mode enabled - button presses won't affect terminal")

# Initialize keypad (12 keys on Macropad RP2040)
try:
    keys = keypad.Keys(
        pins=(board.KEY1, board.KEY2, board.KEY3, board.KEY4,
              board.KEY5, board.KEY6, board.KEY7, board.KEY8,
              board.KEY9, board.KEY10, board.KEY11, board.KEY12),
        value_when_pressed=False,
        pull=True
    )
    print("Keypad initialized")
except Exception as e:
    print(f"Keypad init error: {e}")
    raise

# For keyboard fallback
KEY_MAP = None
if not USE_RAW_HID:
    from adafruit_hid.keycode import Keycode
    KEY_MAP = [
        Keycode.F1, Keycode.F2, Keycode.F3, Keycode.F4,
        Keycode.F5, Keycode.F6, Keycode.F7, Keycode.F8,
        Keycode.F9, Keycode.F10, Keycode.F11, Keycode.F12
    ]

print("Macropad ready!")
if USE_RAW_HID:
    print("Mode: Raw HID (button number sent directly)")
else:
    print("Mode: Keyboard (F1-F12 keys)")

# Main loop
while True:
    try:
        event = keys.events.get()
        if event and event.pressed:
            key_index = event.key_number
            button_num = key_index + 1  # 1-indexed button number
            
            if USE_RAW_HID:
                # Send raw HID report: [button_number, 0, 0, 0, ...]
                # First byte is the button number (1-12)
                # Report is typically 8 or 16 bytes
                report = bytes([button_num] + [0] * 7)  # 8-byte report
                try:
                    raw_hid.send_report(report)
                    print(f"Button {button_num} pressed (raw HID)")
                except Exception as e:
                    print(f"Send error: {e}")
            else:
                # Keyboard fallback
                if key_index < len(KEY_MAP):
                    kbd.press(KEY_MAP[key_index])
                    kbd.release_all()
                    print(f"Key {button_num} pressed (F{button_num})")
                    
        # Small delay to debounce
        time.sleep(0.01)
        
    except Exception as e:
        print(f"Error in loop: {e}")
        time.sleep(0.1)  # Longer delay on error
