#!/usr/bin/env python3
"""
HID Macropad Control for Sony Projector System
Supports 6-9 button HID macropads for controlling projectors

Uses direct /dev/hidraw access instead of the hid library for better compatibility.
"""

import time
import sys
import os
import glob
import select
import logging
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from projector_control import ProjectorManager

class HIDMacropadController:
    """HID Macropad controller for projector control"""
    
    def __init__(self, projectors: list, debug_mode: bool = True):
        self.projectors = projectors
        self.debug_mode = debug_mode
        
        # Convert config format to expected format
        projector_tuples = [(p['ip'], p['port']) for p in projectors]
        self.manager = ProjectorManager(projector_tuples)
        self.running = False
        self.device = None
        
        # Button mappings for 12-button Adafruit Macropad
        # Row 1: Power controls
        # Row 2: Blank controls  
        # Row 3: Freeze controls
        # Row 4: Reserved (customize as needed)
        self.button_functions = {
            1: ("All On", self.power_on_all),
            2: ("All Off", self.power_off_all),
            3: ("Toggle Power", self.toggle_power),
            4: ("Blank Front", self.blank_front),
            5: ("Unblank Front", self.unblank_front),
            6: ("Toggle Blank", self.toggle_blank),
            7: ("Freeze Front", self.freeze_front),
            8: ("Unfreeze Front", self.unfreeze_front),
            9: ("Toggle Freeze", self.toggle_freeze),
            # Bottom row - customize as needed
            10: ("Reserved 10", self.reserved_button),
            11: ("Reserved 11", self.reserved_button),
            12: ("Reserved 12", self.reserved_button),
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO if debug_mode else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hid_macropad_control.log'),
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
            # Fallback to default front projectors
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
                else:
                    print(f"⚠️  Front projector {ip} not found in manager")
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
                else:
                    print(f"⚠️  Front projector {ip} not found in manager")
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
                else:
                    print(f"⚠️  Front projector {ip} not found in manager")
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
                else:
                    print(f"⚠️  Front projector {ip} not found in manager")
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
    
    def toggle_power(self):
        """Toggle power on all projectors"""
        print("🔌 Toggling power...")
        try:
            status = self.manager.get_all_status()
            # Check if any projector is on
            any_on = any(s.get('power') == 'ON' for s in status.values())
            if any_on:
                self.power_off_all()
            else:
                self.power_on_all()
        except Exception as e:
            print(f"❌ Error toggling power: {e}")
            self.logger.error(f"Toggle power error: {e}")
    
    def toggle_blank(self):
        """Toggle blank on front projectors"""
        print("🎬 Toggling blank...")
        try:
            front_ips = self.get_front_projectors()
            # Check current state of first front projector
            for ip in front_ips:
                if ip in self.manager.controllers:
                    try:
                        controller = self.manager.controllers[ip]
                        with controller:
                            status = controller.get_status()
                            if status.get('mute') == 'MUTED':
                                self.unblank_front()
                            else:
                                self.blank_front()
                            return
                    except Exception as e:
                        self.logger.error(f"Error checking {ip}: {e}")
            # Default to blank if can't determine state
            self.blank_front()
        except Exception as e:
            print(f"❌ Error toggling blank: {e}")
            self.logger.error(f"Toggle blank error: {e}")
    
    def toggle_freeze(self):
        """Toggle freeze on front projectors"""
        print("⏸️  Toggling freeze...")
        try:
            front_ips = self.get_front_projectors()
            # Check current state of first front projector
            for ip in front_ips:
                if ip in self.manager.controllers:
                    try:
                        controller = self.manager.controllers[ip]
                        with controller:
                            status = controller.get_status()
                            if status.get('freeze') == 'FROZEN':
                                self.unfreeze_front()
                            else:
                                self.freeze_front()
                            return
                    except Exception as e:
                        self.logger.error(f"Error checking {ip}: {e}")
            # Default to freeze if can't determine state
            self.freeze_front()
        except Exception as e:
            print(f"❌ Error toggling freeze: {e}")
            self.logger.error(f"Toggle freeze error: {e}")
    
    def reserved_button(self):
        """Placeholder for unassigned buttons"""
        print("⚠️  This button is not assigned. Edit button_functions in hid_macropad_control.py to assign it.")
    
    def find_hid_macropad(self):
        """Find connected HID macropad device using direct /dev/hidraw access"""
        
        print("🔍 Searching for Adafruit Macropad in /dev/hidraw*...")
        
        # Look for Adafruit Macropad by checking device info
        for hidraw_path in sorted(glob.glob("/dev/hidraw*")):
            try:
                basename = os.path.basename(hidraw_path)
                uevent_path = f"/sys/class/hidraw/{basename}/device/uevent"
                
                device_name = ""
                product_info = ""
                
                if os.path.exists(uevent_path):
                    with open(uevent_path) as f:
                        for line in f:
                            if line.startswith("HID_NAME="):
                                device_name = line.split("=", 1)[1].strip()
                            if line.startswith("PRODUCT="):
                                product_info = line.split("=", 1)[1].strip()
                
                # Check if this is the Adafruit Macropad
                is_adafruit = "adafruit" in device_name.lower() or "macropad" in device_name.lower()
                # Also check product ID (239a = Adafruit vendor ID)
                is_adafruit = is_adafruit or "239a" in product_info.lower()
                
                if self.debug_mode:
                    print(f"   {hidraw_path}: {device_name} ({product_info})")
                
                if is_adafruit:
                    # Try to open it
                    try:
                        fd = os.open(hidraw_path, os.O_RDONLY | os.O_NONBLOCK)
                        print(f"✅ Found Adafruit Macropad: {hidraw_path}")
                        print(f"   Device: {device_name}")
                        return fd
                    except PermissionError:
                        print(f"❌ Permission denied for {hidraw_path}")
                        print("   Run: sudo chmod 666 " + hidraw_path)
                        continue
                    except Exception as e:
                        print(f"❌ Failed to open {hidraw_path}: {e}")
                        continue
                        
            except Exception as e:
                if self.debug_mode:
                    print(f"   Error checking {hidraw_path}: {e}")
                continue
        
        # If no Adafruit device found, try to open any hidraw device
        print("\n⚠️  No Adafruit Macropad found by name, trying all hidraw devices...")
        for hidraw_path in sorted(glob.glob("/dev/hidraw*")):
            try:
                fd = os.open(hidraw_path, os.O_RDONLY | os.O_NONBLOCK)
                print(f"✅ Opened {hidraw_path} (may not be macropad)")
                return fd
            except Exception as e:
                if self.debug_mode:
                    print(f"   {hidraw_path}: {e}")
                continue
        
        print("❌ No HID macropad found")
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
    
    def read_hid_events(self):
        """Read button events from HID device using direct /dev/hidraw access"""
        if self.device is None:
            return
        
        try:
            # Use select to check if data is available (non-blocking)
            readable, _, _ = select.select([self.device], [], [], 0.1)
            
            if readable:
                # Read data from hidraw device
                data = os.read(self.device, 64)
                
                if data and len(data) > 0:
                    button_pressed = None
                    
                    # Primary method: First byte is button number (1-12)
                    # This matches our macropad code.py format
                    if data[0] > 0 and data[0] <= 12:
                        button_pressed = data[0]
                    
                    # Fallback: Second byte might be button number
                    elif len(data) > 1 and data[1] > 0 and data[1] <= 12:
                        button_pressed = data[1]
                    
                    if button_pressed:
                        self.handle_button_press(button_pressed)
                    elif self.debug_mode and data[0] != 0:
                        # Only print if not all zeros (which is idle state)
                        print(f"🔍 Raw HID data: {data.hex()}")
                        
        except BlockingIOError:
            # No data available, this is normal for non-blocking read
            pass
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️  HID read error: {e}")
            self.logger.debug(f"HID read error: {e}")
    
    def run(self):
        """Start the HID macropad listener using direct /dev/hidraw access"""
        
        print("🎬 HID Macropad Control Started")
        print(f"   Projectors: {len(self.projectors)}")
        print(f"   Debug mode: {self.debug_mode}")
        print("\nButton mappings:")
        for button_num, (func_name, _) in self.button_functions.items():
            print(f"   Button {button_num}: {func_name}")
        print("\nPress buttons on your HID macropad to control projectors!")
        print("Press Ctrl+C to exit\n")
        
        # Find HID macropad
        self.device = self.find_hid_macropad()
        if self.device is None:
            print("❌ No HID macropad found. Please connect your macropad and try again.")
            print("\n💡 Tips:")
            print("   - Make sure your macropad is connected via USB")
            print("   - Check if your macropad appears in: lsusb")
            print("   - Check permissions: ls -la /dev/hidraw*")
            print("   - If permission denied, run:")
            print("     sudo chmod 666 /dev/hidraw0")
            return
        
        self.running = True
        
        try:
            # Main event loop
            while self.running:
                self.read_hid_events()
                # No sleep needed - select() in read_hid_events handles timing
                
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt - stopping...")
            self.running = False
        except Exception as e:
            print(f"❌ Error: {e}")
            self.logger.error(f"Runtime error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if self.device is not None:
            try:
                os.close(self.device)
            except:
                pass
            self.device = None
        self.manager.close()

def main():
    """Main function"""
    import sys
    from config import PROJECTORS
    
    # Parse command line arguments
    debug_mode = True
    if len(sys.argv) > 1:
        debug_mode = sys.argv[1].lower() == "true"
    
    # Create and run controller
    controller = HIDMacropadController(
        projectors=PROJECTORS,
        debug_mode=debug_mode
    )
    
    try:
        controller.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
