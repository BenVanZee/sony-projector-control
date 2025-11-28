#!/usr/bin/env python3
"""
USB Keypad Control for Sony Projector System
Supports various 4-button USB keypads including Cut/Copy/Paste keypads
"""

import time
import threading
import sys
import os
from typing import Dict, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from projector_control import ProjectorManager, ProjectorController
from macropad.usb_keypad_config import get_keypad_config, BUTTON_FUNCTIONS

# Try to import keyboard support
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("❌ Keyboard support not available - install 'pynput' package")
    print("   Install with: pip install pynput")

class USBKeypadController:
    """Controls USB keypad input for projector control"""
    
    def __init__(self, projectors: list, keypad_type: str = "cut_copy_paste", debug_mode: bool = True):
        self.projectors = projectors
        self.keypad_type = keypad_type
        self.debug_mode = debug_mode
        
        # Filter out rear projector for freeze operations since it doesn't support freeze functionality
        filtered_projectors = [p for p in projectors if p[0] != '10.10.10.4']
        self.manager = ProjectorManager(filtered_projectors)
        self.running = False
        
        # Get keypad configuration
        self.key_mappings = get_keypad_config(keypad_type)
        
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
                logging.FileHandler('usb_keypad_control.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def on_press(self, key):
        """Handle key press events"""
        try:
            if self.debug_mode:
                print(f"\n🔑 Key pressed: {key}")
            
            # Map key to button number
            button_num = self.key_mappings.get(key)
            
            if button_num:
                self.handle_button_press(button_num, str(key))
            else:
                if self.debug_mode:
                    print(f"   ⚠️  Unknown key: {key}")
                    print(f"   Available keys: {list(self.key_mappings.keys())}")
                
        except AttributeError:
            # Special keys like ctrl, shift, etc.
            if self.debug_mode:
                print(f"   Special key: {key}")
                
    def on_release(self, key):
        """Handle key release events"""
        # Stop listener on escape key
        if key == Key.esc:
            print("\n🛑 ESC key pressed - stopping listener...")
            self.running = False
            return False
            
    def handle_button_press(self, button_num: int, key_name: str = "Unknown"):
        """Handle button press and execute action"""
        try:
            print(f"\n🎯 BUTTON {button_num} ACTIVATED!")
            print(f"   Function: {BUTTON_FUNCTIONS[button_num]}")
            print(f"   Key: {key_name}")
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
                result = self.manager.mute_all(False)
                action = "unmuted"
            else:
                result = self.manager.mute_all(True)
                action = "muted"
                
            success_count = sum(1 for success in result.values() if success)
            total_count = len(result)
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
                result = self.manager.freeze_all_screens(False)
                action = "unfrozen"
            else:
                result = self.manager.freeze_all_screens(True)
                action = "frozen"
                
            success_count = sum(1 for success in result.values() if success)
            total_count = len(result)
            if success_count == total_count:
                print(f"✅ All screens {action} successfully")
            else:
                print(f"❌ Failed to {action} {total_count - success_count} of {total_count} screens")
                
        except Exception as e:
            print(f"❌ Error toggling freeze: {e}")
            self.logger.error(f"Freeze toggle error: {e}")
            
    def run(self):
        """Start the USB keypad listener"""
        if not KEYBOARD_AVAILABLE:
            print("❌ Cannot start - keyboard support not available")
            return
            
        print(f"🎬 USB Keypad Control Started")
        print(f"   Keypad type: {self.keypad_type}")
        print(f"   Projectors: {len(self.projectors)}")
        print(f"   Debug mode: {self.debug_mode}")
        print("\nButton mappings:")
        for key, button in self.key_mappings.items():
            print(f"   {key} → Button {button}: {BUTTON_FUNCTIONS[button]}")
        print("\nPress buttons on your USB keypad to control projectors!")
        print("Press ESC key to exit\n")
        
        self.running = True
        
        # Start keyboard listener
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\n🛑 Keyboard interrupt - stopping...")
                self.running = False

def main():
    """Main function for testing"""
    import sys
    from config import PROJECTORS
    
    # Parse command line arguments
    keypad_type = "cut_copy_paste"
    debug_mode = True
    
    if len(sys.argv) > 1:
        keypad_type = sys.argv[1]
    if len(sys.argv) > 2:
        debug_mode = sys.argv[2].lower() == "true"
    
    # Create and run controller
    controller = USBKeypadController(
        projectors=PROJECTORS,
        keypad_type=keypad_type,
        debug_mode=debug_mode
    )
    
    try:
        controller.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
