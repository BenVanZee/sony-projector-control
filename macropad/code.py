# CircuitPython code for Adafruit Macropad RP2040
# Sends raw HID reports (button number) — Pi reads via /dev/hidraw*
#
# USB busy is common if send_report is called while the previous report
# has not yet been picked up by the host. Always: retry, send a release,
# and avoid slamming the endpoint on rapid presses.

import board
import keypad
import usb_hid
import time

from hid_send import find_raw_hid_device, send_report_with_retry

# ---------------------------------------------------------------------------
# Discover vendor raw HID device (configured in boot.py)
# ---------------------------------------------------------------------------
raw_hid = find_raw_hid_device(usb_hid.devices)

if raw_hid is None:
    print("ERROR: No raw HID device found!")
    print("Copy boot.py to CIRCUITPY and reset the macropad.")
    for d in usb_hid.devices:
        print(
            "  - usage_page=%s usage=%s"
            % (getattr(d, "usage_page", "N/A"), getattr(d, "usage", "N/A"))
        )
else:
    print("Found raw HID device: usage_page=0xFF00")
    print("Raw HID mode enabled")

# ---------------------------------------------------------------------------
# Keypad
# ---------------------------------------------------------------------------
keys = keypad.Keys(
    pins=(
        board.KEY1,
        board.KEY2,
        board.KEY3,
        board.KEY4,
        board.KEY5,
        board.KEY6,
        board.KEY7,
        board.KEY8,
        board.KEY9,
        board.KEY10,
        board.KEY11,
        board.KEY12,
    ),
    value_when_pressed=False,
    pull=True,
)
print("Keypad initialized")

BUTTON_LABELS = {
    1: "All On",
    2: "All Off",
    3: "Toggle Power",
    4: "Blank Front",
    5: "Unblank Front",
    6: "Toggle Blank",
    7: "Freeze Front",
    8: "Unfreeze Front",
    9: "Toggle Freeze",
    10: "Reserved 10",
    11: "Reserved 11",
    12: "Reserved 12",
}

print("\n" + "=" * 30)
print("Button Functions:")
print("=" * 30)
for n in sorted(BUTTON_LABELS.keys()):
    print("Button %d: %s" % (n, BUTTON_LABELS[n]))
print("=" * 30)
print("\nMacropad ready! Mode: %s" % ("Raw HID" if raw_hid else "disabled"))

# ---------------------------------------------------------------------------
# HID send helpers — survive host not reading for a bit
# ---------------------------------------------------------------------------
REPORT_LEN = 8
RELEASE_REPORT = bytes([0] * REPORT_LEN)
MIN_SEND_INTERVAL = 0.05  # debounce / avoid flood
_last_send_time = 0.0


def send_button(button_num):
    """Send press report then release so host sees a clean edge."""
    global _last_send_time
    now = time.monotonic()
    if now - _last_send_time < MIN_SEND_INTERVAL:
        return False
    _last_send_time = now

    press = bytes([button_num] + [0] * (REPORT_LEN - 1))
    if not send_report_with_retry(raw_hid, press):
        return False
    # Small gap then release (all zeros). Host can treat either as the event.
    time.sleep(0.01)
    send_report_with_retry(raw_hid, RELEASE_REPORT)
    return True


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    try:
        event = keys.events.get()
        if event and event.pressed:
            button_num = event.key_number + 1  # 1-indexed
            func_name = BUTTON_LABELS.get(button_num, "Unknown")

            if raw_hid is not None:
                if send_button(button_num):
                    print("%d: %s" % (button_num, func_name))

        time.sleep(0.01)

    except Exception as e:
        print("Error in loop: %s" % e)
        time.sleep(0.1)
