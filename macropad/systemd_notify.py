"""Minimal systemd readiness/watchdog notifications without dependencies."""

import os
import socket


class SystemdNotifier:
    def __init__(self, socket_path=None):
        self.socket_path = socket_path or os.environ.get("NOTIFY_SOCKET")

    def _send(self, message):
        """Best-effort datagram to the notify socket.

        Never raises. This runs from the HID poll loop, where an escaping
        OSError would exit the process — systemd would read that as an
        unrecoverable internal failure when the only thing that failed was a
        status ping.
        """
        if not self.socket_path:
            return False
        address = self.socket_path
        if address.startswith("@"):
            address = "\0" + address[1:]
        try:
            notifier = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        except OSError:
            return False
        try:
            notifier.connect(address)
            notifier.sendall(message.encode("utf-8"))
            return True
        except OSError:
            return False
        finally:
            notifier.close()

    def ready(self, status):
        return self._send("READY=1\nSTATUS=" + status)

    def status(self, status):
        return self._send("STATUS=" + status)

    def watchdog(self):
        return self._send("WATCHDOG=1")
