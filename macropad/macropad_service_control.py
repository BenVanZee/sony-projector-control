#!/usr/bin/env python3
"""
Macropad Control for Service/Headless Operation
Works on Raspberry Pi without display/X server
Supports both evdev (Linux) and raw HID approaches
"""

import time
import sys
import os
import logging
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from projector_control import ProjectorManager

# Try evdev first (works best on Linux headless)
try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    ecodes = None  # Placeholder

# Try raw HID as fallback
try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False

class MacropadServiceController:
    """Macropad controller for headless/service operation"""
    
    def __init__(self, projectors: list, debug_mode: bool = True):
        self.projectors = projectors
        self.debug_mode = debug_mode
        
        # Convert config format
        projector_tuples = [(p['ip'], p['port']) for p in projectors]
        self.manager = ProjectorManager(projector_tuples)
        self.running = False
        self.device = None
        self.device_path = None
        
        # Button functions
        self.button_functions = {
            1: ("All On", self.power_on_all),
            2: ("All Off", self.power_off_all),
            3: ("Blank Front", self.blank_front),
            4: ("Unblank Front", self.unblank_front),
            5: ("Freeze Front", self.freeze_front),
            6: ("Unfreeze Front", self.unfreeze_front),
        }
        
        # Map function keys (F1-F12) to button numbers
        if EVDEV_AVAILABLE and ecodes:
            self.fkey_to_button = {
                ecodes.KEY_F1: 1, ecodes.KEY_F2: 2, ecodes.KEY_F3: 3, ecodes.KEY_F4: 4,
                ecodes.KEY_F5: 5, ecodes.KEY_F6: 6, ecodes.KEY_F7: 7, ecodes.KEY_F8: 8,
                ecodes.KEY_F9: 9, ecodes.KEY_F10: 10, ecodes.KEY_F11: 11, ecodes.KEY_F12: 12,
            }
        else:
            self.fkey_to_button = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO if debug_mode else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('macropad_service_control.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_front_projectors(self):
        """Get list of front projector IPs"""
        try:
            from config import PROJECTOR_GROUPS, PROJECTOR_ALIASES
            front_nicknames = PROJECTOR_GROUPS.get('front', [])
            front_ips = [PROJECTOR_ALIASES.get(nick, nick) for nick in front_nicknames]
            return front_ips
        except ImportError:
            return ['10.10.10.2', '10.10.10.3']
    
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
    
    def blank_front(self):
        """Blank (mute) front projectors"""
        print("🎬 Blanking front projectors...")
        try:
            front_ips = self.get_front_projectors()
            results = {}
            for ip in front_ips:
                if ip in self.manager.controllers:
                    try:
                        controller = self.manager.controllers[ip]
                        with controller:
                            success = controller.set_mute(True)
                            results[ip] = success
                    except Exception as e:
                        self.logger.error(f"Error blanking {ip}: {e}")
                        results[ip] = False
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            if success_count == total_count:
                print("✅ Front projectors blanked successfully")
            else:
                print(f"❌ Failed to blank {total_count - success_count} of {total_count} front projectors")
        except Exception as e:
            print(f"❌ Error blanking front projectors: {e}")
            self.logger.error(f"Blank front error: {e}")
    
    def unblank_front(self):
        """Unblank (unmute) front projectors"""
        print("🎬 Unblanking front projectors...")
        try:
            front_ips = self.get_front_projectors()
            results = {}
            for ip in front_ips:
                if ip in self.manager.controllers:
                    try:
                        controller = self.manager.controllers[ip]
                        with controller:
                            success = controller.set_mute(False)
                            results[ip] = success
                    except Exception as e:
                        self.logger.error(f"Error unblanking {ip}: {e}")
                        results[ip] = False
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            if success_count == total_count:
                print("✅ Front projectors unblanked successfully")
            else:
                print(f"❌ Failed to unblank {total_count - success_count} of {total_count} front projectors")
        except Exception as e:
            print(f"❌ Error unblanking front projectors: {e}")
            self.logger.error(f"Unblank front error: {e}")
    
    def freeze_front(self):
        """Freeze front projectors"""
        print("⏸️  Freezing front projectors...")
        try:
            front_ips = self.get_front_projectors()
            results = {}
            for ip in front_ips:
                if ip in self.manager.controllers:
                    try:
                        controller = self.manager.controllers[ip]
                        with controller:
                            success = controller.freeze_screen(True)
                            results[ip] = success
                    except Exception as e:
                        self.logger.error(f"Error freezing {ip}: {e}")
                        results[ip] = False
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            if success_count == total_count:
                print("✅ Front projectors frozen successfully")
            else:
                print(f"❌ Failed to freeze {total_count - success_count} of {total_count} front projectors")
        except Exception as e:
            print(f"❌ Error freezing front projectors: {e}")
            self.logger.error(f"Freeze front error: {e}")
    
    def unfreeze_front(self):
        """Unfreeze front projectors"""
        print("▶️  Unfreezing front projectors...")
        try:
            front_ips = self.get_front_projectors()
            results = {}
            for ip in front_ips:
                if ip in self.manager.controllers:
                    try:
                        controller = self.manager.controllers[ip]
                        with controller:
                            success = controller.freeze_screen(False)
                            results[ip] = success
                    except Exception as e:
                        self.logger.error(f"Error unfreezing {ip}: {e}")
                        results[ip] = False
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            if success_count == total_count:
                print("✅ Front projectors unfrozen successfully")
            else:
                print(f"❌ Failed to unfreeze {total_count - success_count} of {total_count} front projectors")
        except Exception as e:
            print(f"❌ Error unfreezing front projectors: {e}")
            self.logger.error(f"Unfreeze front error: {e}")
    
    def find_macropad_evdev(self):
        """Find macropad using evdev (Linux)"""
        if not EVDEV_AVAILABLE:
            return None
        
        try:
            devices = [InputDevice(path) for path in evdev.list_devices()]
            
            for device in devices:
                # Look for Adafruit Macropad
                if 'macropad' in device.name.lower() or 'adafruit' in device.name.lower():
                    print(f"✅ Found macropad via evdev: {device.name} at {device.path}")
                    return device.path
                
                # Check if it's a keyboard-like device with few keys (might be macropad)
                if ecodes.EV_KEY in device.capabilities():
                    key_codes = device.capabilities()[ecodes.EV_KEY]
                    # Macropad typically has 12 keys + modifiers
                    if 10 <= len(key_codes) <= 20:
                        # Check if it supports function keys
                        if any(fkey in key_codes for fkey in [ecodes.KEY_F1, ecodes.KEY_F2, ecodes.KEY_F3]):
                            print(f"✅ Found potential macropad: {device.name} at {device.path}")
                            return device.path
            
            return None
        except Exception as e:
            self.logger.error(f"Error finding macropad via evdev: {e}")
            return None
    
    def handle_button_press(self, button_num: int):
        """Handle button press event"""
        if button_num in self.button_functions:
            func_name, func = self.button_functions[button_num]
            print(f"\n🎯 BUTTON {button_num} PRESSED: {func_name}")
            print(f"   Time: {time.strftime('%H:%M:%S')}")
            try:
                func()
            except Exception as e:
                print(f"   ❌ Error executing {func_name}: {e}")
                self.logger.error(f"Button {button_num} error: {e}")
        else:
            if self.debug_mode:
                print(f"⚠️  Unknown button: {button_num}")
    
    def run_evdev(self):
        """Run using evdev (Linux headless)"""
        device_path = self.find_macropad_evdev()
        if not device_path:
            print("❌ Macropad not found via evdev")
            return False
        
        try:
            device = InputDevice(device_path)
            print(f"🎹 Listening for macropad input via evdev...")
            print(f"   Device: {device.name}")
            print(f"   Path: {device_path}")
            
            # Grab device to prevent other programs from reading it
            device.grab()
            
            self.running = True
            for event in device.read_loop():
                if not self.running:
                    break
                
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    if key_event.keystate == key_event.key_down:
                        # Check if it's a function key
                        button_num = self.fkey_to_button.get(key_event.keycode)
                        if button_num:
                            self.handle_button_press(button_num)
            
        except Exception as e:
            print(f"❌ Error reading from evdev: {e}")
            self.logger.error(f"Evdev error: {e}")
            return False
        finally:
            try:
                device.ungrab()
            except:
                pass
        
        return True
    
    def run_hid(self):
        """Run using raw HID (fallback)"""
        # Use the existing hid_macropad_control.py logic
        from hid_macropad_control import HIDMacropadController
        controller = HIDMacropadController(self.projectors, self.debug_mode)
        controller.run()
    
    def run(self):
        """Start the macropad listener"""
        print("🎬 Macropad Service Control Started")
        print(f"   Projectors: {len(self.projectors)}")
        print(f"   Debug mode: {self.debug_mode}")
        print("\nButton mappings:")
        for button_num, (func_name, _) in self.button_functions.items():
            print(f"   Button {button_num} (F{button_num}): {func_name}")
        print()
        
        # Try evdev first (best for Linux headless)
        if EVDEV_AVAILABLE:
            print("🔍 Trying evdev (Linux headless)...")
            if self.run_evdev():
                return
        
        # Fallback to raw HID
        if HID_AVAILABLE:
            print("🔍 Trying raw HID (fallback)...")
            self.run_hid()
            return
        
        print("❌ No HID access method available")
        print("   Install: sudo apt install python3-evdev python3-hidapi")
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.manager.close()

def main():
    """Main function"""
    from config import PROJECTORS
    
    controller = MacropadServiceController(
        projectors=PROJECTORS,
        debug_mode=True
    )
    
    try:
        controller.run()
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()

