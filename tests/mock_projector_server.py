#!/usr/bin/env python3
"""
Mock PJLink Projector Server
Simulates a Sony projector for testing without hardware
"""

import socket
import threading
import time
from typing import Dict, Optional


class MockProjectorState:
    """Represents the state of a mock projector"""
    
    def __init__(self):
        self.power = "OFF"  # OFF, ON, COOLING, WARMING
        self.mute = "UNMUTED"  # MUTED, UNMUTED
        self.freeze = "NORMAL"  # NORMAL, FROZEN
        self.lamp_hours = 1234
        self.input = "11"  # Input source
        self.error = "00000000"  # Error status
        
    def get_power_response(self) -> str:
        """Get PJLink power status response"""
        power_map = {
            "OFF": "%1POWR=0",
            "ON": "%1POWR=1",
            "COOLING": "%1POWR=2",
            "WARMING": "%1POWR=3"
        }
        return power_map.get(self.power, "%1POWR=0")
    
    def get_mute_response(self) -> str:
        """Get PJLink mute status response"""
        return "%1AVMT=31" if self.mute == "MUTED" else "%1AVMT=30"
    
    def get_freeze_response(self) -> str:
        """Get PJLink freeze status response"""
        return "%2FREZ=1" if self.freeze == "FROZEN" else "%2FREZ=0"
    
    def get_lamp_response(self) -> str:
        """Get PJLink lamp hours response"""
        return f"%1LAMP=1 {self.lamp_hours} 1"
    
    def get_input_response(self) -> str:
        """Get PJLink input status response"""
        return f"%1INPT={self.input}"
    
    def get_error_response(self) -> str:
        """Get PJLink error status response"""
        return f"%1ERST={self.error}"


class MockProjectorServer:
    """Mock PJLink projector server for testing"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        """
        Initialize mock server
        Args:
            host: Host to bind to (default: localhost)
            port: Port to bind to (0 = auto-assign)
        """
        self.host = host
        self.port = port
        self.socket = None
        self.server_thread = None
        self.running = False
        self.state = MockProjectorState()
        self.initial_message = "PJLink 1\r\n"
        
    def start(self) -> int:
        """Start the mock server and return the port it's listening on"""
        if self.running:
            return self.port
            
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.port = self.socket.getsockname()[1]
        self.running = True
        
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        
        return self.port
    
    def stop(self):
        """Stop the mock server"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def _run_server(self):
        """Main server loop"""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                client_socket, address = self.socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle a client connection"""
        try:
            # Send initial PJLink handshake message
            client_socket.sendall(self.initial_message.encode('ascii'))
            
            # Handle commands
            while self.running:
                try:
                    client_socket.settimeout(1.0)
                    data = client_socket.recv(1024)
                    
                    if not data:
                        break
                    
                    command = data.decode('ascii', errors='ignore').strip()
                    response = self._process_command(command)
                    
                    if response:
                        client_socket.sendall(response.encode('ascii'))
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    break
                    
        except Exception as e:
            pass
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _process_command(self, command: str) -> Optional[str]:
        """Process a PJLink command and return response"""
        command = command.strip()
        
        # Power commands
        if command == "%1POWR ?":
            return self.state.get_power_response() + "\r"
        elif command == "%1POWR 1":
            self.state.power = "ON"
            return "%1POWR=OK\r"
        elif command == "%1POWR 0":
            self.state.power = "OFF"
            return "%1POWR=OK\r"
        
        # Mute commands
        elif command == "%1AVMT ?":
            return self.state.get_mute_response() + "\r"
        elif command == "%1AVMT 30":
            self.state.mute = "UNMUTED"
            return "%1AVMT=OK\r"
        elif command == "%1AVMT 31":
            self.state.mute = "MUTED"
            return "%1AVMT=OK\r"
        
        # Freeze commands
        elif command == "%2FREZ ?":
            return self.state.get_freeze_response() + "\r"
        elif command == "%2FREZ 1":
            self.state.freeze = "FROZEN"
            return "%2FREZ=OK\r"
        elif command == "%2FREZ 0":
            self.state.freeze = "NORMAL"
            return "%2FREZ=OK\r"
        
        # Lamp hours
        elif command == "%1LAMP ?":
            return self.state.get_lamp_response() + "\r"
        
        # Input status
        elif command == "%1INPT ?":
            return self.state.get_input_response() + "\r"
        
        # Error status
        elif command == "%1ERST ?":
            return self.state.get_error_response() + "\r"
        
        # Unknown command
        else:
            return None
    
    def set_state(self, **kwargs):
        """Update projector state"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
    
    def get_state(self) -> Dict:
        """Get current projector state"""
        return {
            'power': self.state.power,
            'mute': self.state.mute,
            'freeze': self.state.freeze,
            'lamp_hours': self.state.lamp_hours,
            'input': self.state.input,
            'error': self.state.error
        }


if __name__ == "__main__":
    # Test the mock server
    print("Starting mock projector server...")
    server = MockProjectorServer()
    port = server.start()
    print(f"Mock server running on 127.0.0.1:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
        print("Server stopped")



