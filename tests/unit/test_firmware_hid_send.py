import importlib
import importlib.util
import unittest


class ScriptedHIDDevice:
    def __init__(self, outcomes, usage_page=None):
        self.outcomes = list(outcomes)
        self.reports = []
        self.usage_page = usage_page

    def send_report(self, report):
        self.reports.append(bytes(report))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome


class FirmwareHIDSendTests(unittest.TestCase):
    def load_sender(self):
        spec = importlib.util.find_spec("macropad.hid_send")
        self.assertIsNotNone(spec, "The CircuitPython HID sender module must exist")
        return importlib.import_module("macropad.hid_send").send_report_with_retry

    def test_usb_busy_gets_exactly_one_retry(self):
        """A transient USB busy error gets one delayed second attempt."""
        send_report_with_retry = self.load_sender()
        device = ScriptedHIDDevice([RuntimeError("USB busy"), None])
        sleeps = []

        self.assertTrue(
            send_report_with_retry(device, bytes([4, 0, 0, 0, 0, 0, 0, 0]), sleeps.append)
        )

        self.assertEqual(2, len(device.reports))
        self.assertEqual([0.25], sleeps)

    def test_circuitpython_oserror_form_is_recognized_as_usb_busy(self):
        """CircuitPython raises OSError, and errno forms carry a prefix."""
        send_report_with_retry = self.load_sender()
        device = ScriptedHIDDevice([OSError("USB busy"), None])
        prefixed = ScriptedHIDDevice([OSError(16, "USB busy"), None])

        self.assertTrue(
            send_report_with_retry(device, bytes(8), lambda _: None)
        )
        self.assertTrue(
            send_report_with_retry(prefixed, bytes(8), lambda _: None)
        )
        self.assertEqual(2, len(device.reports))
        self.assertEqual(2, len(prefixed.reports))

    def test_second_usb_busy_returns_without_more_retries(self):
        """Persistent USB busy returns control after the second failure."""
        send_report_with_retry = self.load_sender()
        device = ScriptedHIDDevice(
            [RuntimeError("USB busy"), RuntimeError("USB busy")]
        )

        self.assertFalse(
            send_report_with_retry(device, bytes([5, 0, 0, 0, 0, 0, 0, 0]), lambda _: None)
        )
        self.assertEqual(2, len(device.reports))

    def test_non_busy_exception_is_not_retried_or_hidden(self):
        """Programming and descriptor errors must remain visible."""
        send_report_with_retry = self.load_sender()
        device = ScriptedHIDDevice([ValueError("wrong report length")])

        with self.assertRaisesRegex(ValueError, "wrong report length"):
            send_report_with_retry(
                device, bytes([1, 0, 0, 0, 0, 0, 0, 0]), lambda _: None
            )

        self.assertEqual(1, len(device.reports))

    def test_discovery_never_falls_back_to_a_generic_hid_interface(self):
        """Production firmware must select only its vendor raw-HID interface."""
        module = importlib.import_module("macropad.hid_send")
        keyboard = ScriptedHIDDevice([], usage_page=0x0001)
        raw_hid = ScriptedHIDDevice([], usage_page=0xFF00)

        self.assertIs(raw_hid, module.find_raw_hid_device([keyboard, raw_hid]))
        self.assertIsNone(module.find_raw_hid_device([keyboard]))


if __name__ == "__main__":
    unittest.main()
