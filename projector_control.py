#!/usr/bin/env python3
"""
Sony VPL-PHZ61 Projector Control Application
Controls multiple projectors via PJLink protocol
"""

import socket
import time
import threading
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import logging

# Module-level logger (safe to create at import time)
logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 3.0


def configured_timeout(default: float = DEFAULT_TIMEOUT) -> float:
    """Read NETWORK_TIMEOUT from config, falling back to the built-in default."""
    try:
        from config import NETWORK_TIMEOUT

        return float(NETWORK_TIMEOUT)
    except (ImportError, TypeError, ValueError):
        return default


class ProjectorController:
    """Controls Sony VPL-PHZ61 projectors via PJLink protocol"""

    def __init__(self, ip: str, port: int = 4352, timeout: Optional[float] = None):
        if timeout is None:
            timeout = configured_timeout()
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.lock = threading.Lock()
        self._recv_buffer = bytearray()
        
    def __enter__(self):
        for _ in range(2):
            if self.connect():
                return self
        raise ConnectionError(f"Unable to connect to projector {self.ip}")
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        
    def connect(self) -> bool:
        """Establish connection to projector"""
        with self.lock:
            self._disconnect_unlocked()
            candidate = None
            try:
                candidate = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                candidate.settimeout(self.timeout)
                candidate.connect((self.ip, self.port))
                self.socket = candidate
                self._recv_buffer.clear()
                greeting = self._read_line_unlocked()
                if greeting == "PJLINK 1" or greeting.startswith("PJLINK 1 "):
                    raise ConnectionError("PJLink authentication is required")
                if greeting != "PJLINK 0":
                    raise ConnectionError(f"Invalid PJLink greeting: {greeting!r}")
                logger.info(f"Connected to {self.ip}: {greeting}")
                return True
            except Exception as e:
                if candidate is not None:
                    try:
                        candidate.close()
                    except OSError:
                        pass
                self.socket = None
                self._recv_buffer.clear()
                logger.error(f"Failed to connect to {self.ip}: {e}")
                return False

    def _read_line_unlocked(self) -> str:
        """Read one complete PJLink CR-terminated line with the lock held."""
        if self.socket is None:
            raise ConnectionError("Projector socket is not connected")

        while b"\r" not in self._recv_buffer:
            chunk = self.socket.recv(1024)
            if not chunk:
                raise ConnectionError("Projector closed the connection")
            self._recv_buffer.extend(chunk)
            if len(self._recv_buffer) > 4096:
                raise ConnectionError("PJLink response exceeded 4096 bytes")

        line, _, remainder = self._recv_buffer.partition(b"\r")
        self._recv_buffer = bytearray(remainder)
        # Strip so a CRLF-terminated device does not leave a leading newline on
        # the next line and break every equality comparison after the greeting.
        return line.decode("ascii", errors="strict").strip()

    def _disconnect_unlocked(self):
        if self.socket:
            try:
                self.socket.close()
            except OSError:
                pass
        self.socket = None
        self._recv_buffer.clear()
            
    def disconnect(self):
        """Close connection to projector"""
        with self.lock:
            self._disconnect_unlocked()
                
    def send_command(self, command: str) -> Optional[str]:
        """Send PJLink command and return response.

        A failed connect is always safe to retry: nothing reached the
        projector. A failure *after* the bytes went out is only safe to retry
        for a query. Re-sending a state change whose response was lost gets
        ERR3 back from a projector that already applied it, which reports a
        success as a failure and invites the operator to press again.
        """
        is_query = command.rstrip("\r").endswith("?")
        max_transmits = 2 if is_query else 1
        connect_failures = 0
        transmits = 0

        # Two independent budgets. Sharing one counter meant a query that spent
        # its first attempt on a failed connect never got its retry.
        while connect_failures < 2 and transmits < max_transmits:
            if not self.socket and not self.connect():
                connect_failures += 1
                continue

            # Counted before the write, not after: sendall can put bytes on the
            # wire and then raise. Treating those as delivered costs a retry;
            # treating them as undelivered re-sends a state change.
            transmits += 1
            try:
                with self.lock:
                    if self.socket is None:
                        raise ConnectionError("Projector socket is not connected")
                    self.socket.sendall(command.encode("ascii"))
                    logger.debug(f"Sent to {self.ip}: {command.strip()}")
                    response = self._read_line_unlocked()
                    logger.debug(f"Received from {self.ip}: {response}")
                    return response
            except Exception as e:
                logger.warning(
                    "Transmit %s failed on %s: %s", transmits, self.ip, e
                )
                self.disconnect()
                if not is_query:
                    logger.warning(
                        "Not resending state command %s to %s; it may have applied",
                        command.strip(),
                        self.ip,
                    )

        return None
            
    def get_power_status(self) -> Optional[str]:
        """Get projector power status"""
        response = self.send_command("%1POWR ?\r")
        if response:
            if response == "%1POWR=0":
                return "OFF"
            elif response == "%1POWR=1":
                return "ON"
            elif response == "%1POWR=2":
                return "COOLING"
            elif response == "%1POWR=3":
                return "WARMING"
        return None
        
    def set_power(self, power_on: bool) -> bool:
        """Turn projector on/off"""
        command = "%1POWR 1\r" if power_on else "%1POWR 0\r"
        response = self.send_command(command)
        return response == "%1POWR=OK"
        
    def get_mute_status(self) -> Optional[str]:
        """Get audio/video mute status"""
        response = self.send_command("%1AVMT ?\r")
        if response:
            if response == "%1AVMT=30":
                return "UNMUTED"
            elif response == "%1AVMT=31":
                return "MUTED"
        return None
        
    def set_mute(self, mute: bool) -> bool:
        """Mute/unmute audio and video"""
        command = "%1AVMT 31\r" if mute else "%1AVMT 30\r"
        response = self.send_command(command)
        return response == "%1AVMT=OK"
        
    def free_screen(self) -> bool:
        """Free the screen (unmute/clear any blanking)"""
        command = "%1AVMT 30\r"  # Unmute video and audio
        response = self.send_command(command)
        return response == "%1AVMT=OK"
        
    def freeze_screen(self, freeze: bool) -> bool:
        """Freeze/unfreeze the video image using correct PJLink FREZ command"""
        if freeze:
            # Use the correct PJLink freeze command: %2FREZ 1
            logger.info(f"Attempting to freeze screen for {self.ip} using FREZ command")
            command = "%2FREZ 1\r"
            response = self.send_command(command)
            if response == "%2FREZ=OK":
                logger.info(f"Freeze command successful for {self.ip}")
                return True
            else:
                logger.warning(f"Freeze command failed for {self.ip}: {response}")
                return False
        else:
            # Unfreeze using %2FREZ 0
            logger.info(f"Attempting to unfreeze screen for {self.ip}")
            command = "%2FREZ 0\r"
            response = self.send_command(command)
            if response == "%2FREZ=OK":
                logger.info(f"Unfreeze command successful for {self.ip}")
                return True
            else:
                logger.warning(f"Unfreeze command failed for {self.ip}: {response}")
                return False
        
    def get_freeze_status(self) -> Optional[str]:
        """Get freeze status using correct PJLink FREZ command"""
        response = self.send_command("%2FREZ ?\r")
        logger.info(f"Freeze status response from {self.ip}: {response}")
        
        if response:
            # Import config for status mapping
            try:
                from config import FREEZE_STATUS
                logger.info(f"Available freeze status patterns: {FREEZE_STATUS}")
                # Reverse lookup to find the status
                for response_pattern, status_name in FREEZE_STATUS.items():
                    if response == response_pattern:
                        logger.info(f"Matched freeze status: {response_pattern} -> {status_name}")
                        return status_name
                logger.warning(f"No matching freeze status pattern found for response: {response}")
            except ImportError:
                logger.warning("Config not available, using fallback parsing")
                # Fallback parsing if config not available
                if response == "%2FREZ=0":
                    return "NORMAL"
                elif response == "%2FREZ=1":
                    return "FROZEN"
        else:
            logger.warning(f"No freeze status response from {self.ip}")
        return None
        
    def test_freeze_commands(self) -> Dict[str, bool]:
        """Test which freeze commands work on this projector"""
        commands = {
            "AVMT 32": "%1AVMT 32\r",
            "AVMT 33": "%1AVMT 33\r", 
            "AVMT 34": "%1AVMT 34\r",
            "AVMT 35": "%1AVMT 35\r"
        }
        
        results = {}
        for name, command in commands.items():
            response = self.send_command(command)
            success = response == "%1AVMT=OK"
            results[name] = success
            logger.info(f"Freeze command {name}: {'✅' if success else '❌'}")
            
        return results
        
    def get_lamp_hours(self) -> Optional[int]:
        """Get lamp hours (if supported)"""
        response = self.send_command("%1LAMP ?\r")
        if response and response.startswith("%1LAMP="):
            try:
                # Parse lamp hours from response
                payload = response.split("=", 1)[1]
                return int(payload.split()[0])
            except (ValueError, IndexError):
                pass
        return None

