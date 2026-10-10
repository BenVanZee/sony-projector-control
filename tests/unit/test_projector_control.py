import socket
import threading
import unittest
from unittest import mock

from projector_control import ProjectorController, ProjectorManager
from rear_projector_control import RearProjectorController


class ScriptedSocket:
    def __init__(self, recv_steps=(), connect_error=None):
        self.recv_steps = list(recv_steps)
        self.connect_error = connect_error
        self.closed = False
        self.connected_to = None
        self.sent = []
        self.timeout = None

    def settimeout(self, timeout):
        self.timeout = timeout

    def connect(self, address):
        if self.connect_error:
            raise self.connect_error
        self.connected_to = address

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, size):
        if not self.recv_steps:
            return b""
        step = self.recv_steps.pop(0)
        if isinstance(step, BaseException):
            raise step
        return step

    def close(self):
        self.closed = True


class ConcurrentProjector:
    def __init__(self, barrier):
        self.barrier = barrier

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def set_power(self, power_on):
        self.barrier.wait(timeout=1)
        return power_on

    def set_mute(self, mute):
        self.barrier.wait(timeout=1)
        return mute


class ProjectorControllerTests(unittest.TestCase):
    def test_failed_connect_closes_and_clears_socket(self):
        """A failed connect must not leave a truthy unusable socket behind."""
        failed_socket = ScriptedSocket(connect_error=OSError("offline"))
        controller = ProjectorController("10.10.10.2")

        with mock.patch(
            "projector_control.socket.socket", return_value=failed_socket
        ):
            self.assertFalse(controller.connect())

        self.assertTrue(failed_socket.closed)
        self.assertIsNone(controller.socket)

    def test_partial_greeting_and_response_are_read_to_carriage_return(self):
        """TCP segmentation must not truncate a valid PJLink response."""
        scripted = ScriptedSocket(
            recv_steps=[b"PJ", b"LINK 0\r", b"%1PO", b"WR=1\r"]
        )
        controller = ProjectorController("10.10.10.2")

        with mock.patch("projector_control.socket.socket", return_value=scripted):
            self.assertEqual("ON", controller.get_power_status())

        self.assertEqual([b"%1POWR ?\r"], scripted.sent)
        self.assertEqual(3.0, scripted.timeout)

    def test_idempotent_query_retries_once_after_connection_reset(self):
        """A reset response socket gets one fresh-connection retry."""
        first = ScriptedSocket(
            recv_steps=[b"PJLINK 0\r", ConnectionResetError("reset")]
        )
        second = ScriptedSocket(recv_steps=[b"PJLINK 0\r", b"%1POWR=1\r"])
        controller = ProjectorController("10.10.10.2")

        with mock.patch(
            "projector_control.socket.socket", side_effect=[first, second]
        ):
            self.assertEqual("ON", controller.get_power_status())

        self.assertEqual([b"%1POWR ?\r"], first.sent)
        self.assertEqual([b"%1POWR ?\r"], second.sent)
        self.assertTrue(first.closed)

    def test_context_manager_retries_one_transient_initial_connect_failure(self):
        """The preserved context-manager API gets the same bounded connect retry."""
        first = ScriptedSocket(connect_error=OSError("temporarily offline"))
        second = ScriptedSocket(recv_steps=[b"PJLINK 0\r", b"%1POWR=1\r"])
        controller = ProjectorController("10.10.10.2")

        with mock.patch(
            "projector_control.socket.socket", side_effect=[first, second]
        ):
            with controller:
                self.assertEqual("ON", controller.get_power_status())

        self.assertTrue(first.closed)
        self.assertTrue(second.closed)

    def test_state_command_is_not_resent_after_a_lost_response(self):
        """A projector that already powered off must not be commanded twice."""
        first = ScriptedSocket(
            recv_steps=[b"PJLINK 0\r", TimeoutError("timed out")]
        )
        second = ScriptedSocket(recv_steps=[b"PJLINK 0\r", b"%1POWR=OK\r"])
        controller = ProjectorController("10.10.10.2")

        with mock.patch(
            "projector_control.socket.socket", side_effect=[first, second]
        ):
            self.assertFalse(controller.set_power(False))

        self.assertEqual([b"%1POWR 0\r"], first.sent)
        self.assertEqual([], second.sent)
        self.assertTrue(first.closed)

    def test_state_command_is_not_resent_when_sendall_writes_then_raises(self):
        """sendall can put bytes on the wire and still raise. Assume delivered."""

        class WriteThenReset(ScriptedSocket):
            def sendall(self, data):
                self.sent.append(data)
                raise OSError("connection reset after write")

        first = WriteThenReset(recv_steps=[b"PJLINK 0\r"])
        second = ScriptedSocket(recv_steps=[b"PJLINK 0\r", b"%1POWR=OK\r"])
        controller = ProjectorController("10.10.10.2")

        with mock.patch(
            "projector_control.socket.socket", side_effect=[first, second]
        ):
            self.assertFalse(controller.set_power(True))

        self.assertEqual([b"%1POWR 1\r"], first.sent)
        self.assertEqual([], second.sent)

    def test_query_retry_survives_a_wasted_connect_attempt(self):
        """Connect failures and transmit failures must not share one budget."""
        refused = ScriptedSocket(connect_error=OSError("connect failed"))
        lost = ScriptedSocket(recv_steps=[b"PJLINK 0\r", TimeoutError("lost")])
        good = ScriptedSocket(recv_steps=[b"PJLINK 0\r", b"%1POWR=1\r"])
        controller = ProjectorController("10.10.10.2")

        with mock.patch(
            "projector_control.socket.socket",
            side_effect=[refused, lost, good],
        ):
            self.assertEqual("ON", controller.get_power_status())

        self.assertEqual([b"%1POWR ?\r"], lost.sent)
        self.assertEqual([b"%1POWR ?\r"], good.sent)

    def test_repeated_connect_failure_does_not_loop_forever(self):
        """The connect budget must terminate when the projector never answers."""
        sockets = [ScriptedSocket(connect_error=OSError("offline")) for _ in range(8)]
        controller = ProjectorController("10.10.10.2")

        with mock.patch("projector_control.socket.socket", side_effect=sockets):
            self.assertIsNone(controller.get_power_status())

        self.assertEqual(2, sum(1 for s in sockets if s.closed))

    def test_connect_failure_still_retries_a_state_command(self):
        """Nothing reached the projector, so a second connect is safe."""
        first = ScriptedSocket(connect_error=OSError("temporarily offline"))
        second = ScriptedSocket(recv_steps=[b"PJLINK 0\r", b"%1POWR=OK\r"])
        controller = ProjectorController("10.10.10.2")

        with mock.patch(
            "projector_control.socket.socket", side_effect=[first, second]
        ):
            self.assertTrue(controller.set_power(True))

        self.assertEqual([b"%1POWR 1\r"], second.sent)

    def test_crlf_terminated_response_is_not_poisoned_by_the_newline(self):
        """A device that answers CRLF must not break every later comparison."""
        scripted = ScriptedSocket(
            recv_steps=[b"PJLINK 0\r\n", b"%1POWR=1\r\n"]
        )
        controller = ProjectorController("10.10.10.2")

        with mock.patch("projector_control.socket.socket", return_value=scripted):
            self.assertEqual("ON", controller.get_power_status())

    def test_lamp_hours_parses_value_before_status_flag(self):
        """PJLink's lamp status flag must not be mistaken for lamp hours."""
        controller = ProjectorController("10.10.10.2")
        with mock.patch.object(
            controller, "send_command", return_value="%1LAMP=1234 1"
        ):
            self.assertEqual(1234, controller.get_lamp_hours())


