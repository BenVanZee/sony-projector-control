#!/usr/bin/env python3
"""
HID Macropad Control for Sony Projector System

Reads Adafruit Macropad RP2040 raw HID reports from /dev/hidraw* and
dispatches projector commands.

Important design notes:
  - HID reads must never block on projector network I/O.
  - A disconnected hidraw descriptor remains open but returns EIO forever, so
    fatal reads must close it before discovery opens the re-enumerated device.
  - Button actions run on a worker while the main loop owns HID lifecycle.
  - Status polls for the key lights run on that same worker between buttons.
    The projectors accept one PJLink connection at a time, so a poll must
    never overlap a button action.
"""

from __future__ import annotations

import errno
import fcntl
import glob
import logging
import os
import select
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

# Repo root for config / projector_control
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from projector_control import ProjectorManager  # noqa: E402


# Production Macropad identity from /sys/class/hidraw/*/device/uevent.
ADAFRUIT_VENDOR_ID = "239A"
ADAFRUIT_PRODUCT_ID = "8108"
ADAFRUIT_SERIAL = "DF641C0547692E2E"
STABLE_DEVICE_PATH = "/dev/sony-macropad"
# First three bytes of the boot.py report descriptor: Usage Page (Vendor 0xFF00).
# Identity alone is not enough — a Macropad in CircuitPython safe mode enumerates
# extra hidraw interfaces with the same VID/PID/serial.
VENDOR_USAGE_PAGE_PREFIX = b"\x06\x00\xff"
# Button report: first non-zero byte in 1..12 is the button number
BUTTON_MIN, BUTTON_MAX = 1, 12
# Ignore repeated same-button reports within this window (seconds)
DEBOUNCE_S = 0.25
# Max reconnect sleep (seconds). The main loop only pings the systemd watchdog
# between backoff sleeps, so this must stay well under WatchdogSec in
# systemd/macropad-control.service. test_reconnect_backoff_cap_stays_within_
# systemd_watchdog enforces the relationship.
MAX_BACKOFF_S = 8
INITIAL_BACKOFF_S = 0.25
HEALTHY_CONNECTION_S = 5.0
# Ping the watchdog at most this often; the poll loop runs ~10x/second
HEARTBEAT_INTERVAL_S = 2.0
# Status lights: keys 10-12 show the display state of the first three projectors
# in config order (Left, Right, Rear). The report is the marker byte, one code
# per projector, then zero padding. Codes must match STATUS_COLORS in code.py.
STATUS_REPORT_MARKER = 0x53
STATUS_LIGHT_COUNT = 3
STATUS_UNREACHABLE = 4
STATUS_CODES = {
    "OFF": 1,
    "ON": 2,
    "WARMING": 3,
    "COOLING": 3,
    "BLANKED": 5,
    "FROZEN": 6,
}
STATUS_POLL_INTERVAL_S = 5.0
# Poll less often while a projector is unreachable, so its connect timeouts
# rarely sit in front of a button press.
STATUS_POLL_UNREACHABLE_INTERVAL_S = 20.0
# A button pressed during a poll waits for it. Two connect attempts at this
# timeout bound that wait when a projector is unreachable.
STATUS_POLL_TIMEOUT_S = 1.0
# Repeat an unchanged report so a replugged Macropad relights, and so the
# firmware can tell a silent service from an unchanged projector.
STATUS_RESEND_S = 2.0
HID_REPORT_LEN = 8
# Re-log a persistent error state this often so a bad udev rule stays visible
PROBLEM_STATE_RELOG_S = 300.0


