#!/usr/bin/env python3
"""
Rear Projector Control Script
Controls the rear projector (10.10.10.4) independently from front projectors
"""

import socket
import time
import threading
import os
from typing import Optional
import logging

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Module-level logger (safe to create at import time)
logger = logging.getLogger(__name__)

class RearProjectorController:
    """Controls the rear projector via PJLink protocol"""
    
    def __init__(self, ip: str = '10.10.10.4', port: int = 4352, timeout: int = 10):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.lock = threading.Lock()
        
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        
    def connect(self) -> bool:
        """Establish connection to rear projector"""
        try:
            with self.lock:
                if self.socket:
                    self.socket.close()
                
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                self.socket.connect((self.ip, self.port))
                
                # Read initial connection message
                initial_msg = self.socket.recv(1024).decode('ascii', errors='ignore')
                logger.info(f"Connected to rear projector {self.ip}: {initial_msg.strip()}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to rear projector {self.ip}: {e}")
            return False
            
    def disconnect(self):
        """Close connection to rear projector"""
        with self.lock:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
                
    def send_command(self, command: str) -> Optional[str]:
        """Send PJLink command and return response"""
        if not self.socket:
            if not self.connect():
                return None
                
        try:
            with self.lock:
                # Send command
                self.socket.sendall(command.encode('ascii'))
                logger.debug(f"Sent to rear projector {self.ip}: {command.strip()}")
                
                # Receive response
                response = self.socket.recv(1024).decode('ascii', errors='ignore')
                logger.debug(f"Received from rear projector {self.ip}: {response.strip()}")
                return response.strip()
                
        except Exception as e:
            logger.error(f"Command failed on rear projector {self.ip}: {e}")
            # Try to reconnect
            self.connect()
            return None
            
    def get_power_status(self) -> Optional[str]:
        """Get rear projector power status"""
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
        """Turn rear projector on/off"""
        command = "%1POWR 1\r" if power_on else "%1POWR 0\r"
        response = self.send_command(command)
        return response == "%1POWR=OK"
        
    def get_mute_status(self) -> Optional[str]:
        """Get rear projector audio/video mute status"""
        response = self.send_command("%1AVMT ?\r")
        if response:
            if response == "%1AVMT=30":
                return "UNMUTED"
            elif response == "%1AVMT=31":
                return "MUTED"
        return None
        
    def set_mute(self, mute: bool) -> bool:
        """Mute/unmute rear projector audio and video"""
        command = "%1AVMT 31\r" if mute else "%1AVMT 30\r"
        response = self.send_command(command)
        return response == "%1AVMT=OK"
        
    def free_screen(self) -> bool:
        """Free the rear projector screen (unmute/clear any blanking)"""
        command = "%1AVMT 30\r"  # Unmute video and audio
        response = self.send_command(command)
        return response == "%1AVMT=OK"
        
    def freeze_screen(self, freeze: bool) -> bool:
        """Freeze/unfreeze the rear projector video image using correct PJLink FREZ command"""
        if freeze:
            logger.info(f"Attempting to freeze rear projector screen using FREZ command")
            command = "%2FREZ 1\r"
            response = self.send_command(command)
            if response == "%2FREZ=OK":
                logger.info(f"Freeze command successful for rear projector")
                return True
            else:
                logger.warning(f"Freeze command failed for rear projector: {response}")
                return False
        else:
            logger.info(f"Attempting to unfreeze rear projector screen")
            command = "%2FREZ 0\r"
            response = self.send_command(command)
            if response == "%2FREZ=OK":
                logger.info(f"Unfreeze command successful for rear projector")
                return True
            else:
                logger.warning(f"Unfreeze command failed for rear projector: {response}")
                return False
        
    def get_freeze_status(self) -> Optional[str]:
        """Get rear projector freeze status using correct PJLink FREZ command"""
        response = self.send_command("%2FREZ ?\r")
        logger.info(f"Freeze status response from rear projector: {response}")
        
        if response:
            if response == "%2FREZ=0":
                return "NORMAL"
            elif response == "%2FREZ=1":
                return "FROZEN"
        return None
        
    def get_lamp_hours(self) -> Optional[str]:
        """Get rear projector lamp hours"""
        response = self.send_command("%1LAMP ?\r")
        if response and response.startswith("%1LAMP="):
            return response.replace("%1LAMP=", "")
        return None
        
    def get_input_status(self) -> Optional[str]:
        """Get rear projector input status"""
        response = self.send_command("%1INPT ?\r")
        if response and response.startswith("%1INPT="):
            return response.replace("%1INPT=", "")
        return None
        
    def get_error_status(self) -> Optional[str]:
        """Get rear projector error status"""
        response = self.send_command("%1ERST ?\r")
        if response and response.startswith("%1ERST="):
            return response.replace("%1ERST=", "")
        return None
        
    def get_status(self) -> dict:
        """Get comprehensive status of rear projector"""
        try:
            with self:
                return {
                    'power': self.get_power_status(),
                    'mute': self.get_mute_status(),
                    'freeze': self.get_freeze_status(),
                    'lamp_hours': self.get_lamp_hours(),
                    'input': self.get_input_status(),
                    'error': self.get_error_status(),
                    'online': True
                }
        except Exception as e:
            logger.error(f"Failed to get rear projector status: {e}")
            return {
                'power': None,
                'mute': None,
                'freeze': None,
                'lamp_hours': None,
                'input': None,
                'error': None,
                'online': False
            }

