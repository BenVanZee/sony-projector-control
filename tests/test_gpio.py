#!/usr/bin/env python3
"""
GPIO Test Script for Raspberry Pi Macropad
Tests buttons and LEDs before running the main system
"""

import time
import sys

# Try to import GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("❌ RPi.GPIO not available")
    print("Install with: sudo pip3 install RPi.GPIO")
    sys.exit(1)

def setup_gpio():
    """Setup GPIO pins for testing"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Button pins (input with pull-up)
    button_pins = [5, 6, 13, 19, 26, 16, 20, 21, 12]
    
    # LED pins (output)
    led_pins = [17, 18, 27, 22, 23, 24, 25, 8, 7]
    
    # Setup buttons
    for pin in button_pins:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    # Setup LEDs
    for pin in led_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        
    return button_pins, led_pins

def test_leds(led_pins):
    """Test all LEDs"""
    print("🔆 Testing LEDs...")
    
    # Test each LED individually
    for i, pin in enumerate(led_pins, 1):
        print(f"  LED {i} (GPIO {pin}): ", end="")
        try:
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(pin, GPIO.LOW)
            print("✅ Working")
        except Exception as e:
            print(f"❌ Error: {e}")
            
    # Test all LEDs together
    print("  All LEDs together: ", end="")
    try:
        for pin in led_pins:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
        for pin in led_pins:
            GPIO.output(pin, GPIO.LOW)
        print("✅ Working")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_buttons(button_pins, led_pins):
    """Test all buttons"""
    print("\n🔘 Testing buttons...")
    print("Press each button to test. Press Ctrl+C to exit.")
    
    try:
        while True:
            for i, pin in enumerate(button_pins):
                if GPIO.input(pin) == GPIO.LOW:  # Button pressed
                    print(f"  Button {i+1} (GPIO {pin}): ✅ Pressed")
                    
                    # Light corresponding LED
                    if i < len(led_pins):
                        GPIO.output(led_pins[i], GPIO.HIGH)
                        time.sleep(0.2)
                        GPIO.output(led_pins[i], GPIO.LOW)
                        
                    time.sleep(0.3)  # Debounce
                    
            time.sleep(0.1)  # Small delay
            
    except KeyboardInterrupt:
        print("\n🛑 Button test stopped")

def test_button_led_pairs(button_pins, led_pins):
    """Test button-LED pairs"""
    print("\n🔗 Testing button-LED pairs...")
    print("Press each button to light its corresponding LED")
    print("Press Ctrl+C to exit.")
    
    try:
        while True:
            for i, pin in enumerate(button_pins):
                if GPIO.input(pin) == GPIO.LOW:  # Button pressed
                    print(f"  Button {i+1} → LED {i+1}")
                    
                    # Light corresponding LED
                    if i < len(led_pins):
                        GPIO.output(led_pins[i], GPIO.HIGH)
                        time.sleep(0.5)
                        GPIO.output(led_pins[i], GPIO.LOW)
                        
                    time.sleep(0.3)  # Debounce
                    
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Pair test stopped")

def cleanup():
    """Cleanup GPIO"""
    GPIO.cleanup()
    print("\n🧹 GPIO cleanup complete")

def main():
    """Main test function"""
    print("🔧 GPIO Test for Raspberry Pi Macropad")
    print("="*50)
    
    if not GPIO_AVAILABLE:
        print("❌ GPIO not available on this system")
        return
        
    try:
        # Setup GPIO
        button_pins, led_pins = setup_gpio()
        print(f"✅ GPIO setup complete")
        print(f"   Buttons: {len(button_pins)} pins")
        print(f"   LEDs: {len(led_pins)} pins")
        
        # Test LEDs
        test_leds(led_pins)
        
        # Test buttons
        test_buttons(button_pins, led_pins)
        
        # Test button-LED pairs
        test_button_led_pairs(button_pins, led_pins)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