class HIDMacropadController:
    """HID macropad controller for projector control."""

    def __init__(
        self,
        projectors: list,
        debug_mode: bool = True,
        heartbeat: Optional[Callable[[], None]] = None,
    ):
        self.projectors = projectors
        self.debug_mode = debug_mode
        self._heartbeat = heartbeat or (lambda: None)

        projector_tuples = [(p["ip"], p["port"]) for p in projectors]
        self.manager = ProjectorManager(projector_tuples)
        self.status_manager = ProjectorManager(
            projector_tuples, timeout=STATUS_POLL_TIMEOUT_S, quiet=True
        )
        self._status_report: Optional[bytes] = None
        self._status_sent: Optional[bytes] = None
        self._status_sent_time = 0.0
        self._next_status_poll = 0.0

        self.running = False
        self.device: Optional[int] = None
        self.device_path: Optional[str] = None
        self.reconnect_attempts = 0
        self._connected_since: Optional[float] = None
        self._hid_state = "starting"
        self._hid_state_logged = 0.0
        # None rather than 0.0: monotonic() is uptime on Linux, so a service
        # started seconds after boot would otherwise skip its first ping.
        self._last_heartbeat: Optional[float] = None

        self._action_condition = threading.Condition()
        self._pending_button: Optional[int] = None
        self._worker: Optional[threading.Thread] = None
        self._last_button: Optional[int] = None
        self._last_button_time = 0.0

        # Row layout for 12-button Adafruit Macropad
        self.button_functions: Dict[int, Tuple[str, Callable[[], None]]] = {
            1: ("All On", self.power_on_all),
            2: ("All Off", self.power_off_all),
            3: ("Toggle Power", self.toggle_power),
            4: ("Blank Front", self.blank_front),
            5: ("Unblank Front", self.unblank_front),
            6: ("Toggle Blank", self.toggle_blank),
            7: ("Freeze Front", self.freeze_front),
            8: ("Unfreeze Front", self.unfreeze_front),
            9: ("Toggle Freeze", self.toggle_freeze),
            10: ("Reserved 10", self.reserved_button),
            11: ("Reserved 11", self.reserved_button),
            12: ("Reserved 12", self.reserved_button),
        }

        self.logger = logging.getLogger(__name__)

    def _set_hid_state(self, state: str, message: str, level: int) -> None:
        """Log a HID state on change, and repeat persistent errors periodically.

        Transitions log once so a routine unplug does not flood the journal. An
        error state is different: a wrong udev rule would otherwise produce one
        line at boot and then permanent silence on a service that stays active.
        """
        now = time.monotonic()
        if state == self._hid_state:
            if level < logging.ERROR:
                return
            if now - self._hid_state_logged < PROBLEM_STATE_RELOG_S:
                return
        self._hid_state = state
        self._hid_state_logged = now
        self.logger.log(level, message)

    def _notify_watchdog(self) -> None:
        """Ping the systemd watchdog, rate-limited to HEARTBEAT_INTERVAL_S."""
        now = time.monotonic()
        if (
            self._last_heartbeat is not None
            and now - self._last_heartbeat < HEARTBEAT_INTERVAL_S
        ):
            return
        self._last_heartbeat = now
        self._heartbeat()

    # ------------------------------------------------------------------
    # Projector helpers
    # ------------------------------------------------------------------
    def get_front_projectors(self) -> List[str]:
        try:
            from config import PROJECTOR_ALIASES, PROJECTOR_GROUPS

            front_nicknames = PROJECTOR_GROUPS.get("front", [])
            return [PROJECTOR_ALIASES.get(nick, nick) for nick in front_nicknames]
        except ImportError:
            return ["10.10.10.2", "10.10.10.3"]

    def _run_on_front(
        self, label: str, op_name: str, method_name: str, *method_args
    ) -> None:
        """Apply a ProjectorController method to each front projector."""
        print(f"{label}...")
        try:
            front_ips = self.get_front_projectors()
            raw_results = self.manager.run_on(front_ips, method_name, *method_args)
            results = {}
            for ip in front_ips:
                if ip not in self.manager.controllers:
                    print(f"⚠️  Front projector {ip} not found in manager")
                    results[ip] = False
                else:
                    results[ip] = bool(raw_results.get(ip))

            ok = sum(1 for v in results.values() if v)
            total = len(results)
            if total == 0:
                print(f"❌ No front projectors configured for {op_name}")
            elif ok == total:
                print(f"✅ Front projectors {op_name} successfully")
            else:
                print(f"❌ Failed to {op_name} {total - ok} of {total} front projectors")
        except Exception as e:
            print(f"❌ Error {op_name}: {e}")
            self.logger.error(f"{op_name} error: {e}")

    def power_on_all(self):
        print("🔌 Turning ON all projectors...")
        try:
            results = self.manager.power_all(True)
            self._report_bulk("turn on", results)
        except Exception as e:
            print(f"❌ Error turning on projectors: {e}")
            self.logger.error(f"Power on error: {e}")

    def power_off_all(self):
        print("🔌 Turning OFF all projectors...")
        try:
            results = self.manager.power_all(False)
            self._report_bulk("turn off", results)
        except Exception as e:
            print(f"❌ Error turning off projectors: {e}")
            self.logger.error(f"Power off error: {e}")

    def _report_bulk(self, action: str, results: dict) -> None:
        ok = sum(1 for v in results.values() if v)
        total = len(results)
        if ok == total:
            print(f"✅ All projectors {action} successfully")
        else:
            print(f"❌ Failed to {action} {total - ok} of {total} projectors")

    def blank_front(self):
        self._run_on_front("🎬 Blanking front projectors", "blank", "set_mute", True)

    def unblank_front(self):
        self._run_on_front(
            "🎬 Unblanking front projectors", "unblank", "set_mute", False
        )

    def freeze_front(self):
        self._run_on_front(
            "⏸️  Freezing front projectors", "freeze", "freeze_screen", True
        )

    def unfreeze_front(self):
        self._run_on_front(
            "▶️  Unfreezing front projectors", "unfreeze", "freeze_screen", False
        )

    def toggle_power(self):
        print("🔌 Toggling power...")
        try:
            status = self.manager.get_all_status()
            unavailable = [
                ip for ip, info in status.items() if not info or not info.get("online")
            ]
            known_power_states = {"ON", "OFF", "COOLING", "WARMING"}
            unknown = [
                ip
                for ip, info in status.items()
                if info
                and info.get("online")
                and info.get("power") not in known_power_states
            ]
            self._report_state_gaps("power", unavailable, unknown)
            known = [
                info
                for info in status.values()
                if info
                and info.get("online")
                and info.get("power") in known_power_states
            ]
            if not known:
                print("❌ Cannot toggle power: no projector returned a known state")
                self.logger.warning(
                    "Refusing power toggle: no projector returned a known state"
                )
                return
            any_on = any(info.get("power") == "ON" for info in known)
            if any_on:
                self.power_off_all()
            else:
                self.power_on_all()
        except Exception as e:
            print(f"❌ Error toggling power: {e}")
            self.logger.error(f"Toggle power error: {e}")

    def toggle_blank(self):
        print("🎬 Toggling blank...")
        try:
            status = self._first_front_state(
                "blank", "get_mute_status", {"MUTED", "UNMUTED"}
            )
            if status is None:
                return
            if status == "MUTED":
                self.unblank_front()
            else:
                self.blank_front()
        except Exception as e:
            print(f"❌ Error toggling blank: {e}")
            self.logger.error(f"Toggle blank error: {e}")

    def toggle_freeze(self):
        print("⏸️  Toggling freeze...")
        try:
            status = self._first_front_state(
                "freeze", "get_freeze_status", {"FROZEN", "NORMAL"}
            )
            if status is None:
                return
            if status == "FROZEN":
                self.unfreeze_front()
            else:
                self.freeze_front()
        except Exception as e:
            print(f"❌ Error toggling freeze: {e}")
            self.logger.error(f"Toggle freeze error: {e}")

    def _first_front_state(
        self, label: str, getter_name: str, valid_states: set
    ) -> Optional[str]:
        """Return the first reachable front state without guessing on failure."""
        unavailable = []
        unknown = []
        for ip in self.get_front_projectors():
            controller = self.manager.controllers.get(ip)
            if controller is None:
                unavailable.append(ip)
                continue
            try:
                with controller:
                    status = getattr(controller, getter_name)()
            except Exception as e:
                unavailable.append(ip)
                self.logger.warning("Unable to read %s state from %s: %s", label, ip, e)
                continue
            if status not in valid_states:
                unknown.append(ip)
                continue

            self._report_state_gaps(label, unavailable, unknown)
            return status

        self._report_state_gaps(label, unavailable, unknown)
        print(f"❌ Cannot toggle {label}: no front projector returned a known state")
        return None

    def _report_state_gaps(
        self, label: str, unavailable: List[str], unknown: List[str]
    ) -> None:
        if unavailable:
            message = f"{label} unavailable: {', '.join(unavailable)}"
            print(f"⚠️  {message}")
            self.logger.warning(message)
        if unknown:
            message = f"{label} unknown: {', '.join(unknown)}"
            print(f"⚠️  {message}")
            self.logger.warning(message)

    def reserved_button(self):
        print(
            "⚠️  This button is not assigned. "
            "Edit button_functions in hid_macropad_control.py to assign it."
        )

    # ------------------------------------------------------------------
    # HID device management
    # ------------------------------------------------------------------
    def _close_device(self) -> None:
        if self.device is not None:
            try:
                os.close(self.device)
            except OSError as e:
                self.logger.debug(f"Error closing device: {e}")
            self.device = None
            self.device_path = None
            self._connected_since = None

    def check_device_health(self) -> bool:
        if self.device is None:
            return False
        try:
            fcntl.fcntl(self.device, fcntl.F_GETFD)
            # Path removed (unplug) even if fd still "valid"
            if self.device_path and not os.path.exists(self.device_path):
                return False
            return True
        except OSError as e:
            if e.errno in (errno.EBADF, errno.ENODEV):
                return False
            return True

    def _is_adafruit_hidraw(self, hidraw_path: str) -> Tuple[bool, str, str]:
        basename = os.path.basename(os.path.realpath(hidraw_path))
        uevent_path = f"/sys/class/hidraw/{basename}/device/uevent"
        device_name = ""
        hid_id = ""
        serial = ""
        if os.path.exists(uevent_path):
            with open(uevent_path) as f:
                for line in f:
                    if line.startswith("HID_NAME="):
                        device_name = line.split("=", 1)[1].strip()
                    elif line.startswith("HID_ID="):
                        hid_id = line.split("=", 1)[1].strip()
                    elif line.startswith("HID_UNIQ="):
                        serial = line.split("=", 1)[1].strip()

        id_parts = hid_id.upper().split(":")
        vendor = id_parts[-2].lstrip("0") if len(id_parts) >= 3 else ""
        product = id_parts[-1].lstrip("0") if len(id_parts) >= 3 else ""
        is_adafruit = (
            vendor == ADAFRUIT_VENDOR_ID
            and product == ADAFRUIT_PRODUCT_ID
            and serial == ADAFRUIT_SERIAL
        )
        return is_adafruit, device_name, hid_id

    def _has_vendor_usage_page(self, hidraw_path: str) -> bool:
        """Confirm this interface is the boot.py vendor collection.

        VID/PID/serial identify the board, not the interface. If boot.py fails
        to run, CircuitPython restores its default HID set and several hidraw
        nodes share that identity, any of which udev may point the symlink at.
        Binding a keyboard interface would look healthy and deliver nothing.
        """
        basename = os.path.basename(os.path.realpath(hidraw_path))
        descriptor_path = f"/sys/class/hidraw/{basename}/device/report_descriptor"
        try:
            with open(descriptor_path, "rb") as descriptor:
                return descriptor.read(3) == VENDOR_USAGE_PAGE_PREFIX
        except OSError as e:
            self.logger.debug("Unable to read %s: %s", descriptor_path, e)
            return False

    def find_hid_macropad(self) -> Tuple[Optional[int], Optional[str]]:
        """Find and open Adafruit Macropad hidraw device.

        Do not open random HID devices by default — that can steal input from
        keyboards and leave the real macropad undrained (USB busy on device).
        """
        candidates = []
        if os.path.exists(STABLE_DEVICE_PATH):
            candidates.append(STABLE_DEVICE_PATH)
        known_real_paths = {os.path.realpath(path) for path in candidates}
        candidates.extend(
            path
            for path in sorted(glob.glob("/dev/hidraw*"))
            if os.path.realpath(path) not in known_real_paths
        )
        if not candidates:
            return None, None

        for hidraw_path in candidates:
            try:
                is_adafruit, device_name, hid_id = self._is_adafruit_hidraw(
                    hidraw_path
                )
                if self.debug_mode:
                    self.logger.debug(
                        "HID candidate %s: %s (%s)",
                        hidraw_path,
                        device_name,
                        hid_id,
                    )

                if not is_adafruit:
                    continue

                if not self._has_vendor_usage_page(hidraw_path):
                    self._set_hid_state(
                        "wrong-interface",
                        f"{hidraw_path} matches the Macropad but is not the "
                        "vendor raw-HID interface; check that boot.py ran",
                        logging.WARNING,
                    )
                    continue

                # Read-write: button reports come in, status reports go out.
                fd = os.open(hidraw_path, os.O_RDWR | os.O_NONBLOCK)
                return fd, hidraw_path
            except PermissionError:
                self._set_hid_state(
                    "permission-error",
                    "Permission denied for exact Macropad; check udev rule and group",
                    logging.ERROR,
                )
            except OSError as e:
                self.logger.debug("Failed to open %s: %s", hidraw_path, e)

        return None, None

    def reconnect_device(self) -> bool:
        """Close and reopen the HID device with exponential backoff."""
        attempt = self.reconnect_attempts + 1
        self.logger.debug("HID reconnect attempt %s", attempt)
        old_path = self.device_path
        self._close_device()

        if self.reconnect_attempts > 0:
            wait_time = min(
                INITIAL_BACKOFF_S * (2 ** (self.reconnect_attempts - 1)),
                MAX_BACKOFF_S,
            )
            self.logger.debug("Waiting %ss before HID reconnection", wait_time)
            time.sleep(wait_time)

        try:
            fd, path = self.find_hid_macropad()
            if fd is not None:
                self.device = fd
                self.device_path = path
                self._connected_since = time.monotonic()
                self._set_hid_state(
                    "connected", f"Macropad connected: {path}", logging.INFO
                )
                if old_path and path != old_path:
                    self.logger.info(f"Device path changed {old_path} → {path}")
                return True
            self.reconnect_attempts += 1
            if self._hid_state != "permission-error":
                self._set_hid_state(
                    "waiting",
                    "Macropad absent; waiting for exact device with capped backoff",
                    logging.WARNING,
                )
            self.logger.debug("HID reconnect attempt %s found no device", attempt)
            return False
        except Exception as e:
            self.reconnect_attempts += 1
            self._set_hid_state(
                "discovery-error",
                f"Macropad discovery error; retrying: {e}",
                logging.ERROR,
            )
            return False

    # ------------------------------------------------------------------
    # Button handling (queued; never blocks HID drain)
    # ------------------------------------------------------------------
    def _action_worker(self) -> None:
        while True:
            with self._action_condition:
                if self._pending_button is None and self.running:
                    self._action_condition.wait(timeout=0.5)
                if self._pending_button is None and not self.running:
                    return
                button_num = self._pending_button
                self._pending_button = None
            if button_num is None:
                self._poll_status_if_due()
                continue
            self._execute_button(button_num)
            # Refresh the lights as soon as the worker is idle again.
            self._next_status_poll = 0.0

    def _execute_button(self, button_num: int) -> None:
        if button_num not in self.button_functions:
            if self.debug_mode:
                print(f"⚠️  Unknown button: {button_num}")
            return
        func_name, func = self.button_functions[button_num]
        try:
            # Inside the try: a stdout encoding that cannot carry the emoji
            # would otherwise kill the worker and restart-loop the service.
            print(f"\n🎯 BUTTON {button_num} PRESSED: {func_name}")
            print(f"   Time: {time.strftime('%H:%M:%S')}")
            func()
        except Exception as e:
            print(f"   ❌ Error executing {func_name}: {e}")
            self.logger.error(f"Button {button_num} error: {e}")

    def enqueue_button(self, button_num: int) -> None:
        """Debounce and queue a button press for the worker thread."""
        now = time.monotonic()
        if (
            button_num == self._last_button
            and (now - self._last_button_time) < DEBOUNCE_S
        ):
            return
        self._last_button = button_num
        self._last_button_time = now

        with self._action_condition:
            replaced = self._pending_button
            self._pending_button = button_num
            self._action_condition.notify()
        if replaced is not None:
            self.logger.info(
                "Replaced pending button %s with latest button %s",
                replaced,
                button_num,
            )

    def parse_button_from_report(self, data: bytes) -> Optional[int]:
        """Parse button number from raw HID report.

        Firmware sends [button, 0, 0, ...] then a release [0, 0, ...].
        Only non-zero button numbers are events.
        """
        if len(data) != 8 or any(data[1:]):
            return None
        if BUTTON_MIN <= data[0] <= BUTTON_MAX:
            return data[0]
        return None

    def _drain_hid(self) -> None:
        """Read all currently available HID reports without blocking long."""
        if self.device is None:
            return

        # Multiple short reads: empty kernel buffer even if reports piled up
        for _ in range(32):
            try:
                readable, _, _ = select.select([self.device], [], [], 0)
                if not readable:
                    break
                data = os.read(self.device, 64)
            except BlockingIOError:
                break
            except OSError:
                raise

            if not data:
                break

            button = self.parse_button_from_report(data)
            if button is not None:
                self.enqueue_button(button)
            elif self.debug_mode and any(data):
                print(f"🔍 Raw HID data: {data.hex()}")

    def read_hid_events(self) -> None:
        """Poll the HID device; queue button work but always keep reading."""
        if self._worker is not None and not self._worker.is_alive():
            raise RuntimeError("Macropad action worker stopped")

        if self.device is None:
            self.reconnect_device()
            self._notify_watchdog()
            return

        if not self.check_device_health():
            self._set_hid_state(
                "disconnected",
                "Macropad disconnected; reopening the exact device",
                logging.WARNING,
            )
            self.reconnect_device()
            self._notify_watchdog()
            return

        try:
            # Wait up to 100ms for activity, then drain everything present
            readable, _, _ = select.select([self.device], [], [], 0.1)
            if readable:
                self._drain_hid()
            if (
                self._connected_since is not None
                and time.monotonic() - self._connected_since
                >= HEALTHY_CONNECTION_S
            ):
                if self.reconnect_attempts:
                    self.logger.info("HID connection stable; reconnect backoff reset")
                self.reconnect_attempts = 0
                self._connected_since = None
        except BlockingIOError:
            pass
        except OSError as e:
            if e.errno in (errno.EBUSY, errno.ENODEV, errno.EBADF, errno.EIO):
                self._set_hid_state(
                    "disconnected",
                    f"Macropad disconnected after HID error {e.errno}; reopening",
                    logging.WARNING,
                )
            else:
                self._set_hid_state(
                    "io-error",
                    f"Unexpected HID error {e.errno}; retrying: {e}",
                    logging.ERROR,
                )
            # reconnect_device() owns the attempt counter. Incrementing here too
            # would advance the backoff at double rate.
            self.reconnect_device()
        except Exception as e:
            self.logger.error(f"Unexpected error in read_hid_events: {e}")
            raise

        self._send_status_report()
        self._notify_watchdog()

    # ------------------------------------------------------------------
    # Status lights
    # ------------------------------------------------------------------
    def _poll_status_if_due(self) -> None:
        """Read each projector's display state and stage it for the Macropad."""
        now = time.monotonic()
        if now < self._next_status_poll:
            return
        self._next_status_poll = now + STATUS_POLL_INTERVAL_S

        ips = [p["ip"] for p in self.projectors[:STATUS_LIGHT_COUNT]]
        try:
            states = self.status_manager.run_on(ips, "get_display_state")
        except Exception as e:
            self.logger.warning("Status poll failed: %s", e)
            return

        codes = [
            STATUS_CODES.get(states.get(ip), STATUS_UNREACHABLE) for ip in ips
        ]
        if STATUS_UNREACHABLE in codes:
            self._next_status_poll = now + STATUS_POLL_UNREACHABLE_INTERVAL_S
        report = bytes([STATUS_REPORT_MARKER] + codes).ljust(HID_REPORT_LEN, b"\0")
        if report != self._status_report:
            summary = ", ".join(
                f"{p.get('nickname', p['ip'])}={states.get(p['ip']) or 'unreachable'}"
                for p in self.projectors[:STATUS_LIGHT_COUNT]
            )
            self.logger.info("Projector status: %s", summary)
        self._status_report = report

    def _send_status_report(self) -> None:
        """Write the staged status to the Macropad from the HID-owning thread."""
        report = self._status_report
        if report is None or self.device is None:
            return
        now = time.monotonic()
        if (
            report == self._status_sent
            and now - self._status_sent_time < STATUS_RESEND_S
        ):
            return
        self._status_sent = report
        self._status_sent_time = now
        try:
            # hidraw takes the report ID first; 0 means the device has none.
            os.write(self.device, b"\x00" + report)
        except OSError as e:
            # The read path owns disconnect handling; a missed light update
            # is repeated on the next resend.
            self.logger.debug("Status report write failed: %s", e)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def run(self) -> None:
        print("🎬 HID Macropad Control Started")
        print(f"   Projectors: {len(self.projectors)}")
        print(f"   Debug mode: {self.debug_mode}")
        print("\nButton mappings:")
        for button_num, (func_name, _) in self.button_functions.items():
            print(f"   Button {button_num}: {func_name}")
        print("\nPress buttons on your HID macropad to control projectors!")
        print("Press Ctrl+C to exit\n")

        self.running = True
        self._worker = threading.Thread(
            target=self._action_worker, name="macropad-actions", daemon=True
        )
        self._worker.start()

        try:
            while self.running:
                self.read_hid_events()
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt - stopping...")
            self.running = False
        except Exception as e:
            print(f"❌ Error: {e}")
            self.logger.exception("Runtime error: %s", e)
            raise
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        self.running = False
        with self._action_condition:
            self._action_condition.notify_all()
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(timeout=2.0)
            self._worker = None
        self._close_device()
        try:
            self.manager.close()
            self.status_manager.close()
        except Exception:
            pass


def main() -> None:
    from config import PROJECTORS

    debug_mode = True
    if len(sys.argv) > 1:
        debug_mode = sys.argv[1].lower() == "true"

    controller = HIDMacropadController(projectors=PROJECTORS, debug_mode=debug_mode)
    try:
        controller.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
