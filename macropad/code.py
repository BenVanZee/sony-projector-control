# CircuitPython code for Adafruit Macropad RP2040
# Sends function keys (F1-F12) instead of numbers to avoid terminal input
# Function keys won't appear as text in terminal

import board
import keypad
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# Initialize keyboard
try:
    kbd = Keyboard(usb_hid.devices)
    print("Keyboard initialized")
except Exception as e:
    print(f"Keyboard init error: {e}")
    raise

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

# Key mappings - send function keys F1-F12 (won't appear as text in terminal)
KEY_MAP = [
    Keycode.F1, Keycode.F2, Keycode.F3, Keycode.F4,
    Keycode.F5, Keycode.F6, Keycode.F7, Keycode.F8,
    Keycode.F9, Keycode.F10, Keycode.F11, Keycode.F12
]

print("Macropad ready - Press keys 1-12 (sends F1-F12)")

# Main loop
while True:
    try:
        event = keys.events.get()
        if event:
            if event.pressed:
                key_index = event.key_number
                if key_index < len(KEY_MAP):
                    kbd.press(KEY_MAP[key_index])
                    print(f"Key {key_index + 1} pressed (F{key_index + 1})")
            elif event.released:
                key_index = event.key_number
                if key_index < len(KEY_MAP):
                    kbd.release(KEY_MAP[key_index])
    except Exception as e:
        print(f"Error in loop: {e}")
        # Continue running even if there's an error
