# CircuitPython code for Adafruit Macropad RP2040
# Sends raw HID reports (button number) — Pi reads via /dev/hidraw*
# Receives status reports from the Pi and lights keys 10-12 (Left, Right, Rear)
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
    10: "Left status",
    11: "Right status",
    12: "Rear status",
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
# Status lights — keys 10-12 show Left, Right, Rear display state
# ---------------------------------------------------------------------------
# The Pi sends: marker byte, one code per projector, zero padding. Codes must
# match STATUS_CODES in hid_macropad_control.py. Colors are (red, green, blue).
STATUS_REPORT_MARKER = 0x53
STATUS_FIRST_KEY = 9  # 0-indexed pixel under key 10
STATUS_LIGHT_COUNT = 3
STATUS_COLORS = {
    1: (0, 0, 0),    # off: unlit
    2: (0, 60, 0),   # on, live picture: green
    3: (50, 25, 0),  # warming or cooling: amber
    4: (60, 0, 0),   # unreachable: red
    5: (40, 0, 50),  # on and blanked: purple
    6: (0, 0, 60),   # on and frozen: blue, as in cold
}
NO_STATUS = (0,) * STATUS_LIGHT_COUNT  # unlit until the Pi's first report
# The Pi repeats its report every 2s. When it stops, or never starts, show
# every projector as unreachable: the buttons cannot reach them either, and
# an unlit row would look the same as three projectors that are off.
PI_SILENT = (4,) * STATUS_LIGHT_COUNT
STATUS_STALE_S = 15
PIXEL_COUNT = 12

# Built-in neopixel_write, so nothing needs copying into CIRCUITPY/lib. Lights
# are optional: any failure here must leave the buttons working.
try:
    import digitalio
    import neopixel_write

    pixel_pin = digitalio.DigitalInOut(board.NEOPIXEL)
    pixel_pin.direction = digitalio.Direction.OUTPUT
except Exception as e:
    print("Status lights disabled: %s" % e)
    pixel_pin = None

pixel_buffer = bytearray(PIXEL_COUNT * 3)
_last_status_time = time.monotonic()


def show_status(codes):
    for offset in range(STATUS_LIGHT_COUNT):
        red, green, blue = STATUS_COLORS.get(codes[offset], (0, 0, 0))
        start = (STATUS_FIRST_KEY + offset) * 3
        # The Macropad's pixels take green first.
        pixel_buffer[start] = green
        pixel_buffer[start + 1] = red
        pixel_buffer[start + 2] = blue
    neopixel_write.neopixel_write(pixel_pin, pixel_buffer)


def update_status_lights():
    global _last_status_time
    now = time.monotonic()
    report = raw_hid.get_last_received_report()
    if report and len(report) > STATUS_LIGHT_COUNT and report[0] == STATUS_REPORT_MARKER:
        show_status(report[1 : 1 + STATUS_LIGHT_COUNT])
        _last_status_time = now
    elif _last_status_time is not None and now - _last_status_time > STATUS_STALE_S:
        show_status(PI_SILENT)
        _last_status_time = None


if pixel_pin is not None:
    try:
        show_status(NO_STATUS)
    except Exception as e:
        print("Status lights disabled: %s" % e)
        pixel_pin = None

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

        if pixel_pin is not None and raw_hid is not None:
            try:
                update_status_lights()
            except Exception as e:
                print("Status lights disabled: %s" % e)
                pixel_pin = None

        time.sleep(0.01)

    except Exception as e:
        print("Error in loop: %s" % e)
        time.sleep(0.1)
