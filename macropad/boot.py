# boot.py - Runs before code.py to configure USB devices
# This enables raw HID device for direct button reports

import usb_hid

# Define a custom raw HID device descriptor
# This creates a vendor-defined HID device that won't act as keyboard/mouse
RAW_HID_REPORT_DESCRIPTOR = bytes((
    0x06, 0x00, 0xFF,  # Usage Page (Vendor Defined 0xFF00)
    0x09, 0x01,        # Usage (0x01)
    0xA1, 0x01,        # Collection (Application)
    0x09, 0x02,        #   Usage (0x02)
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x00,  #   Logical Maximum (255)
    0x75, 0x08,        #   Report Size (8 bits)
    0x95, 0x08,        #   Report Count (8 bytes)
    0x81, 0x02,        #   Input (Data,Var,Abs)
    0x09, 0x03,        #   Usage (0x03)
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x00,  #   Logical Maximum (255)
    0x75, 0x08,        #   Report Size (8 bits)
    0x95, 0x08,        #   Report Count (8 bytes)
    0x91, 0x02,        #   Output (Data,Var,Abs)
    0xC0,              # End Collection
))

# Create the raw HID device
raw_hid_device = usb_hid.Device(
    report_descriptor=RAW_HID_REPORT_DESCRIPTOR,
    usage_page=0xFF00,         # Vendor defined
    usage=0x01,                # Vendor usage
    report_ids=(0,),           # No report ID
    in_report_lengths=(8,),    # 8 bytes input
    out_report_lengths=(8,),   # 8 bytes output
)

# Enable both the raw HID device and keep keyboard for debugging
# You can remove Keyboard/Mouse if you don't need them
usb_hid.enable((
    raw_hid_device,
    # Uncomment below if you want keyboard as fallback:
    # usb_hid.Device.KEYBOARD,
))

print("boot.py: Raw HID device enabled")