class ProjectorManager:
    """Manages multiple projectors"""

    def __init__(
        self,
        projectors: List[Tuple[str, int]],
        aliases: dict = None,
        timeout: Optional[float] = None,
    ):
        self.controllers = {
            ip: ProjectorController(ip, port, timeout)
            for ip, port in projectors
        }
        self.aliases = aliases or {}
        self.nickname_to_ip = {
            nickname.lower(): ip for nickname, ip in self.aliases.items()
        }

    def get_projector_by_nickname(self, nickname: str) -> Optional[str]:
        """Get projector IP by nickname"""
        return self.nickname_to_ip.get(nickname.lower())

    def get_nickname_by_ip(self, ip: str) -> Optional[str]:
        """Get nickname by projector IP"""
        for nickname, projector_ip in self.nickname_to_ip.items():
            if projector_ip == ip:
                return nickname
        return None

    def _run_parallel(self, method_name: str, *args) -> Dict[str, object]:
        """Run one controller method per projector with bounded concurrency."""
        return self.run_on(list(self.controllers), method_name, *args)

    def run_on(
        self, ips: List[str], method_name: str, *args
    ) -> Dict[str, object]:
        """Run a controller method concurrently on the selected projector IPs."""
        selected = {
            ip: self.controllers[ip] for ip in dict.fromkeys(ips) if ip in self.controllers
        }
        if not selected:
            return {}

        def invoke(controller):
            try:
                return getattr(controller, method_name)(*args)
            finally:
                disconnect = getattr(controller, "disconnect", None)
                if disconnect is not None:
                    disconnect()

        unordered = {}
        with ThreadPoolExecutor(max_workers=len(selected)) as executor:
            future_to_ip = {
                executor.submit(invoke, controller): ip
                for ip, controller in selected.items()
            }
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    unordered[ip] = future.result()
                except Exception as e:
                    logger.error("Failed to run %s on %s: %s", method_name, ip, e)
                    unordered[ip] = None
        return {ip: unordered.get(ip) for ip in selected}

    def get_all_status(self) -> Dict[str, Dict]:
        """Get status of all projectors"""
        if not self.controllers:
            return {}

        def read_status(controller):
            try:
                power = controller.get_power_status()
                reachable = controller.socket is not None
                return {
                    "power": power,
                    "mute": controller.get_mute_status(),
                    "freeze": controller.get_freeze_status(),
                    "lamp_hours": controller.get_lamp_hours(),
                    "online": reachable,
                }
            finally:
                controller.disconnect()

        unordered = {}
        with ThreadPoolExecutor(max_workers=len(self.controllers)) as executor:
            future_to_ip = {
                executor.submit(read_status, controller): ip
                for ip, controller in self.controllers.items()
            }
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    unordered[ip] = future.result()
                except Exception as e:
                    logger.error(f"Failed to get status from {ip}: {e}")
                    unordered[ip] = {
                        "power": None,
                        "mute": None,
                        "freeze": None,
                        "lamp_hours": None,
                        "online": False,
                    }
        return {ip: unordered[ip] for ip in self.controllers}

    def power_all(self, power_on: bool) -> Dict[str, bool]:
        """Turn all projectors on/off"""
        raw_results = self._run_parallel("set_power", power_on)
        results = {ip: bool(result) for ip, result in raw_results.items()}
        for ip, success in results.items():
            logger.info(
                f"{ip}: Power {'ON' if power_on else 'OFF'} "
                f"{'successful' if success else 'failed'}"
            )
        return results

    def mute_all(self, mute: bool) -> Dict[str, bool]:
        """Mute/unmute all projectors"""
        raw_results = self._run_parallel("set_mute", mute)
        results = {ip: bool(result) for ip, result in raw_results.items()}
        for ip, success in results.items():
            logger.info(
                f"{ip}: {'Mute' if mute else 'Unmute'} "
                f"{'successful' if success else 'failed'}"
            )
        return results

    def free_all_screens(self) -> Dict[str, bool]:
        """Free all screens (unmute/clear blanking)"""
        raw_results = self._run_parallel("free_screen")
        results = {ip: bool(result) for ip, result in raw_results.items()}
        for ip, success in results.items():
            logger.info(
                f"{ip}: Free screen {'successful' if success else 'failed'}"
            )
        return results

    def freeze_all_screens(self, freeze: bool) -> Dict[str, bool]:
        """Freeze/unfreeze all screens"""
        raw_results = self._run_parallel("freeze_screen", freeze)
        results = {ip: bool(result) for ip, result in raw_results.items()}
        action = "Freeze" if freeze else "Unfreeze"
        for ip, success in results.items():
            logger.info(
                f"{ip}: {action} screen {'successful' if success else 'failed'}"
            )
        return results

    def close(self):
        """Close all connections"""
        for controller in self.controllers.values():
            controller.disconnect()

