"""CircuitPython-safe bounded raw HID sending."""

import time


USB_BUSY_MESSAGE = "USB busy"
USB_BUSY_RETRY_DELAY_S = 0.25


def find_raw_hid_device(devices):
    """Return only the vendor-defined raw-HID interface from boot.py."""
    for device in devices:
        if getattr(device, "usage_page", None) == 0xFF00:
            return device
    return None


def _is_usb_busy(error):
    """CircuitPython raises OSError('USB busy') when the endpoint is not ready.

    Substring rather than equality: the message is translatable, and the
    OSError(errno, strerror) form stringifies with an '[Errno n] ' prefix.
    """
    return USB_BUSY_MESSAGE in str(error)


def send_report_with_retry(device, report, sleep=time.sleep):
    """Send once, retry one USB-busy failure, and expose all other errors."""
    try:
        device.send_report(report)
        return True
    except Exception as error:
        if not _is_usb_busy(error):
            raise

    sleep(USB_BUSY_RETRY_DELAY_S)
    try:
        device.send_report(report)
        return True
    except Exception as error:
        if not _is_usb_busy(error):
            raise
        print("Send error: USB busy (after one retry)")
        return False
