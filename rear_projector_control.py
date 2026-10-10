#!/usr/bin/env python3
"""
Rear Projector Control Script
Controls the rear projector (10.10.10.4) independently from front projectors

The PJLink protocol itself lives in ProjectorController. This subclass only adds
the rear-specific default address and the extra queries the rear CLI shows. A
second copy of the wire handling is what let the rear projector keep an
unbuffered recv() long after the front controller was fixed.
"""

import logging
import os
import time
from typing import Optional

from projector_control import ProjectorController

# Module-level logger (safe to create at import time)
logger = logging.getLogger(__name__)


class RearProjectorController(ProjectorController):
    """Controls the rear projector via PJLink protocol"""

    def __init__(
        self,
        ip: str = '10.10.10.4',
        port: int = 4352,
        timeout: Optional[float] = None,
    ):
        super().__init__(ip, port, timeout)

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
        """Get comprehensive status of rear projector.

        Entering the context manager raises when the projector cannot be
        reached, so an unreachable unit reports online False instead of True
        with every field empty.
        """
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
    os.makedirs('logs', exist_ok=True)
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
