import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

import macropad.hid_send

CODE_PY = Path(__file__).resolve().parents[2] / "macropad" / "code.py"
LEFT, RIGHT, REAR = 9, 10, 11  # 0-indexed pixels under keys 10, 11, 12


class StopFirmware(BaseException):
    """Ends code.py's endless loop; its own handler only catches Exception."""


class FirmwareHarness:
    """Runs the real code.py against scripted hardware, one loop pass per step."""

    def __init__(self, steps, pixels_fail=False):
        # Each step: (monotonic seconds, received report or None, pressed key or None)
        self.steps = list(steps)
        self.now = 0.0
        self.received = None
        self.pixel_writes = []
        self.sent_reports = []
        self.pixels_fail = pixels_fail

    def next_event(self):
        if not self.steps:
            raise StopFirmware()
        self.now, self.received, key = self.steps.pop(0)
        if key is None:
            return None
        return types.SimpleNamespace(pressed=True, key_number=key)

    def take_report(self):
        report, self.received = self.received, None
        return report

    def write_pixels(self, pin, buffer):
        if self.pixels_fail:
            raise RuntimeError("pixel hardware fault")
        self.pixel_writes.append(bytes(buffer))

    def pixel(self, index):
        """Last written color of one key as (red, green, blue)."""
        green, red, blue = self.pixel_writes[-1][index * 3 : index * 3 + 3]
        return (red, green, blue)

    def run(self):
        raw_hid = types.SimpleNamespace(
            usage_page=0xFF00,
            send_report=self.sent_reports.append,
            get_last_received_report=self.take_report,
        )
        board = types.SimpleNamespace(NEOPIXEL="NEOPIXEL")
        for number in range(1, 13):
            setattr(board, "KEY%d" % number, number)
        keys = types.SimpleNamespace(
            events=types.SimpleNamespace(get=self.next_event)
        )
        stubs = {
            "board": board,
            "keypad": types.SimpleNamespace(Keys=lambda **kwargs: keys),
            "usb_hid": types.SimpleNamespace(devices=[raw_hid]),
            "digitalio": types.SimpleNamespace(
                DigitalInOut=lambda pin: types.SimpleNamespace(direction=None),
                Direction=types.SimpleNamespace(OUTPUT="OUTPUT"),
            ),
            "neopixel_write": types.SimpleNamespace(neopixel_write=self.write_pixels),
            "hid_send": macropad.hid_send,
        }
        with (
            mock.patch.dict(sys.modules, stubs),
            mock.patch("time.sleep"),
            mock.patch("time.monotonic", side_effect=lambda: self.now),
            mock.patch("builtins.print"),
        ):
            try:
                runpy.run_path(str(CODE_PY))
            except StopFirmware:
                pass
        return self


def status_report(left, right, rear):
    return bytes([0x53, left, right, rear, 0, 0, 0, 0])


class FirmwareStatusLightTests(unittest.TestCase):
    def test_status_report_lights_the_bottom_row_only(self):
        """On is green, off is dim, unreachable is red; other keys stay dark."""
        firmware = FirmwareHarness([(1.0, status_report(2, 1, 4), None)]).run()

        self.assertEqual((0, 60, 0), firmware.pixel(LEFT))
        self.assertEqual((4, 4, 4), firmware.pixel(RIGHT))
        self.assertEqual((60, 0, 0), firmware.pixel(REAR))
        self.assertEqual(bytes(LEFT * 3), firmware.pixel_writes[-1][: LEFT * 3])

    def test_warming_and_cooling_show_amber(self):
        firmware = FirmwareHarness([(1.0, status_report(3, 3, 3), None)]).run()

        self.assertEqual((50, 25, 0), firmware.pixel(REAR))

    def test_lights_go_dark_when_the_pi_stops_reporting(self):
        """A stopped service must not leave a stale green light on."""
        firmware = FirmwareHarness(
            [
                (1.0, status_report(2, 2, 2), None),
                (10.0, None, None),
                (17.0, None, None),
            ]
        ).run()

        self.assertEqual(bytes(36), firmware.pixel_writes[-1])

    def test_lights_stay_on_between_reports(self):
        firmware = FirmwareHarness(
            [(1.0, status_report(2, 2, 2), None), (10.0, None, None)]
        ).run()

        self.assertEqual((0, 60, 0), firmware.pixel(LEFT))

    def test_report_without_the_status_marker_is_ignored(self):
        firmware = FirmwareHarness([(1.0, bytes([2, 2, 2, 2, 0, 0, 0, 0]), None)]).run()

        self.assertEqual(bytes(36), firmware.pixel_writes[-1])

    def test_pixel_failure_leaves_buttons_working(self):
        """Lights are optional; a pixel fault must never cost a button press."""
        firmware = FirmwareHarness(
            [(1.0, status_report(2, 2, 2), None), (2.0, None, 1)],
            pixels_fail=True,
        ).run()

        self.assertEqual(bytes([2, 0, 0, 0, 0, 0, 0, 0]), firmware.sent_reports[0])


if __name__ == "__main__":
    unittest.main()
