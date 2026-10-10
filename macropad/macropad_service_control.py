#!/usr/bin/env python3
"""
Macropad Control for systemd / headless Raspberry Pi operation.

Production path: raw HID via hid_macropad_control (matches CircuitPython
boot.py + code.py vendor HID reports).
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROJECTORS  # noqa: E402

# Prefer package-dir import so this works whether launched as a script or from
# another working directory under systemd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )
    logger = logging.getLogger(__name__)

    print("🎬 Macropad Service Control Started")
    print(f"   Projectors: {len(PROJECTORS)}")
    print("   Mode: raw HID (/dev/hidraw*) via hid_macropad_control")
    print()

    # HIDMacropadController owns its main loop and cleanup.
    try:
        from hid_macropad_control import HIDMacropadController
        from systemd_notify import SystemdNotifier

        notifier = SystemdNotifier()
        controller = HIDMacropadController(
            projectors=PROJECTORS,
            debug_mode=False,
            heartbeat=notifier.watchdog,
        )
        notifier.ready("Sony Macropad controller running")
        controller.run()
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    except Exception as e:
        logger.exception("Service failed: %s", e)
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
