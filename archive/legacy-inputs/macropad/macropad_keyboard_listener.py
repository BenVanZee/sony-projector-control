#!/usr/bin/env python3
"""
Macropad Control using Keyboard Listener (Alternative to Raw HID)
This approach listens for keyboard events instead of raw HID access,
avoiding the trackpad blocking issue.
"""

import time
import sys
import os
import logging
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from projector_control import ProjectorManager

# Try to import keyboard listener
try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("❌ Keyboard listener not available - install with: pip install pynput")

class MacropadKeyboardListener:
    """Listens for keyboard events from macropad and controls projectors"""
    
    def __init__(self, projectors: list, debug_mode: bool = True):
        self.projectors = projectors
        self.debug_mode = debug_mode
        
        # Convert config format
        projector_tuples = [(p['ip'], p['port']) for p in projectors]
        self.manager = ProjectorManager(projector_tuples)
        self.running = False
        self.listener = None
        
        # Map keyboard keys to button numbers
        # Based on code.py, keys send: F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12
        # Function keys won't appear as text in terminal
        from pynput.keyboard import Key
        self.key_to_button = {
            Key.f1: 1,
            Key.f2: 2,
            Key.f3: 3,
            Key.f4: 4,
            Key.f5: 5,
            Key.f6: 6,
            Key.f7: 7,
            Key.f8: 8,
            Key.f9: 9,
            Key.f10: 10,
            Key.f11: 11,
            Key.f12: 12,
        }
        
        # Button functions (using first 6 for projector control)
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
                logging.FileHandler('macropad_keyboard_control.log'),
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
    
    def on_key_press(self, key):
        """Handle key press events"""
        try:
            # Map key to button number
            button_num = self.key_to_button.get(key)
            
            if button_num and button_num in self.button_functions:
                func_name, func = self.button_functions[button_num]
                print(f"\n🎯 BUTTON {button_num} PRESSED: {func_name}")
                print(f"   Time: {time.strftime('%H:%M:%S')}")
                try:
                    func()
                except Exception as e:
                    print(f"   ❌ Error executing {func_name}: {e}")
                    self.logger.error(f"Button {button_num} error: {e}")
            elif self.debug_mode and button_num:
                print(f"⚠️  Button {button_num} pressed but no function mapped")
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️  Key press error: {e}")
    
    def on_key_release(self, key):
        """Handle key release events"""
        # Stop on ESC key
        from pynput.keyboard import Key
        if key == Key.esc:
            print("\n🛑 ESC key pressed - stopping...")
            self.running = False
            return False
    
    def run(self):
        """Start the keyboard listener"""
        if not KEYBOARD_AVAILABLE:
            print("❌ Cannot start - keyboard listener not available")
            print("   Install with: pip install pynput")
            return
        
        print("🎬 Macropad Keyboard Listener Started")
        print(f"   Projectors: {len(self.projectors)}")
        print(f"   Debug mode: {self.debug_mode}")
        print("\nButton mappings:")
        for button_num, (func_name, _) in self.button_functions.items():
            print(f"   Button {button_num} (F{button_num}): {func_name}")
        print("\n💡 This approach uses keyboard events instead of raw HID")
        print("   This avoids blocking other HID devices like your trackpad!")
        print("\nPress buttons on your macropad to control projectors!")
        print("Press ESC to exit\n")
        
        self.running = True
        
        try:
            # Start keyboard listener
            with keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            ) as listener:
                self.listener = listener
                print("🎹 Listening for macropad key presses...")
                
                # Keep running until stopped
                while self.running:
                    time.sleep(0.1)
        
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
        if self.listener:
            self.listener.stop()
        self.manager.close()

def main():
    """Main function"""
    from config import PROJECTORS
    
    # Create and run controller
    controller = MacropadKeyboardListener(
        projectors=PROJECTORS,
        debug_mode=True
    )
    
    try:
        controller.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

