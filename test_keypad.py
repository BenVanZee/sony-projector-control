#!/usr/bin/env python3
"""
4-Button USB-C Keypad Test Script
Test script to verify USB keypad functionality and see what values each button returns
Compatible with macOS, Linux, and Windows
"""

import time
import sys
import threading
from typing import Dict, Optional

# Try to import cross-platform keyboard support
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    KEYBOARD_AVAILABLE = True
    print("✅ Cross-platform keyboard support detected - pynput available")
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("❌ Keyboard support not available - install 'pynput' package")
    print("   Install with: pip install pynput")

class USBKeypadTester:
    """USB keypad tester to verify button functionality"""
    
    def __init__(self):
        self.running = False
        self.button_press_count = {1: 0, 2: 0, 3: 0, 4: 0}
        self.last_button_press = None
        self.listener = None
        
        # Button mapping for reference
        self.button_functions = {
            1: "Turn projectors OFF (Ctrl)",
            2: "Turn projectors ON (C)", 
            3: "Toggle screen blanking (V)",
            4: "Toggle screen freezing (Enter)"
        }
        
        # Key mappings for your specific keypad - only set if pynput is available
        self.key_mappings = {}
        if KEYBOARD_AVAILABLE:
            from pynput.keyboard import Key, KeyCode
            self.key_mappings = {
                Key.ctrl: 1,        # Ctrl key - Turn projectors OFF
                KeyCode.from_char('c'): 2,  # C key - Turn projectors ON
                KeyCode.from_char('v'): 3,  # V key - Toggle screen blanking
                Key.enter: 4,       # Enter key - Toggle screen freezing
            }
        
    def on_press(self, key):
        """Handle key press events"""
        try:
            print(f"\n🔑 Key pressed: {key}")
            
            # Map key to button number
            button_num = self.key_mappings.get(key)
            
            if button_num:
                self.handle_button_press(button_num, str(key))
            else:
                print(f"   ⚠️  Unknown key: {key}")
                print(f"   Add mapping in key_mappings if needed")
                
        except AttributeError:
            # Special keys like ctrl, shift, etc.
            print(f"   Special key: {key}")
            
    def on_release(self, key):
        """Handle key release events"""
        # Stop listener on escape key
        if key == Key.esc:
            print("\n🛑 ESC key pressed - stopping listener...")
            self.running = False
            return False
            
    def handle_button_press(self, button_num: int, key_name: str = "Unknown"):
        """Handle button press and display information"""
        self.button_press_count[button_num] += 1
        self.last_button_press = (button_num, time.time())
        
        print(f"\n🎯 BUTTON {button_num} ACTIVATED!")
        print(f"   Function: {self.button_functions[button_num]}")
        print(f"   Key: {key_name}")
        print(f"   Press count: {self.button_press_count[button_num]}")
        print(f"   Time: {time.strftime('%H:%M:%S')}")
        
        # Show all button counts
        print(f"\n📊 Total button presses:")
        for btn, count in self.button_press_count.items():
            print(f"   Button {btn}: {count} presses")
            
    def run_keyboard_mode(self):
        """Run in keyboard listening mode"""
        print("\n🔌 Running in keyboard listening mode...")
        print("Press buttons on your USB keypad to test them!")
        print("Press ESC key to exit\n")
        
        self.running = True
        
        try:
            # Start keyboard listener
            with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            ) as listener:
                self.listener = listener
                print("🎹 Listening for keypad input...")
                print("   Press Ctrl, C, V, or Enter to test")
                print("   Press ESC to exit")
                
                # Keep the listener running
                while self.running:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Shutting down keypad tester...")
        except Exception as e:
            print(f"❌ Error reading from keypad: {e}")
        finally:
            self.cleanup()
            
    def run_console_mode(self):
        """Run in console mode for testing without USB keypad"""
        print("\n💻 Running in console mode...")
        print("Enter button number (1-4) to simulate button press")
        print("Enter 's' to show stats, 'q' to quit\n")
        
        self.running = True
        try:
            while self.running:
                try:
                    user_input = input("Enter button (1-4) or command (s/q): ").strip().lower()
                    
                    if user_input == 'q':
                        break
                    elif user_input == 's':
                        print(f"\n📊 Button Statistics:")
                        for btn, count in self.button_press_count.items():
                            print(f"   Button {btn}: {count} presses")
                        if self.last_button_press:
                            btn, timestamp = self.last_button_press
                            print(f"   Last button: {btn} at {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
                    else:
                        try:
                            button_num = int(user_input)
                            if 1 <= button_num <= 4:
                                self.handle_button_press(button_num, "Console Input")
                            else:
                                print("❌ Invalid button number (1-4)")
                        except ValueError:
                            print("❌ Invalid input. Use 1-4, 's' for stats, or 'q' to quit")
                            
                except KeyboardInterrupt:
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Shutting down keypad tester...")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if self.listener:
            self.listener.stop()
        print("\n🧹 Cleanup complete")
        
    def show_final_stats(self):
        """Show final statistics"""
        print(f"\n🎯 FINAL TEST RESULTS:")
        print("=" * 40)
        for btn, count in self.button_press_count.items():
            print(f"Button {btn} ({self.button_functions[btn]}): {count} presses")
        print("=" * 40)

def main():
    """Main function"""
    print("🎹 4-Button USB-C Keypad Tester")
    print("=" * 40)
    
    tester = USBKeypadTester()
    
    try:
        if KEYBOARD_AVAILABLE:
            tester.run_keyboard_mode()
        else:
            tester.run_console_mode()
    finally:
        tester.show_final_stats()

if __name__ == "__main__":
    main()
