import unittest
from unittest import mock


class SystemdNotifierTests(unittest.TestCase):
    def test_ready_and_watchdog_messages_reach_notify_socket(self):
        """The service sends systemd-compatible readiness and heartbeat datagrams."""
        from macropad.systemd_notify import SystemdNotifier

        ready_socket = mock.Mock()
        watchdog_socket = mock.Mock()
        with mock.patch(
            "macropad.systemd_notify.socket.socket",
            side_effect=[ready_socket, watchdog_socket],
        ):
            notifier = SystemdNotifier("/run/systemd/notify")
            notifier.ready("Waiting for Sony Macropad")
            notifier.watchdog()

        ready_socket.connect.assert_called_once_with("/run/systemd/notify")
        ready_socket.sendall.assert_called_once_with(
            b"READY=1\nSTATUS=Waiting for Sony Macropad"
        )
        ready_socket.close.assert_called_once_with()
        watchdog_socket.connect.assert_called_once_with("/run/systemd/notify")
        watchdog_socket.sendall.assert_called_once_with(b"WATCHDOG=1")
        watchdog_socket.close.assert_called_once_with()

    def test_notify_socket_failure_never_reaches_the_service_loop(self):
        """A status ping that fails must not look like an unrecoverable fault."""
        from macropad.systemd_notify import SystemdNotifier

        broken = mock.Mock()
        broken.connect.side_effect = OSError("no such notify socket")

        with mock.patch(
            "macropad.systemd_notify.socket.socket", return_value=broken
        ):
            self.assertFalse(SystemdNotifier("/run/systemd/notify").watchdog())

        broken.close.assert_called_once_with()

    def test_unset_notify_socket_is_a_no_op(self):
        """Running outside systemd must not attempt a connection."""
        from macropad.systemd_notify import SystemdNotifier

        with mock.patch("macropad.systemd_notify.socket.socket") as created:
            self.assertFalse(SystemdNotifier("").watchdog())

        created.assert_not_called()


if __name__ == "__main__":
    unittest.main()
