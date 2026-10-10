#!/usr/bin/env python3
"""
Mock helpers for testing projector control
Provides utilities and fixtures for mocking projector responses
"""

import unittest.mock
from contextlib import contextmanager
from typing import Dict, Optional

try:
    # Try relative import first (when used as module)
    from .mock_projector_server import MockProjectorServer, MockProjectorState
except ImportError:
    # Fall back to absolute import (when run directly)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mock_projector_server import MockProjectorServer, MockProjectorState


class MockSocketResponse:
    """Helper class to mock socket responses"""
    
    def __init__(self, responses: Dict[str, str], initial_message: str = "PJLink 1\r\n"):
        """
        Initialize mock socket response handler
        Args:
            responses: Dict mapping commands to responses
            initial_message: Initial message sent on connection
        """
        self.responses = responses
        self.initial_message = initial_message
        self.received_commands = []
        self.sent_responses = []
        
    def get_response(self, command: str) -> str:
        """Get response for a command"""
        self.received_commands.append(command)
        response = self.responses.get(command.strip(), "")
        self.sent_responses.append(response)
        return response


@contextmanager
def mock_projector_server(host: str = "127.0.0.1", port: int = 0, **state_kwargs):
    """
    Context manager for a mock projector server
    
    Usage:
        with mock_projector_server(power="ON", mute="UNMUTED") as server:
            controller = ProjectorController(server.host, server.port)
            status = controller.get_power_status()
    """
    server = MockProjectorServer(host=host, port=port)
    if state_kwargs:
        server.set_state(**state_kwargs)
    
    try:
        port = server.start()
        # Give server a moment to start
        import time
        time.sleep(0.1)
        yield server
    finally:
        server.stop()


def create_mock_socket_patcher(responses: Dict[str, str], initial_message: str = "PJLink 1\r\n"):
    """
    Create a mock socket patcher that simulates projector responses
    
    Args:
        responses: Dict mapping commands (without \\r) to responses (without \\r)
        initial_message: Initial message sent on connection
    
    Returns:
        A mock patcher that can be used with unittest.mock.patch
    
    Usage:
        responses = {
            "%1POWR ?": "%1POWR=1",
            "%1AVMT ?": "%1AVMT=30"
        }
        with create_mock_socket_patcher(responses):
            controller = ProjectorController("127.0.0.1", 4352)
            status = controller.get_power_status()
    """
    class MockSocket:
        def __init__(self, *args, **kwargs):
            self.responses = responses
            self.initial_message = initial_message
            self.connected = False
            self.sent_data = []
            self.received_data = []
            
        def connect(self, address):
            self.connected = True
            self.address = address
            
        def settimeout(self, timeout):
            pass
            
        def sendall(self, data):
            if not self.connected:
                raise Exception("Not connected")
            command = data.decode('ascii', errors='ignore').strip()
            self.sent_data.append(command)
            
        def recv(self, bufsize):
            if not self.connected:
                raise Exception("Not connected")
            
            # First call returns initial message
            if not hasattr(self, '_initial_sent'):
                self._initial_sent = True
                return self.initial_message.encode('ascii')
            
            # Subsequent calls return responses based on last sent command
            if self.sent_data:
                last_command = self.sent_data[-1]
                response = self.responses.get(last_command, "")
                if response:
                    return (response + "\r").encode('ascii')
            
            return b""
            
        def close(self):
            self.connected = False
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            self.close()
    
    return unittest.mock.patch('socket.socket', return_value=MockSocket())


def get_default_responses() -> Dict[str, str]:
    """Get default mock responses for common commands"""
    return {
        "%1POWR ?": "%1POWR=1",  # Power ON
        "%1POWR 1": "%1POWR=OK",  # Power ON command
        "%1POWR 0": "%1POWR=OK",  # Power OFF command
        "%1AVMT ?": "%1AVMT=30",  # Unmuted
        "%1AVMT 30": "%1AVMT=OK",  # Unmute command
        "%1AVMT 31": "%1AVMT=OK",  # Mute command
        "%2FREZ ?": "%2FREZ=0",   # Not frozen
        "%2FREZ 1": "%2FREZ=OK",   # Freeze command
        "%2FREZ 0": "%2FREZ=OK",   # Unfreeze command
        "%1LAMP ?": "%1LAMP=1 1234 1",  # Lamp hours
        "%1INPT ?": "%1INPT=11",   # Input status
        "%1ERST ?": "%1ERST=00000000"  # No errors
    }


class ProjectorStateBuilder:
    """Builder for creating projector states for testing"""
    
    def __init__(self):
        self.state = MockProjectorState()
    
    def power_on(self):
        self.state.power = "ON"
        return self
    
    def power_off(self):
        self.state.power = "OFF"
        return self
    
    def muted(self):
        self.state.mute = "MUTED"
        return self
    
    def unmuted(self):
        self.state.mute = "UNMUTED"
        return self
    
    def frozen(self):
        self.state.freeze = "FROZEN"
        return self
    
    def normal(self):
        self.state.freeze = "NORMAL"
        return self
    
    def lamp_hours(self, hours: int):
        self.state.lamp_hours = hours
        return self
    
    def build_responses(self) -> Dict[str, str]:
        """Build response dictionary from current state"""
        return {
            "%1POWR ?": self.state.get_power_response(),
            "%1AVMT ?": self.state.get_mute_response(),
            "%2FREZ ?": self.state.get_freeze_response(),
            "%1LAMP ?": self.state.get_lamp_response(),
            "%1INPT ?": self.state.get_input_response(),
            "%1ERST ?": self.state.get_error_response(),
            "%1POWR 1": "%1POWR=OK",
            "%1POWR 0": "%1POWR=OK",
            "%1AVMT 30": "%1AVMT=OK",
            "%1AVMT 31": "%1AVMT=OK",
            "%2FREZ 1": "%2FREZ=OK",
            "%2FREZ 0": "%2FREZ=OK",
        }


# Example usage functions
def example_mock_server_test():
    """Example of using mock server"""
    from projector_control import ProjectorController
    
    with mock_projector_server(power="ON", mute="UNMUTED") as server:
        controller = ProjectorController(server.host, server.port)
        controller.connect()
        
        # Test power status
        status = controller.get_power_status()
        print(f"Power status: {status}")
        assert status == "ON"
        
        # Test mute status
        mute_status = controller.get_mute_status()
        print(f"Mute status: {mute_status}")
        assert mute_status == "UNMUTED"
        
        controller.disconnect()


def example_mock_socket_test():
    """Example of using mock socket patcher"""
    from projector_control import ProjectorController
    
    builder = ProjectorStateBuilder()
    builder.power_on().unmuted().normal()
    responses = builder.build_responses()
    
    with create_mock_socket_patcher(responses):
        controller = ProjectorController("127.0.0.1", 4352)
        controller.connect()
        
        status = controller.get_power_status()
        print(f"Power status: {status}")
        assert status == "ON"
        
        controller.disconnect()


if __name__ == "__main__":
    print("Testing mock helpers...")
    print("\n1. Testing mock server:")
    example_mock_server_test()
    print("\n2. Testing mock socket:")
    example_mock_socket_test()
    print("\n✅ All tests passed!")