class RearProjectorControllerTests(unittest.TestCase):
    def test_rear_projector_inherits_the_buffered_carriage_return_read(self):
        """The rear unit must not keep its own unbuffered recv."""
        scripted = ScriptedSocket(
            recv_steps=[b"PJLI", b"NK 0\r", b"%1PO", b"WR=1\r"]
        )
        controller = RearProjectorController()

        with mock.patch("projector_control.socket.socket", return_value=scripted):
            self.assertEqual("ON", controller.get_power_status())

        self.assertEqual(("10.10.10.4", 4352), scripted.connected_to)
        self.assertEqual(3.0, scripted.timeout)

    def test_unreachable_rear_projector_reports_offline(self):
        """get_status must not claim online when the connect never succeeded."""
        controller = RearProjectorController()

        with mock.patch(
            "projector_control.socket.socket",
            side_effect=lambda *a, **k: ScriptedSocket(
                connect_error=OSError("offline")
            ),
        ):
            status = controller.get_status()

        self.assertFalse(status["online"])
        self.assertIsNone(status["power"])


class ProjectorManagerTests(unittest.TestCase):
    def test_alias_lookup_maps_nickname_to_ip(self):
        """The public nickname lookup must not reverse keys and values."""
        manager = ProjectorManager(
            [], aliases={"left": "10.10.10.2", "right": "10.10.10.3"}
        )
        self.assertEqual("10.10.10.2", manager.get_projector_by_nickname("left"))
        self.assertEqual("left", manager.get_nickname_by_ip("10.10.10.2"))

    def test_power_all_starts_projectors_concurrently(self):
        """One unreachable projector must not serialize every network timeout."""
        manager = ProjectorManager([])
        barrier = threading.Barrier(2)
        manager.controllers = {
            "10.10.10.2": ConcurrentProjector(barrier),
            "10.10.10.3": ConcurrentProjector(barrier),
        }

        self.assertEqual(
            {"10.10.10.2": True, "10.10.10.3": True}, manager.power_all(True)
        )

    def test_selected_front_projectors_start_concurrently(self):
        """Front-only actions use the same bounded concurrent fan-out."""
        manager = ProjectorManager([])
        barrier = threading.Barrier(2)
        manager.controllers = {
            "10.10.10.2": ConcurrentProjector(barrier),
            "10.10.10.3": ConcurrentProjector(barrier),
            "10.10.10.4": mock.Mock(),
        }

        self.assertEqual(
            {"10.10.10.2": True, "10.10.10.3": True},
            manager.run_on(
                ["10.10.10.2", "10.10.10.3"], "set_mute", True
            ),
        )

    def test_managed_command_retries_one_transient_initial_connect_failure(self):
        """The manager must not bypass command-level connect retry handling."""
        first = ScriptedSocket(connect_error=OSError("temporarily offline"))
        second = ScriptedSocket(recv_steps=[b"PJLINK 0\r", b"%1POWR=1\r"])
        manager = ProjectorManager([("10.10.10.2", 4352)])

        with mock.patch(
            "projector_control.socket.socket", side_effect=[first, second]
        ):
            results = manager.run_on(["10.10.10.2"], "get_power_status")

        self.assertEqual({"10.10.10.2": "ON"}, results)
        self.assertTrue(first.closed)
        self.assertTrue(second.closed)

    def test_reachable_projector_with_unknown_power_is_not_marked_offline(self):
        """Protocol-level unknown state is distinct from network unavailability."""
        scripted = ScriptedSocket(
            recv_steps=[
                b"PJLINK 0\r",
                b"%1POWR=ERR3\r",
                b"%1AVMT=30\r",
                b"%2FREZ=0\r",
                b"%1LAMP=1234 1\r",
            ]
        )
        manager = ProjectorManager([("10.10.10.2", 4352)])

        with mock.patch("projector_control.socket.socket", return_value=scripted):
            status = manager.get_all_status()["10.10.10.2"]

        self.assertIsNone(status["power"])
        self.assertTrue(status["online"])


if __name__ == "__main__":
    unittest.main()