def main():
    """Main application loop for rear projector control"""
    # Configure logging only when run as script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/rear_projector_control.log'),
            logging.StreamHandler()
        ]
    )
    
    controller = RearProjectorController()
    
    try:
        while True:
            print("\n" + "="*60)
            print("Rear Projector Control System (10.10.10.4)")
            print("="*60)
            
            # Display status
            try:
                status = controller.get_status()
                print(f"\nRear Projector Status:")
                print(f"  Power: {status['power'] or 'UNKNOWN'}")
                print(f"  Mute: {status['mute'] or 'UNKNOWN'}")
                print(f"  Freeze: {status['freeze'] or 'UNKNOWN'}")
                print(f"  Lamp Hours: {status['lamp_hours'] or 'UNKNOWN'}")
                print(f"  Input: {status['input'] or 'UNKNOWN'}")
                print(f"  Error: {status['error'] or 'NONE'}")
                print(f"  Online: {'Yes' if status['online'] else 'No'}")
            except Exception as e:
                print(f"Error getting status: {e}")
            
            print("\nCommands:")
            print("1. Turn rear projector ON")
            print("2. Turn rear projector OFF")
            print("3. Mute rear projector (blank screen)")
            print("4. Unmute rear projector")
            print("5. Free rear projector screen (clear blanking)")
            print("6. Freeze rear projector screen (pause video)")
            print("7. Unfreeze rear projector screen (resume video)")
            print("8. Refresh status")
            print("9. Exit")
            
            choice = input("\nEnter choice (1-9): ").strip()
            
            if choice == "1":
                success = controller.set_power(True)
                print(f"Power ON: {'SUCCESS' if success else 'FAILED'}")
                
            elif choice == "2":
                success = controller.set_power(False)
                print(f"Power OFF: {'SUCCESS' if success else 'FAILED'}")
                
            elif choice == "3":
                success = controller.set_mute(True)
                print(f"Mute: {'SUCCESS' if success else 'FAILED'}")
                
            elif choice == "4":
                success = controller.set_mute(False)
                print(f"Unmute: {'SUCCESS' if success else 'FAILED'}")
                
            elif choice == "5":
                success = controller.free_screen()
                print(f"Free screen: {'SUCCESS' if success else 'FAILED'}")
                
            elif choice == "6":
                success = controller.freeze_screen(True)
                print(f"Freeze screen: {'SUCCESS' if success else 'FAILED'}")
                
            elif choice == "7":
                success = controller.freeze_screen(False)
                print(f"Unfreeze screen: {'SUCCESS' if success else 'FAILED'}")
                
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
        controller.disconnect()

if __name__ == "__main__":
    main()