def main():
    """Main application loop"""
    # Configure logging only when run as script
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/projector_control.log'),
            logging.StreamHandler()
        ]
    )
    
    # Import config
    try:
        from config import PROJECTORS, PROJECTOR_ALIASES
        # Convert config format to tuple format
        projectors = [(p['ip'], p['port']) for p in PROJECTORS]
        aliases = PROJECTOR_ALIASES
    except ImportError:
        # Fallback configuration
        projectors = [
            ("10.10.10.2", 4352),
            ("10.10.10.3", 4352),
        ]
        aliases = {
            'left': '10.10.10.2',
            'right': '10.10.10.3',
            'l': '10.10.10.2',
            'r': '10.10.10.3'
        }
    
    manager = ProjectorManager(projectors, aliases)
    
    try:
        while True:
            print("\n" + "="*60)
            print("Sony Projector Control System")
            print("="*60)
            
            # Display status
            status = manager.get_all_status()
            for ip, info in status.items():
                nickname = manager.get_nickname_by_ip(ip)
                display_name = f"{nickname} ({ip})" if nickname else ip
                print(f"\n{display_name}:")
                print(f"  Power: {info['power'] or 'UNKNOWN'}")
                print(f"  Mute: {info['mute'] or 'UNKNOWN'}")
                print(f"  Lamp Hours: {info['lamp_hours'] or 'UNKNOWN'}")
                print(f"  Online: {'Yes' if info['online'] else 'No'}")
            
            print("\nCommands:")
            print("1. Turn all projectors ON")
            print("2. Turn all projectors OFF")
            print("3. Mute all projectors (blank screen)")
            print("4. Unmute all projectors")
            print("5. Free all screens (clear blanking)")
            print("6. Freeze all screens (pause video)")
            print("7. Unfreeze all screens (resume video)")
            print("8. Refresh status")
            print("9. Exit")
            
            choice = input("\nEnter choice (1-9): ").strip()
            
            if choice == "1":
                results = manager.power_all(True)
                print("Power ON results:", results)
                
            elif choice == "2":
                results = manager.power_all(False)
                print("Power OFF results:", results)
                
            elif choice == "3":
                results = manager.mute_all(True)
                print("Mute results:", results)
                
            elif choice == "4":
                results = manager.mute_all(False)
                print("Unmute results:", results)
                
            elif choice == "5":
                results = manager.free_all_screens()
                print("Free screen results:", results)
                
            elif choice == "6":
                results = manager.freeze_all_screens(True)
                print("Freeze screen results:", results)
                
            elif choice == "7":
                results = manager.freeze_all_screens(False)
                print("Unfreeze screen results:", results)
                
            elif choice == "8":
                continue  # Refresh status
                
            elif choice == "9":
                print("Exiting...")
                break
                
            else:
                print("Invalid choice. Please try again.")
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        manager.close()

if __name__ == "__main__":
    main()
