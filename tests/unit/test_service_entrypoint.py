import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from macropad import macropad_service_control


class FakeController:
    ran = False

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def run(self):
        type(self).ran = True


class FakeNotifier:
    ready_status = None

    def ready(self, status):
        type(self).ready_status = status
        return True

    def watchdog(self):
        return True


class ServiceEntrypointTests(unittest.TestCase):
    def test_service_starts_when_installation_tree_is_not_writable(self):
        """Journald logging must not require a service-owned file under /opt."""
        FakeController.ran = False
        FakeNotifier.ready_status = None
        fake_hid = types.SimpleNamespace(HIDMacropadController=FakeController)
        fake_notify = types.SimpleNamespace(SystemdNotifier=FakeNotifier)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "macropad").mkdir()
            logs = root / "logs"
            logs.mkdir(mode=0o555)
            fake_entrypoint = root / "macropad" / "macropad_service_control.py"

            try:
                with (
                    mock.patch.object(
                        macropad_service_control, "__file__", str(fake_entrypoint)
                    ),
                    mock.patch.dict(
                        sys.modules,
                        {
                            "hid_macropad_control": fake_hid,
                            "systemd_notify": fake_notify,
                        },
                    ),
                    mock.patch.object(
                        macropad_service_control.logging, "basicConfig"
                    ),
                ):
                    macropad_service_control.main()
            finally:
                logs.chmod(0o755)

            self.assertTrue(FakeController.ran)
            self.assertEqual(
                "Sony Macropad controller running", FakeNotifier.ready_status
            )
            self.assertEqual([], list(logs.iterdir()))


if __name__ == "__main__":
    unittest.main()
