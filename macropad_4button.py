#!/usr/bin/env python3
"""
4-Button Macropad Control for Sony Projector System
Simplified layout with essential functions only
"""

import time
import threading
from typing import Dict, Optional
import logging
from projector_control import ProjectorManager

# Try to import GPIO support (Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("GPIO not available - install 'RPi.GPIO' for Raspberry Pi button support")

class Macropad4Button:
    """4-Button macropad controller with essential functions"""
    
    def __init__(self, projectors: list, debug_mode: bool = True):
        self.projectors = projectors
        self.debug_mode = debug_mode
        self.manager = ProjectorManager(projectors)
        self.running = False
        
        # 4-Button layout - essential functions only
        self.button_actions = {
            1: self.power_on_all,          # Button 1: Power ON all projectors
            2: self.power_off_all,         # Button 2: Power OFF all projectors
            3: self.toggle_mute,           # Button 3: Toggle screen blank
            4: self.toggle_freeze,         # Button 4: Toggle freeze
        }
        
        # Visual feedback states
        self.led_states = {}
        self.setup_visual_feedback()
        
    def setup_visual_feedback(self):
        """Setup visual feedback system for 4 buttons"""
        if GPIO_AVAILABLE:
            # Setup GPIO LEDs for 4 buttons
            self.led_pins = [17, 18, 27, 22]  # GPIO pins for 4 LEDs
            GPIO.setmode(GPIO.BCM)
            for pin in self.led_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
        else:
            print("GPIO not available - using console feedback only")
            
    def set_led(self, button_num: int, state: bool):
        """Set LED state for a button"""
        if GPIO_AVAILABLE and 1 <= button_num <= len(self.led_pins):
            pin = self.led_pins[button_num - 1]
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            
    def flash_led(self, button_num: int, duration: float = 0.5):
        """Flash LED briefly for feedback"""
        if GPIO_AVAILABLE and 1 <= button_num <= len(self.led_pins):
            self.set_led(button_num, True)
            time.sleep(duration)
            self.set_led(button_num, False)
            
    def power_on_all(self):
        """Power on all projectors"""
        print("🔌 Powering on all projectors...")
        try:
            results = self.manager.power_all(True)
            if all(results.values()):
                print("✅ All projectors powered on successfully")
                self.flash_led(1, 1.0)
            else:
                print(f"❌ Power on failed: {results}")
                self.flash_led(1, 0.2)
        except Exception as e:
            print(f"❌ Error powering on: {e}")
            self.flash_led(1, 0.2)
            
    def power_off_all(self):
        """Power off all projectors"""
        print("🔌 Powering off all projectors...")
        try:
            results = self.manager.power_all(False)
            if all(results.values()):
                print("✅ All projectors powered off successfully")
                self.flash_led(2, 1.0)
            else:
                print(f"❌ Power off failed: {results}")
                self.flash_led(2, 0.2)
        except Exception as e:
            print(f"❌ Error powering off: {e}")
            self.flash_led(2, 0.2)
            
    def toggle_mute(self):
        """Toggle screen blank/unblank"""
        print("🎬 Toggling screen mute...")
        try:
            # Get current status and toggle
            status = self.manager.get_all_status()
            current_mute = None
            
            for ip, info in status.items():
                if info['mute'] is not None:
                    current_mute = info['mute'] == 'MUTED'
                    break
                    
            if current_mute is not None:
                new_mute = not current_mute
                results = self.manager.mute_all(new_mute)
                
                if all(results.values()):
                    print(f"✅ Screen {'blanked' if new_mute else 'unblanked'} successfully")
                    self.flash_led(3, 1.0)
                else:
                    print(f"❌ Screen toggle failed: {results}")
                    self.flash_led(3, 0.2)
            else:
                print("❌ Could not determine current mute status")
                self.flash_led(3, 0.2)
                
        except Exception as e:
            print(f"❌ Error toggling mute: {e}")
            self.flash_led(3, 0.2)
            
    def toggle_freeze(self):
        """Toggle freeze on all screens"""
        print("❄️ Toggling screen freeze...")
        try:
            # Get current status and toggle
            status = self.manager.get_all_status()
            current_freeze = None
            
            for ip, info in status.items():
                if info.get('freeze') is not None:
                    current_freeze = info['freeze'] == 'FROZEN'
                    break
                    
            if current_freeze:
                # Unfreeze
                results = self.manager.freeze_all_screens(False)
                if all(results.values()):
                    print("✅ All screens unfrozen successfully")
                    self.flash_led(4, 1.0)
                else:
                    print(f"❌ Unfreeze failed: {results}")
                    self.flash_led(4, 0.2)
            else:
                # Freeze
                results = self.manager.freeze_all_screens(True)
                if all(results.values()):
                    print("✅ All screens frozen successfully")
                    self.flash_led(4, 1.0)
                else:
                    print(f"❌ Freeze failed: {results}")
                    self.flash_led(4, 0.2)
                    
        except Exception as e:
            print(f"❌ Error toggling freeze: {e}")
            self.flash_led(4, 0.2)
            
    def handle_button_press(self, button_num: int):
        """Handle button press from macropad"""
        if button_num in self.button_actions:
            print(f"\n🎯 Button {button_num} pressed")
            self.button_actions[button_num]()
        else:
            print(f"❌ Unknown button: {button_num}")
            
    def setup_gpio_buttons(self):
        """Setup GPIO buttons on Raspberry Pi"""
        if not GPIO_AVAILABLE:
            print("❌ GPIO not available")
            return False
            
        try:
            # Setup GPIO buttons for 4-button layout
            button_pins = [5, 6, 13, 19]  # GPIO pins for 4 buttons
            
            for pin in button_pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
            print(f"✅ GPIO buttons setup on pins: {button_pins}")
            return button_pins
            
        except Exception as e:
            print(f"❌ GPIO button setup error: {e}")
            return False
            
    def run(self):
        """Main macropad loop"""
        print("🎹 Starting 4-Button Macropad Control System")
        print("="*50)
        print("Button Layout:")
        print("1: Power ON All")
        print("2: Power OFF All")
        print("3: Toggle Screen Blank")
        print("4: Toggle Freeze")
        print("="*50)
        
        # Setup GPIO buttons
        gpio_buttons = self.setup_gpio_buttons()
        
        self.running = True
        
        try:
            while self.running:
                # Handle GPIO input
                if gpio_buttons:
                    for i, pin in enumerate(gpio_buttons):
                        if GPIO.input(pin) == GPIO.LOW:  # Button pressed
                            button_num = i + 1
                            self.handle_button_press(button_num)
                            time.sleep(0.2)  # Debounce
                            
                # Console input fallback
                if not gpio_buttons:
                    print("\nNo GPIO detected. Using console input.")
                    print("Enter button number (1-4) or 'q' to quit:")
                    try:
                        user_input = input("> ").strip()
                        if user_input.lower() == 'q':
                            break
                        try:
                            button_num = int(user_input)
                            if 1 <= button_num <= 4:
                                self.handle_button_press(button_num)
                            else:
                                print("Invalid button number (1-4)")
                        except ValueError:
                            print("Invalid input")
                    except KeyboardInterrupt:
                        break
                        
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down macropad...")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        self.manager.close()

def main():
    """Main function"""
    # Import config for projectors and aliases
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
    
    macropad = Macropad4Button(projectors, debug_mode=True)
    macropad.run()

if __name__ == "__main__":
    main()
