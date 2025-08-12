#!/usr/bin/env python3
"""
Macropad Control for Sony Projector System
Supports USB HID devices and GPIO buttons (Raspberry Pi)
"""

import time
import threading
from typing import Dict, Optional
import logging
from projector_control import ProjectorManager, ProjectorController

# Try to import USB HID support
try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False
    print("USB HID not available - install 'hidapi' for USB macropad support")

# Try to import GPIO support (Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("GPIO not available - install 'RPi.GPIO' for Raspberry Pi button support")

class MacropadController:
    """Controls macropad input and provides visual feedback"""
    
    def __init__(self, projectors: list, debug_mode: bool = True, button_layout: str = "9"):
        self.projectors = projectors
        self.debug_mode = debug_mode
        self.button_layout = button_layout
        self.manager = ProjectorManager(projectors)
        self.running = False
        
        # Macropad button mappings based on layout
        if button_layout == "4":
            self.button_actions = {
                1: self.power_on_all,          # Button 1: Power ON all projectors
                2: self.power_off_all,         # Button 2: Power OFF all projectors
                3: self.toggle_mute,           # Button 3: Toggle screen blank
                4: self.toggle_freeze,         # Button 4: Toggle freeze
            }
        else:  # Default 9-button layout
            self.button_actions = {
                1: self.toggle_mute,           # Button 1: Toggle screen blank
                2: self.toggle_power,          # Button 2: Toggle power
                3: self.power_on_all,          # Button 3: Power ON all projectors
                4: self.status_check,          # Button 4: Status check
                5: self.blank_screen,          # Button 5: Force blank
                6: self.free_screen,           # Button 6: Free screen (clear blanking)
                7: self.toggle_freeze,         # Button 7: Toggle freeze
                8: self.power_off_all,         # Button 8: Power OFF all projectors
                9: self.debug_mode_toggle      # Button 9: Toggle debug mode
            }
        
        # Visual feedback states
        self.led_states = {}
        self.setup_visual_feedback()
        
    def setup_visual_feedback(self):
        """Setup visual feedback system"""
        if GPIO_AVAILABLE:
            # Setup GPIO LEDs for visual feedback based on layout
            if self.button_layout == "4":
                self.led_pins = [17, 18, 27, 22]  # 4 LEDs for 4-button layout
            else:
                self.led_pins = [17, 18, 27, 22, 23, 24, 25, 8, 7]  # 9 LEDs for 9-button layout
                
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
                    self.flash_led(1, 1.0)
                else:
                    print(f"❌ Screen toggle failed: {results}")
                    self.flash_led(1, 0.2)  # Quick flash for error
            else:
                print("❌ Could not determine current mute status")
                self.flash_led(1, 0.2)
                
        except Exception as e:
            print(f"❌ Error toggling mute: {e}")
            self.flash_led(1, 0.2)
            
    def toggle_power(self):
        """Toggle projector power"""
        print("🔌 Toggling projector power...")
        try:
            status = self.manager.get_all_status()
            current_power = None
            
            for ip, info in status.items():
                if info['power'] is not None:
                    current_power = info['power'] == 'ON'
                    break
                    
            if current_power is not None:
                new_power = not current_power
                results = self.manager.power_all(new_power)
                
                if all(results.values()):
                    print(f"✅ Projectors {'powered on' if new_power else 'powered off'} successfully")
                    self.flash_led(2, 1.0)
                else:
                    print(f"❌ Power toggle failed: {results}")
                    self.flash_led(2, 0.2)
            else:
                print("❌ Could not determine current power status")
                self.flash_led(2, 0.2)
                
        except Exception as e:
            print(f"❌ Error toggling power: {e}")
            self.flash_led(2, 0.2)
            
    def status_check(self):
        """Check status of all projectors"""
        print("📊 Checking projector status...")
        try:
            status = self.manager.get_all_status()
            
            print("\n" + "="*50)
            print("PROJECTOR STATUS")
            print("="*50)
            
            for ip, info in status.items():
                print(f"\n{ip}:")
                print(f"  Power: {info['power'] or 'UNKNOWN'}")
                print(f"  Mute: {info['mute'] or 'UNKNOWN'}")
                print(f"  Freeze: {info.get('freeze') or 'UNKNOWN'}")
                print(f"  Online: {'Yes' if info['online'] else 'No'}")
                
                # Visual feedback based on status
                if info['online']:
                    if info['power'] == 'ON':
                        self.set_led(4, True)  # Solid LED for good status
                    else:
                        self.flash_led(4, 0.5)  # Slow flash for powered off
                else:
                    self.flash_led(4, 0.2)  # Fast flash for offline
                    
            print("="*50)
            
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            self.flash_led(4, 0.2)
            
    def blank_screen(self):
        """Force blank all screens"""
        print("⬛ Forcing screen blank...")
        try:
            results = self.manager.mute_all(True)
            if all(results.values()):
                print("✅ All screens blanked successfully")
                self.flash_led(5, 1.0)
            else:
                print(f"❌ Screen blank failed: {results}")
                self.flash_led(5, 0.2)
        except Exception as e:
            print(f"❌ Error blanking screens: {e}")
            self.flash_led(5, 0.2)
            
    def free_screen(self):
        """Free all screens (clear any blanking)"""
        print("🆓 Freeing all screens...")
        try:
            results = self.manager.free_all_screens()
            if all(results.values()):
                print("✅ All screens freed successfully")
                self.flash_led(6, 1.0)
            else:
                print(f"❌ Screen free failed: {results}")
                self.flash_led(6, 0.2)
        except Exception as e:
            print(f"❌ Error freeing screens: {e}")
            self.flash_led(6, 0.2)
            
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
                    self.flash_led(7, 1.0)
                else:
                    print(f"❌ Unfreeze failed: {results}")
                    self.flash_led(7, 0.2)
            else:
                # Freeze
                results = self.manager.freeze_all_screens(True)
                if all(results.values()):
                    print("✅ All screens frozen successfully")
                    self.flash_led(7, 1.0)
                else:
                    print(f"❌ Freeze failed: {results}")
                    self.flash_led(7, 0.2)
                    
        except Exception as e:
            print(f"❌ Error toggling freeze: {e}")
            self.flash_led(7, 0.2)
            
    def power_off_all(self):
        """Power off all projectors"""
        print("🔌 Powering off all projectors...")
        try:
            results = self.manager.power_all(False)
            if all(results.values()):
                print("✅ All projectors powered off successfully")
                self.flash_led(8, 1.0)
            else:
                print(f"❌ Power off failed: {results}")
                self.flash_led(8, 0.2)
            self.flash_led(8, 1.0)
        except Exception as e:
            print(f"❌ Error powering off: {e}")
            self.flash_led(8, 0.2)
            
    def power_on_all(self):
        """Power on all projectors"""
        print("🔌 Powering on all projectors...")
        try:
            results = self.manager.power_all(True)
            if all(results.values()):
                print("✅ All projectors powered on successfully")
                self.flash_led(3, 1.0)
            else:
                print(f"❌ Power on failed: {results}")
                self.flash_led(3, 0.2)
        except Exception as e:
            print(f"❌ Error powering on: {e}")
            self.flash_led(3, 0.2)
            
    def debug_mode_toggle(self):
        """Toggle debug mode"""
        self.debug_mode = not self.debug_mode
        print(f"🔧 Debug mode {'ENABLED' if self.debug_mode else 'DISABLED'}")
        self.flash_led(9, 0.5)
        
    def handle_button_press(self, button_num: int):
        """Handle button press from macropad"""
        if button_num in self.button_actions:
            print(f"\n🎯 Button {button_num} pressed")
            self.button_actions[button_num]()
        else:
            print(f"❌ Unknown button: {button_num}")
            
    def setup_usb_macropad(self):
        """Setup USB HID macropad"""
        if not HID_AVAILABLE:
            print("❌ USB HID not available")
            return False
            
        try:
            # Common macropad vendor/product IDs
            macropad_ids = [
                (0x0C45, 0x8601),  # Stream Deck
                (0x0483, 0x5750),  # Common macropad
                (0x1B1C, 0x0A1F),  # Corsair
            ]
            
            for vendor_id, product_id in macropad_ids:
                try:
                    device = hid.device()
                    device.open(vendor_id, product_id)
                    print(f"✅ USB Macropad connected: {vendor_id:04x}:{product_id:04x}")
                    return device
                except:
                    continue
                    
            print("❌ No USB macropad found")
            return False
            
        except Exception as e:
            print(f"❌ USB macropad setup error: {e}")
            return False
            
    def setup_gpio_buttons(self):
        """Setup GPIO buttons on Raspberry Pi"""
        if not GPIO_AVAILABLE:
            print("❌ GPIO not available")
            return False
            
        try:
            # Setup GPIO buttons based on layout
            if self.button_layout == "4":
                button_pins = [5, 6, 13, 19]  # 4 buttons for 4-button layout
            else:
                button_pins = [5, 6, 13, 19, 26, 16, 20, 21, 12]  # 9 buttons for 9-button layout
            
            for pin in button_pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
            print(f"✅ GPIO buttons setup on pins: {button_pins}")
            return button_pins
            
        except Exception as e:
            print(f"❌ GPIO button setup error: {e}")
            return False
            
    def run(self):
        """Main macropad loop"""
        print("🎹 Starting Macropad Control System")
        print("="*50)
        
        if self.button_layout == "4":
            print("4-Button Layout:")
            print("1: Power ON All")
            print("2: Power OFF All")
            print("3: Toggle Screen Blank")
            print("4: Toggle Freeze")
        else:
            print("9-Button Layout:")
            print("1: Toggle Screen Blank")
            print("2: Toggle Power")
            print("3: Power ON All")
            print("4: Status Check")
            print("5: Force Blank")
            print("6: Free Screen (clear blanking)")
            print("7: Toggle Freeze")
            print("8: Power OFF All")
            print("9: Toggle Debug")
            
        print("="*50)
        
        # Try USB macropad first
        usb_device = self.setup_usb_macropad()
        
        # Setup GPIO buttons as fallback
        gpio_buttons = self.setup_gpio_buttons()
        
        self.running = True
        
        try:
            while self.running:
                # Handle USB input
                if usb_device:
                    try:
                        data = usb_device.read(64, timeout_ms=100)
                        if data:
                            # Process USB data (simplified)
                            button_num = data[0] if data[0] > 0 else None
                            if button_num:
                                self.handle_button_press(button_num)
                    except:
                        pass
                        
                # Handle GPIO input
                if gpio_buttons:
                    for i, pin in enumerate(gpio_buttons):
                        if GPIO.input(pin) == GPIO.LOW:  # Button pressed
                            button_num = i + 1
                            self.handle_button_press(button_num)
                            time.sleep(0.2)  # Debounce
                            
                # Console input fallback
                if not usb_device and not gpio_buttons:
                    print("\nNo macropad detected. Using console input.")
                    print("Enter button number (1-9) or 'q' to quit:")
                    try:
                        user_input = input("> ").strip()
                        if user_input.lower() == 'q':
                            break
                        try:
                            button_num = int(user_input)
                            if 1 <= button_num <= 9:
                                self.handle_button_press(button_num)
                            else:
                                print("Invalid button number (1-9)")
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
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Sony Projector Macropad Control')
    parser.add_argument('--layout', choices=['4', '9'], default='9',
                       help='Button layout: 4 or 9 buttons (default: 9)')
    args = parser.parse_args()
    
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
    
    print(f"🎹 Starting {args.layout}-button macropad control system")
    macropad = MacropadController(projectors, debug_mode=True, button_layout=args.layout)
    macropad.run()

if __name__ == "__main__":
    main()
