#!/usr/bin/env python3
"""
Specific USB Keypad Control for Sony Projector System
Targets a specific USB device to avoid keyboard interference
"""

import time
import threading
import os
import sys
from typing import Dict, Optional
import logging
from projector_control import ProjectorManager, ProjectorController

# Try to import evdev for direct USB input
try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    print("❌ evdev not available - install with: sudo apt install python3-evdev")

class SpecificUSBKeypadController:
    """USB keypad controller targeting a specific device"""
    
    def __init__(self, projectors: list, device_path: str = None, debug_mode: bool = True):
        self.projectors = projectors
        self.device_path = device_path
        self.debug_mode = debug_mode
        
        # Convert config format to expected format
        projector_tuples = [(p['ip'], p['port']) for p in projectors]
        self.manager = ProjectorManager(projector_tuples)
        self.running = False
        
        # Key mappings for common 4-button keypads
        self.key_mappings = {
            # Common key codes for Cut/Copy/Paste/Enter keypads
            45: 1,  # X key (Cut) - Turn projectors OFF
            46: 2,  # C key (Copy) - Turn projectors ON
            47: 3,  # V key (Paste) - Toggle screen blanking
            28: 4,  # Enter key - Toggle screen freezing
            
            # Alternative mappings
            30: 1,  # A key - Turn projectors OFF
            48: 2,  # B key - Turn projectors ON
            32: 3,  # D key - Toggle screen blanking
            18: 4,  # E key - Toggle screen freezing
            
            # Function keys
            59: 1,  # F1 - Turn projectors OFF
            60: 2,  # F2 - Turn projectors ON
            61: 3,  # F3 - Toggle screen blanking
            62: 4,  # F4 - Toggle screen freezing
            
            # Number keys
            2: 1,   # 1 - Turn projectors OFF
            3: 2,   # 2 - Turn projectors ON
            4: 3,   # 3 - Toggle screen blanking
            5: 4,   # 4 - Toggle screen freezing
        }
        
        # Button functions
        self.button_functions = {
            1: "Turn projectors OFF",
            2: "Turn projectors ON", 
            3: "Toggle screen blanking",
            4: "Toggle screen freezing"
        }
        
        # Button actions
        self.button_actions = {
            1: self.power_off_all,         # Button 1: Power OFF all projectors
            2: self.power_on_all,          # Button 2: Power ON all projectors
            3: self.toggle_mute,           # Button 3: Toggle screen blank
            4: self.toggle_freeze,         # Button 4: Toggle freeze
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO if debug_mode else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('usb_keypad_control_specific.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def list_input_devices(self):
        """List all available input devices"""
        if not EVDEV_AVAILABLE:
            print("❌ evdev not available")
            return []
            
        try:
            devices = []
            for path in evdev.list_devices():
                device = InputDevice(path)
                devices.append((path, device.name, device.phys))
                print(f"📱 Device: {device.name}")
                print(f"   Path: {path}")
                print(f"   Physical: {device.phys}")
                print(f"   Capabilities: {list(device.capabilities().keys())}")
                print()
            return devices
        except Exception as e:
            print(f"❌ Error listing devices: {e}")
            return []
            
    def find_usb_keypad(self):
        """Find USB keypad device, excluding keyboards"""
        if not EVDEV_AVAILABLE:
            return None
            
        try:
            # If specific device path provided, use it
            if self.device_path:
                if os.path.exists(self.device_path):
                    device = InputDevice(self.device_path)
                    print(f"✅ Using specified device: {device.name} at {self.device_path}")
                    return device
                else:
                    print(f"❌ Specified device not found: {self.device_path}")
                    return None
            
            # Look for input devices, excluding keyboards
            devices = [InputDevice(path) for path in evdev.list_devices()]
            
            for device in devices:
                # Skip keyboard devices
                if 'keyboard' in device.name.lower():
                    continue
                    
                # Check if it's a keypad-like device
                if ('keypad' in device.name.lower() or 
                    'macro' in device.name.lower() or
                    'usb' in device.name.lower()):
                    print(f"✅ Found potential keypad: {device.name} at {device.path}")
                    return device
                    
                # Check capabilities for key events (but not keyboard)
                if ecodes.EV_KEY in device.capabilities():
                    # Skip if it looks like a full keyboard
                    key_codes = device.capabilities()[ecodes.EV_KEY]
                    if len(key_codes) < 20:  # Keypads typically have fewer keys
                        print(f"✅ Found potential keypad: {device.name} at {device.path}")
                        return device
                    
            print("❌ No USB keypad found")
            return None
            
        except Exception as e:
            print(f"❌ Error finding USB keypad: {e}")
            return None
            
    def handle_key_event(self, event):
        """Handle key press events"""
        if event.type == ecodes.EV_KEY and event.value == 1:  # Key press
            key_code = event.code
            
            if self.debug_mode:
                print(f"\n🔑 Key pressed: {key_code} ({ecodes.KEY[event.code] if event.code in ecodes.KEY else 'Unknown'})")
            
            # Map key to button number
            button_num = self.key_mappings.get(key_code)
            
            if button_num:
                self.handle_button_press(button_num, key_code)
            else:
                if self.debug_mode:
                    print(f"   ⚠️  Unknown key code: {key_code}")
                    print(f"   Available key codes: {list(self.key_mappings.keys())}")
                    
    def handle_button_press(self, button_num: int, key_code: int = 0):
        """Handle button press and execute action"""
        try:
            print(f"\n🎯 BUTTON {button_num} ACTIVATED!")
            print(f"   Function: {self.button_functions[button_num]}")
            print(f"   Key code: {key_code}")
            print(f"   Time: {time.strftime('%H:%M:%S')}")
            
            # Execute the button action
            action = self.button_actions.get(button_num)
            if action:
                action()
            else:
                print(f"   ❌ No action defined for button {button_num}")
                
        except Exception as e:
            print(f"   ❌ Error executing button {button_num}: {e}")
            self.logger.error(f"Button {button_num} error: {e}")
            
    def power_on_all(self):
        """Turn on all projectors"""
        print("🔌 Turning ON all projectors...")
        try:
            results = self.manager.power_all(True)
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            if success_count == total_count:
                print("✅ All projectors turned ON successfully")
            else:
                print(f"❌ Failed to turn on {total_count - success_count} of {total_count} projectors")
        except Exception as e:
            print(f"❌ Error turning on projectors: {e}")
            self.logger.error(f"Power on error: {e}")
            
    def power_off_all(self):
        """Turn off all projectors"""
        print("🔌 Turning OFF all projectors...")
        try:
            results = self.manager.power_all(False)
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            if success_count == total_count:
                print("✅ All projectors turned OFF successfully")
            else:
                print(f"❌ Failed to turn off {total_count - success_count} of {total_count} projectors")
        except Exception as e:
            print(f"❌ Error turning off projectors: {e}")
            self.logger.error(f"Power off error: {e}")
            
    def toggle_mute(self):
        """Toggle screen blank/unblank"""
        print("🎬 Toggling screen mute...")
        try:
            # Get current status and toggle
            status = self.manager.get_all_status()
            current_mute = None
            
            # Check if all projectors have the same mute status
            mute_statuses = []
            for projector_status in status.values():
                if 'mute' in projector_status:
                    mute_statuses.append(projector_status['mute'])
            
            if mute_statuses:
                # If all projectors have the same mute status, toggle it
                if len(set(mute_statuses)) == 1:
                    current_mute = mute_statuses[0] == 'MUTED'
                else:
                    # Mixed status - force to unmute
                    current_mute = False
            
            # Toggle based on current status
            if current_mute:
                results = self.manager.mute_all(False)
                action = "unmuted"
            else:
                results = self.manager.mute_all(True)
                action = "muted"
                
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            if success_count == total_count:
                print(f"✅ All screens {action} successfully")
            else:
                print(f"❌ Failed to {action} {total_count - success_count} of {total_count} screens")
                
        except Exception as e:
            print(f"❌ Error toggling mute: {e}")
            self.logger.error(f"Mute toggle error: {e}")
            
    def toggle_freeze(self):
        """Toggle freeze (pause/resume video)"""
        print("⏸️  Toggling freeze...")
        try:
            # Get current status and toggle
            status = self.manager.get_all_status()
            current_freeze = None
            
            # Check if all projectors have the same freeze status
            freeze_statuses = []
            for projector_status in status.values():
                if 'freeze' in projector_status:
                    freeze_statuses.append(projector_status['freeze'])
            
            if freeze_statuses:
                # If all projectors have the same freeze status, toggle it
                if len(set(freeze_statuses)) == 1:
                    current_freeze = freeze_statuses[0] == 'FROZEN'
                else:
                    # Mixed status - force to unfreeze
                    current_freeze = False
            
            # Toggle based on current status
            if current_freeze:
                results = self.manager.freeze_all_screens(False)
                action = "unfrozen"
            else:
                results = self.manager.freeze_all_screens(True)
                action = "frozen"
                
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            if success_count == total_count:
                print(f"✅ All screens {action} successfully")
            else:
                print(f"❌ Failed to {action} {total_count - success_count} of {total_count} screens")
                
        except Exception as e:
            print(f"❌ Error toggling freeze: {e}")
            self.logger.error(f"Freeze toggle error: {e}")
            
    def run(self):
        """Start the specific USB keypad listener"""
        if not EVDEV_AVAILABLE:
            print("❌ Cannot start - evdev not available")
            print("   Install with: sudo apt install python3-evdev")
            return
            
        print(f"🎬 Specific USB Keypad Control Started")
        print(f"   Projectors: {len(self.projectors)}")
        print(f"   Debug mode: {self.debug_mode}")
        print("\nButton mappings:")
        for key_code, button in self.key_mappings.items():
            key_name = ecodes.KEY[key_code] if key_code in ecodes.KEY else f"Key_{key_code}"
            print(f"   {key_name} ({key_code}) → Button {button}: {self.button_functions[button]}")
        print("\nPress buttons on your USB keypad to control projectors!")
        print("Press Ctrl+C to exit\n")
        
        # List all devices first
        print("📱 Available input devices:")
        self.list_input_devices()
        
        # Find USB keypad
        device = self.find_usb_keypad()
        if not device:
            print("❌ No USB keypad found. Please connect your keypad and try again.")
            print("   You can also specify a device path: python3 usb_keypad_control_specific.py /dev/input/eventX")
            return
            
        self.running = True
        
        try:
            # Read events from the device
            for event in device.read_loop():
                if not self.running:
                    break
                    
                self.handle_key_event(event)
                
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt - stopping...")
            self.running = False
        except Exception as e:
            print(f"❌ Error reading from device: {e}")
            self.logger.error(f"Device read error: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.manager.close()

def main():
    """Main function for testing"""
    import sys
    from config import PROJECTORS
    
    # Parse command line arguments
    device_path = None
    debug_mode = True
    
    if len(sys.argv) > 1:
        device_path = sys.argv[1]
    if len(sys.argv) > 2:
        debug_mode = sys.argv[2].lower() == "true"
    
    # Create and run controller
    controller = SpecificUSBKeypadController(
        projectors=PROJECTORS,
        device_path=device_path,
        debug_mode=debug_mode
    )
    
    try:
        controller.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
