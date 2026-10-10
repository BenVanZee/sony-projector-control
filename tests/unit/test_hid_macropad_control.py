import errno
import io
import os
import re
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from macropad.hid_macropad_control import (
    MAX_BACKOFF_S,
    STABLE_DEVICE_PATH,
    STATUS_POLL_UNREACHABLE_INTERVAL_S,
    STATUS_RESEND_S,
    HIDMacropadController,
)

KEYBOARD_DESCRIPTOR = b"\x05\x01\x09\x06"  # Usage Page (Generic Desktop), Keyboard
VENDOR_DESCRIPTOR = b"\x06\x00\xff\x09\x01"  # Usage Page (Vendor 0xFF00)
PRODUCTION_UEVENT = (
    "HID_ID=0003:0000239A:00008108\n"
    "HID_NAME=Adafruit Macropad RP2040\n"
    "HID_UNIQ=DF641C0547692E2E\n"
)


class FakeProjector:
    def __init__(self, *, mute=None, freeze=None):
        self.mute = mute
        self.freeze = freeze

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def get_mute_status(self):
        return self.mute

    def get_freeze_status(self):
        return self.freeze


class HIDMacropadControllerTests(unittest.TestCase):
    def make_controller(self):
        return HIDMacropadController(projectors=[], debug_mode=False)

    def test_latest_pending_button_replaces_stale_waiting_button(self):
        """A stale button must not execute after a newer pending intent."""
        controller = self.make_controller()
        first_started = threading.Event()
        release_first = threading.Event()
        actions_finished = threading.Event()
        executed = []

        def first_action():
            executed.append(1)
            first_started.set()
            release_first.wait(timeout=1)

        def second_action():
            executed.append(2)

        def third_action():
            executed.append(3)
            actions_finished.set()

        controller.button_functions = {
            1: ("first", first_action),
            2: ("second", second_action),
            3: ("third", third_action),
        }
        controller.running = True
        worker = threading.Thread(target=controller._action_worker)
        worker.start()

        controller.enqueue_button(1)
        self.assertTrue(first_started.wait(timeout=1))
        controller.enqueue_button(2)
        controller.enqueue_button(3)
        release_first.set()
        self.assertTrue(actions_finished.wait(timeout=1))

        controller.running = False
        worker.join(timeout=1)
        self.assertFalse(worker.is_alive())
        self.assertEqual([1, 3], executed)

    def test_successful_open_does_not_reset_backoff_before_stability(self):
        """An immediately broken reopen must inherit the current backoff."""
        controller = self.make_controller()
        controller.reconnect_attempts = 2

        with (
            mock.patch.object(
                controller,
                "find_hid_macropad",
                return_value=(42, "/dev/sony-macropad"),
            ),
            mock.patch("macropad.hid_macropad_control.time.sleep"),
        ):
            self.assertTrue(controller.reconnect_device())

        self.assertEqual(2, controller.reconnect_attempts)

    def test_reconnect_backoff_is_capped(self):
        """Long outages must never sleep beyond the watchdog-safe cap."""
        controller = self.make_controller()
        controller.reconnect_attempts = 50

        with (
            mock.patch.object(
                controller, "find_hid_macropad", return_value=(None, None)
            ),
            mock.patch("macropad.hid_macropad_control.time.sleep") as sleep,
        ):
            controller.reconnect_device()

        sleep.assert_called_once_with(MAX_BACKOFF_S)

    def test_reconnect_backoff_cap_stays_within_systemd_watchdog(self):
        """The poll loop only heartbeats between sleeps, so the two are coupled."""
        unit = (
            Path(__file__).resolve().parents[2]
            / "systemd"
            / "macropad-control.service"
        )
        match = re.search(r"^WatchdogSec=(\d+)s?$", unit.read_text(), re.MULTILINE)
        self.assertIsNotNone(match, "macropad-control.service must set WatchdogSec")

        self.assertLess(MAX_BACKOFF_S * 2, int(match.group(1)))

    def test_duplicate_button_within_debounce_window_is_ignored(self):
        """One physical edge must not create two pending actions."""
        controller = self.make_controller()

        with mock.patch(
            "macropad.hid_macropad_control.time.monotonic",
            side_effect=[10.0, 10.1],
        ):
            controller.enqueue_button(4)
            controller.enqueue_button(4)

        self.assertEqual(4, controller._pending_button)
        self.assertEqual(10.0, controller._last_button_time)

    def test_disconnected_controller_retries_forever_without_counter_reset(self):
        """Reaching a retry threshold must not create a reset-and-spin cycle."""
        controller = self.make_controller()
        controller.reconnect_attempts = 50

        with mock.patch.object(
            controller, "reconnect_device", return_value=False
        ) as reconnect:
            controller.read_hid_events()

        reconnect.assert_called_once_with()
        self.assertEqual(50, controller.reconnect_attempts)

    def test_absent_device_logs_one_waiting_transition_not_every_retry(self):
        """A long unplugged period must stay quiet after the first state change."""
        controller = self.make_controller()

        with (
            mock.patch.object(
                controller, "find_hid_macropad", return_value=(None, None)
            ),
            mock.patch("macropad.hid_macropad_control.time.sleep"),
            self.assertLogs(controller.logger.name, level="INFO") as captured,
        ):
            controller.reconnect_device()
            controller.reconnect_device()

        waiting = [
            message for message in captured.output if "waiting for exact device" in message
        ]
        self.assertEqual(1, len(waiting))
        self.assertFalse(any("attempt 2" in message for message in captured.output))

    def test_absent_discovery_does_not_print_on_each_poll(self):
        """Raw discovery itself must not flood the journal while unplugged."""
        controller = self.make_controller()

        with (
            mock.patch("macropad.hid_macropad_control.os.path.exists", return_value=False),
            mock.patch("macropad.hid_macropad_control.glob.glob", return_value=[]),
            mock.patch("builtins.print") as output,
        ):
            self.assertEqual((None, None), controller.find_hid_macropad())

        output.assert_not_called()

    def test_identity_requires_matching_vendor_product_and_serial(self):
        """An Adafruit-named device with the wrong product must be rejected."""
        controller = self.make_controller()
        uevent = (
            "HID_ID=0003:0000239A:00009999\n"
            "HID_NAME=Adafruit Macropad RP2040\n"
            "HID_UNIQ=DF641C0547692E2E\n"
        )

        with (
            mock.patch("macropad.hid_macropad_control.os.path.exists", return_value=True),
            mock.patch("builtins.open", mock.mock_open(read_data=uevent)),
        ):
            matches, _, _ = controller._is_adafruit_hidraw("/dev/hidraw9")

        self.assertFalse(matches)

    def test_identity_accepts_the_exact_production_device(self):
        """The deployed VID, PID, and serial combination must be discoverable."""
        controller = self.make_controller()
        uevent = (
            "HID_ID=0003:0000239A:00008108\n"
            "HID_NAME=Adafruit Macropad RP2040\n"
            "HID_UNIQ=DF641C0547692E2E\n"
        )

        with (
            mock.patch("macropad.hid_macropad_control.os.path.exists", return_value=True),
            mock.patch("builtins.open", mock.mock_open(read_data=uevent)),
        ):
            matches, name, _ = controller._is_adafruit_hidraw("/dev/hidraw7")

        self.assertTrue(matches)
        self.assertEqual("Adafruit Macropad RP2040", name)

    def discovery_patches(self, descriptor, hidraw_path="/dev/hidraw3"):
        """Patch discovery so one candidate reports the production identity."""

        def fake_open(path, *args, **kwargs):
            if str(path).endswith("report_descriptor"):
                return io.BytesIO(descriptor)
            return io.StringIO(PRODUCTION_UEVENT)

        return (
            mock.patch(
                "macropad.hid_macropad_control.os.path.exists",
                side_effect=lambda path: path != STABLE_DEVICE_PATH,
            ),
            mock.patch(
                "macropad.hid_macropad_control.glob.glob",
                return_value=[hidraw_path],
            ),
            mock.patch(
                "macropad.hid_macropad_control.os.path.realpath",
                side_effect=lambda path: path,
            ),
            mock.patch("builtins.open", side_effect=fake_open),
        )

    def test_matching_identity_on_a_keyboard_interface_is_never_opened(self):
        """Safe mode re-exposes this VID/PID/serial on non-vendor interfaces."""
        controller = self.make_controller()
        exists, glob_paths, realpath, opener = self.discovery_patches(
            KEYBOARD_DESCRIPTOR
        )

        with (
            exists,
            glob_paths,
            realpath,
            opener,
            mock.patch("macropad.hid_macropad_control.os.open") as opened,
        ):
            self.assertEqual((None, None), controller.find_hid_macropad())

        opened.assert_not_called()
        self.assertEqual("wrong-interface", controller._hid_state)

    def test_vendor_usage_page_interface_is_opened(self):
        """The identity gate must not reject the real production interface."""
        controller = self.make_controller()
        exists, glob_paths, realpath, opener = self.discovery_patches(
            VENDOR_DESCRIPTOR
        )

        with (
            exists,
            glob_paths,
            realpath,
            opener,
            mock.patch("macropad.hid_macropad_control.os.open", return_value=7),
        ):
            self.assertEqual(
                (7, "/dev/hidraw3"), controller.find_hid_macropad()
            )

    def test_report_parser_accepts_only_exact_eight_byte_wire_format(self):
        """Only byte zero may carry a button in the production report."""
        controller = self.make_controller()

        self.assertEqual(10, controller.parse_button_from_report(bytes([10] + [0] * 7)))
        self.assertIsNone(
            controller.parse_button_from_report(bytes([0, 10] + [0] * 6))
        )
        self.assertIsNone(
            controller.parse_button_from_report(bytes([10, 1] + [0] * 6))
        )
        self.assertIsNone(controller.parse_button_from_report(bytes([10])))

    def test_eio_closes_dead_handle_before_reconnect(self):
        """The reproduced EIO path must release hidraw0 before discovery."""
        controller = self.make_controller()
        controller.device = 10
        controller.device_path = "/dev/hidraw0"

        with (
            mock.patch.object(controller, "check_device_health", return_value=True),
            mock.patch(
                "macropad.hid_macropad_control.select.select",
                side_effect=OSError(errno.EIO, "Input/output error"),
            ),
            mock.patch.object(
                controller,
                "find_hid_macropad",
                return_value=(11, "/dev/hidraw1"),
            ),
            mock.patch("macropad.hid_macropad_control.os.close") as close,
            mock.patch("macropad.hid_macropad_control.time.sleep"),
        ):
            controller.read_hid_events()

        close.assert_called_once_with(10)
        self.assertEqual(11, controller.device)
        self.assertEqual("/dev/hidraw1", controller.device_path)

    def test_toggle_blank_uses_first_reachable_front_projector_status(self):
        """A muted first reachable projector must cause an unblank action."""
        controller = self.make_controller()
        controller.manager.controllers = {
            "front-left": FakeProjector(mute="MUTED"),
            "front-right": FakeProjector(mute="UNMUTED"),
        }

        with (
            mock.patch.object(
                controller,
                "get_front_projectors",
                return_value=["front-left", "front-right"],
            ),
            mock.patch.object(controller, "blank_front") as blank,
            mock.patch.object(controller, "unblank_front") as unblank,
        ):
            controller.toggle_blank()

        unblank.assert_called_once_with()
        blank.assert_not_called()

    def test_toggle_power_turns_all_off_when_any_projector_reports_on(self):
        """One ON state chooses all-off even when another projector is unavailable."""
        controller = self.make_controller()
        status = {
            "front-left": {"power": "ON", "online": True},
            "rear": {"power": None, "online": False},
        }

        with (
            mock.patch.object(controller.manager, "get_all_status", return_value=status),
            mock.patch.object(controller, "power_off_all") as power_off,
            mock.patch.object(controller, "power_on_all") as power_on,
        ):
            controller.toggle_power()

        power_off.assert_called_once_with()
        power_on.assert_not_called()

    def test_toggle_power_turns_all_on_when_no_projector_reports_on(self):
        """Known OFF, warming, and unavailable states choose all-on."""
        controller = self.make_controller()
        status = {
            "front-left": {"power": "OFF", "online": True},
            "front-right": {"power": "WARMING", "online": True},
            "rear": {"power": None, "online": False},
        }

        with (
            mock.patch.object(controller.manager, "get_all_status", return_value=status),
            mock.patch.object(controller, "power_off_all") as power_off,
            mock.patch.object(controller, "power_on_all") as power_on,
        ):
            controller.toggle_power()

        power_on.assert_called_once_with()
        power_off.assert_not_called()

    def test_toggle_power_does_nothing_when_no_projector_reports_a_known_state(self):
        """An all-unreachable fleet must not be guessed into a power command."""
        controller = self.make_controller()
        status = {
            "front-left": {"power": None, "online": False},
            "front-right": {"power": "ERR3", "online": True},
            "rear": {"power": None, "online": False},
        }

        with (
            mock.patch.object(controller.manager, "get_all_status", return_value=status),
            mock.patch.object(controller, "power_off_all") as power_off,
            mock.patch.object(controller, "power_on_all") as power_on,
        ):
            controller.toggle_power()

        power_on.assert_not_called()
        power_off.assert_not_called()

    def test_toggle_freeze_uses_first_reachable_front_projector_status(self):
        """A frozen first reachable projector must cause one unfreeze action."""
        controller = self.make_controller()
        controller.manager.controllers = {
            "front-left": FakeProjector(freeze="FROZEN"),
            "front-right": FakeProjector(freeze="NORMAL"),
        }

        with (
            mock.patch.object(
                controller,
                "get_front_projectors",
                return_value=["front-left", "front-right"],
            ),
            mock.patch.object(controller, "freeze_front") as freeze,
            mock.patch.object(controller, "unfreeze_front") as unfreeze,
        ):
            controller.toggle_freeze()

        unfreeze.assert_called_once_with()
        freeze.assert_not_called()

    def test_toggle_blank_does_nothing_when_all_front_states_are_unknown(self):
        """A toggle without a real state must not guess and invert the wrong way."""
        controller = self.make_controller()
        controller.manager.controllers = {
            "front-left": FakeProjector(mute=None),
            "front-right": FakeProjector(mute=None),
        }

        with (
            mock.patch.object(
                controller,
                "get_front_projectors",
                return_value=["front-left", "front-right"],
            ),
            mock.patch.object(controller, "blank_front") as blank,
            mock.patch.object(controller, "unblank_front") as unblank,
        ):
            controller.toggle_blank()

        blank.assert_not_called()
        unblank.assert_not_called()

    def test_unrecoverable_run_error_is_propagated_to_service_wrapper(self):
        """A broken internal loop must make systemd observe a failed process."""
        controller = self.make_controller()

        with mock.patch.object(
            controller,
            "read_hid_events",
            side_effect=RuntimeError("reader invariant failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "reader invariant failed"):
                controller.run()

    def test_disconnected_poll_emits_service_heartbeat(self):
        """Waiting for hardware still proves the service loop is responsive."""
        heartbeats = []
        controller = HIDMacropadController(
            projectors=[], debug_mode=False, heartbeat=lambda: heartbeats.append(True)
        )

        with mock.patch.object(controller, "reconnect_device", return_value=False):
            controller.read_hid_events()

        self.assertEqual([True], heartbeats)

    def test_heartbeat_is_rate_limited_below_the_poll_frequency(self):
        """A 100ms poll loop must not emit a watchdog datagram every pass."""
        heartbeats = []
        controller = HIDMacropadController(
            projectors=[], debug_mode=False, heartbeat=lambda: heartbeats.append(True)
        )

        with mock.patch.object(controller, "reconnect_device", return_value=False):
            for _ in range(5):
                controller.read_hid_events()

        self.assertEqual(1, len(heartbeats))

    def test_dead_action_worker_prevents_service_heartbeat(self):
        """Systemd must restart a process whose projector worker has died."""
        heartbeat = mock.Mock()
        controller = HIDMacropadController(
            projectors=[], debug_mode=False, heartbeat=heartbeat
        )
        controller._worker = mock.Mock()
        controller._worker.is_alive.return_value = False

        with self.assertRaisesRegex(RuntimeError, "action worker stopped"):
            controller.read_hid_events()

        heartbeat.assert_not_called()

    def make_status_controller(self, states):
        """Three configured projectors whose status poll returns ``states``."""
        projectors = [
            {"ip": "10.0.0.1", "port": 4352, "nickname": "left"},
            {"ip": "10.0.0.2", "port": 4352, "nickname": "right"},
            {"ip": "10.0.0.3", "port": 4352, "nickname": "rear"},
        ]
        controller = HIDMacropadController(projectors=projectors, debug_mode=False)
        controller.status_manager = mock.Mock()
        controller.status_manager.run_on.return_value = dict(
            zip(["10.0.0.1", "10.0.0.2", "10.0.0.3"], states)
        )
        return controller

    def test_status_poll_stages_one_code_per_projector_in_config_order(self):
        """Keys 10-12 follow Left, Right, Rear; no answer means unreachable."""
        controller = self.make_status_controller(["ON", "WARMING", None])

        controller._poll_status_if_due()

        self.assertEqual(
            bytes([0x53, 2, 3, 4, 0, 0, 0, 0]), controller._status_report
        )
        controller.status_manager.run_on.assert_called_once_with(
            ["10.0.0.1", "10.0.0.2", "10.0.0.3"], "get_display_state"
        )

    def test_blanked_and_frozen_projectors_get_their_own_codes(self):
        controller = self.make_status_controller(["BLANKED", "FROZEN", "ON"])

        controller._poll_status_if_due()

        self.assertEqual(
            bytes([0x53, 5, 6, 2, 0, 0, 0, 0]), controller._status_report
        )

    def test_status_poll_waits_for_its_interval(self):
        """The worker loop wakes twice a second; it must not poll that often."""
        controller = self.make_status_controller(["ON", "ON", "OFF"])

        controller._poll_status_if_due()
        controller._poll_status_if_due()

        self.assertEqual(1, controller.status_manager.run_on.call_count)

    def test_unreachable_projector_slows_the_status_poll(self):
        """Connect timeouts must rarely sit in front of a button press."""
        controller = self.make_status_controller(["ON", "ON", None])

        with mock.patch(
            "macropad.hid_macropad_control.time.monotonic", return_value=100.0
        ):
            controller._poll_status_if_due()

        self.assertEqual(100.0 + STATUS_POLL_UNREACHABLE_INTERVAL_S, controller._next_status_poll)

    def test_status_poll_runs_only_when_no_button_is_waiting(self):
        """A button action and a poll never overlap: one PJLink connection."""
        controller = self.make_status_controller(["ON", "ON", "ON"])
        order = []
        polled_after_button = threading.Event()

        def poll(*args):
            order.append("poll")
            if "button" in order:
                polled_after_button.set()
            return {}

        controller.status_manager.run_on.side_effect = poll
        controller.button_functions = {1: ("first", lambda: order.append("button"))}
        controller._pending_button = 1
        controller.running = True
        worker = threading.Thread(target=controller._action_worker)
        worker.start()
        self.assertTrue(polled_after_button.wait(timeout=2))
        controller.running = False
        with controller._action_condition:
            controller._action_condition.notify_all()
        worker.join(timeout=2)

        self.assertEqual(["button", "poll"], order[:2])

    def test_status_report_is_written_with_a_zero_report_id_and_rate_limited(self):
        controller = self.make_status_controller(["ON", "OFF", "ON"])
        controller._poll_status_if_due()
        controller.device = 7

        with mock.patch("macropad.hid_macropad_control.os.write") as written:
            controller._send_status_report()
            controller._send_status_report()

        written.assert_called_once_with(
            7, bytes([0, 0x53, 2, 1, 2, 0, 0, 0, 0])
        )

    def test_unchanged_status_report_is_repeated_after_the_resend_interval(self):
        """A replugged Macropad relights without waiting for a state change."""
        controller = self.make_status_controller(["ON", "OFF", "ON"])
        controller._poll_status_if_due()
        controller.device = 7

        with (
            mock.patch("macropad.hid_macropad_control.os.write") as written,
            mock.patch(
                "macropad.hid_macropad_control.time.monotonic",
                side_effect=[50.0, 50.0 + STATUS_RESEND_S],
            ),
        ):
            controller._send_status_report()
            controller._send_status_report()

        self.assertEqual(2, written.call_count)

    def test_failed_status_write_does_not_disturb_the_service(self):
        controller = self.make_status_controller(["ON", "OFF", "ON"])
        controller._poll_status_if_due()
        controller.device = 7

        with mock.patch(
            "macropad.hid_macropad_control.os.write",
            side_effect=OSError(errno.EIO, "gone"),
        ):
            controller._send_status_report()

        self.assertEqual(7, controller.device)

    def test_macropad_is_opened_read_write_for_status_reports(self):
        controller = self.make_controller()
        exists, glob_paths, realpath, opener = self.discovery_patches(
            VENDOR_DESCRIPTOR
        )

        with (
            exists,
            glob_paths,
            realpath,
            opener,
            mock.patch(
                "macropad.hid_macropad_control.os.open", return_value=7
            ) as opened,
        ):
            controller.find_hid_macropad()

        self.assertTrue(opened.call_args.args[1] & os.O_RDWR)


if __name__ == "__main__":
    unittest.main()
