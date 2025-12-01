#!/usr/bin/env python3
"""
HID Macropad Control for Sony Projector System
Supports 6-9 button HID macropads for controlling projectors
"""

import time
import sys
import os
import logging
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from projector_control import ProjectorManager

# Try to import USB HID support
HID_AVAILABLE = False
HID_IMPORT_ERROR = None

try:
    import hid
    HID_AVAILABLE = True
except ImportError as e:
    HID_AVAILABLE = False
    HID_IMPORT_ERROR = str(e)
    # Don't print here - let the run() method provide better diagnostics

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
        
        # Button mappings (6 functions for 6-9 button macropad)
        self.button_functions = {
            1: ("All On", self.power_on_all),
            2: ("All Off", self.power_off_all),
            3: ("Blank Front", self.blank_front),
            4: ("Unblank Front", self.unblank_front),
            5: ("Freeze Front", self.freeze_front),
            6: ("Unfreeze Front", self.unfreeze_front),
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
    
    def find_hid_macropad(self):
        """Find connected HID macropad device"""
        if not HID_AVAILABLE:
            return None
        
        try:
            # List of common HID macropad vendor/product IDs
            # Add your macropad's VID/PID here
            macropad_ids = [
                # Elgato Stream Deck
                (0x0FD9, 0x0060),  # Stream Deck
                (0x0FD9, 0x0063),  # Stream Deck Mini
                (0x0FD9, 0x006C),  # Stream Deck XL
                
                # Generic HID macropads
                (0x0C45, 0x8601),  # Generic macropad
                (0x0483, 0x5750),  # Common HID device
                
                # Corsair
                (0x1B1C, 0x0A1F),  # Corsair K95
                
                # Razer
                (0x1532, 0x0205),  # Razer Tartarus
                
                # Adafruit Macropad
                (0x239A, 0x8027),  # Adafruit Macropad RP2040 (firmware mode)
                (0x239A, 0x8107),  # Adafruit Macropad RP2040 (alternative PID)
                (0x239A, 0x8108),  # Adafruit Macropad RP2040 (HID mode)
            ]
            
            # Try to find any matching device
            for vendor_id, product_id in macropad_ids:
                try:
                    device = hid.device()
                    device.open(vendor_id, product_id)
                    device_info = device.get_manufacturer_string() + " " + device.get_product_string()
                    print(f"✅ Found HID macropad: {device_info} ({vendor_id:04x}:{product_id:04x})")
                    return device
                except:
                    continue
            
            # If no known device found, try to enumerate all HID devices
            print("🔍 Searching for HID devices...")
            for device_info in hid.enumerate():
                vid = device_info['vendor_id']
                pid = device_info['product_id']
                name = device_info.get('product_string', 'Unknown')
                print(f"   Found HID device: {name} ({vid:04x}:{pid:04x})")
                
                # Try to open it
                try:
                    device = hid.device()
                    device.open(vid, pid)
                    print(f"✅ Opened HID device: {name}")
                    return device
                except:
                    continue
            
            print("❌ No HID macropad found")
            return None
            
        except Exception as e:
            print(f"❌ Error finding HID macropad: {e}")
            self.logger.error(f"HID device search error: {e}")
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
        """Read button events from HID device"""
        if not self.device:
            return
        
        try:
            # Read data from HID device with timeout to avoid blocking
            # Use non-blocking read to prevent interfering with other HID devices
            # Short timeout prevents blocking other HID devices like trackpad
            try:
                data = self.device.read(64, timeout_ms=100)  # 100ms timeout, non-blocking
            except Exception as read_error:
                # Handle timeout or read errors gracefully
                if "timeout" not in str(read_error).lower():
                    if self.debug_mode:
                        print(f"⚠️  HID read error: {read_error}")
                return  # Exit early on error, don't block
            
            if data:
                # Parse button presses (implementation depends on macropad)
                # Common format: first byte is button number, or bitmask
                if len(data) > 0:
                    # Try different parsing methods
                    button_pressed = None
                    
                    # Method 1: First byte is button number (1-9)
                    if data[0] > 0 and data[0] <= 9:
                        button_pressed = data[0]
                    
                    # Method 2: Bitmask in first byte
                    elif data[0] > 0:
                        # Find which bit is set
                        for i in range(8):
                            if data[0] & (1 << i):
                                button_pressed = i + 1
                                break
                    
                    # Method 3: Second byte might be button number
                    if not button_pressed and len(data) > 1 and data[1] > 0 and data[1] <= 9:
                        button_pressed = data[1]
                    
                    if button_pressed:
                        self.handle_button_press(button_pressed)
                    elif self.debug_mode:
                        print(f"🔍 Raw HID data: {data.hex()}")
                        
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️  HID read error: {e}")
            self.logger.debug(f"HID read error: {e}")
    
    def run(self):
        """Start the HID macropad listener"""
        if not HID_AVAILABLE:
            print("❌ Cannot start - USB HID not available")
            print()
            print("📋 Diagnostic Information:")
            import sys
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            print(f"   Python version: {sys.version.split()[0]}")
            print(f"   Python executable: {sys.executable}")
            print(f"   Virtual environment: {'Yes' if in_venv else 'No'}")
            if in_venv:
                print(f"   Venv path: {sys.prefix}")
            if HID_IMPORT_ERROR:
                print(f"   Import error: {HID_IMPORT_ERROR}")
            print()
            print("🔧 Installation Options:")
            print()
            if in_venv:
                print("   ⚠️  You're using a virtual environment!")
                print("   Apt packages (python3-hidapi) are NOT available in venv.")
                print()
                print("   ✅ RECOMMENDED: Install via pip in your venv:")
                print("     pip install hidapi")
                print()
                print("   Or install system-wide and use system Python:")
                print("     deactivate  # exit venv")
                print("     sudo apt install -y python3-hidapi")
                print("     python3 run_macropad_with_mocks.py hid-macropad")
            else:
                print("   Option 1: Install via apt (system-wide):")
                print("     sudo apt update")
                print("     sudo apt install -y python3-hidapi")
                print()
                print("   Option 2: If apt package doesn't work, try pip:")
                print("     pip3 install hidapi")
                print("     # Note: May require: sudo apt install libhidapi-hidraw0")
            print()
            print("   Verify installation with:")
            print("     python3 -c 'import hid; print(\"✅ Success! hid module works\")'")
            print()
            print("   If still not working, check:")
            print("     - Are you using 'python3' not 'python'?")
            print("     - Try: which python3")
            print("     - Try: python3 --version")
            print()
            return
        
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
        if not self.device:
            print("❌ No HID macropad found. Please connect your macropad and try again.")
            print("\n💡 Tips:")
            print("   - Make sure your macropad is connected via USB")
            print("   - Check if your macropad appears in: lsusb")
            print("   - You may need to add your macropad's VID/PID to the script")
            print("   - If your device acts as a keyboard, try using:")
            print("     python run_macropad_with_mocks.py usb-keypad")
            print("     (uses keyboard listener instead of raw HID)")
            return
        
        # Check if device might be a keyboard (common issue)
        try:
            device_info = self.device.get_manufacturer_string() + " " + self.device.get_product_string()
            if "keyboard" in device_info.lower() or "trackpad" in device_info.lower():
                print(f"\n⚠️  Warning: Device appears to be a keyboard/trackpad: {device_info}")
                print("   This may cause terminal input issues.")
                print("   Consider using the keyboard listener approach instead:")
                print("   python run_macropad_with_mocks.py usb-keypad")
        except:
            pass
        
        self.running = True
        terminal_modified = False
        old_settings = None
        
        try:
            # Suppress terminal echo if possible (helps with keyboard-like devices)
            # Note: This may not work on all systems, especially macOS
            try:
                import sys
                import termios
                import tty
                # Save terminal settings
                old_settings = termios.tcgetattr(sys.stdin)
                # Set terminal to raw mode (suppresses echo)
                tty.setraw(sys.stdin.fileno())
                terminal_modified = True
            except (ImportError, AttributeError, OSError):
                # termios not available (Windows) or can't modify terminal
                terminal_modified = False
                old_settings = None
            
            # Main event loop
            while self.running:
                self.read_hid_events()
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt - stopping...")
            self.running = False
        except Exception as e:
            print(f"❌ Error: {e}")
            self.logger.error(f"Runtime error: {e}")
        finally:
            # Restore terminal settings
            if terminal_modified and old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except:
                    pass
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if self.device:
            try:
                self.device.close()
            except:
                pass
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
