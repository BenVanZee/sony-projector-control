#!/usr/bin/env python3
"""
Auto-start USB Keypad Control for Sony Projector System
Automatically detects USB keypad device and starts control
"""

import time
import os
import sys
import subprocess
import logging
from typing import Optional

# Try to import evdev for direct USB input
try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    print("❌ evdev not available - install with: sudo apt install python3-evdev")

def find_usb_keypad_device():
    """Find the USB keypad device path"""
    if not EVDEV_AVAILABLE:
        return None
        
    try:
        # Look for input devices
        devices = [InputDevice(path) for path in evdev.list_devices()]
        
        for device in devices:
            # Skip keyboard devices
            if 'keyboard' in device.name.lower():
                continue
                
            # Check if it's a keypad-like device
            if ('keypad' in device.name.lower() or 
                'macro' in device.name.lower() or
                'usb' in device.name.lower()):
                print(f"✅ Found USB keypad: {device.name} at {device.path}")
                return device.path
                
            # Check capabilities for key events (but not keyboard)
            if ecodes.EV_KEY in device.capabilities():
                # Skip if it looks like a full keyboard
                key_codes = device.capabilities()[ecodes.EV_KEY]
                if len(key_codes) < 20:  # Keypads typically have fewer keys
                    print(f"✅ Found potential keypad: {device.name} at {device.path}")
                    return device.path
                
        print("❌ No USB keypad found")
        return None
        
    except Exception as e:
        print(f"❌ Error finding USB keypad: {e}")
        return None

def wait_for_usb_keypad(max_wait_time=60):
    """Wait for USB keypad to be available"""
    print("🔍 Waiting for USB keypad to be detected...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        device_path = find_usb_keypad_device()
        if device_path:
            return device_path
        
        print(f"   Still waiting... ({int(time.time() - start_time)}s/{max_wait_time}s)")
        time.sleep(2)
    
    print(f"❌ USB keypad not detected within {max_wait_time} seconds")
    return None

def start_keypad_control(device_path: str):
    """Start the USB keypad control with specific device"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        control_script = os.path.join(script_dir, 'usb_keypad_control_specific.py')
        
        if not os.path.exists(control_script):
            print(f"❌ Control script not found: {control_script}")
            return False
        
        print(f"🚀 Starting USB keypad control with device: {device_path}")
        
        # Start the control script
        cmd = [sys.executable, control_script, device_path, "true"]  # true for debug mode
        process = subprocess.Popen(cmd, cwd=script_dir)
        
        print(f"✅ USB keypad control started (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Error starting keypad control: {e}")
        return None

def main():
    """Main function"""
    print("🎬 USB Keypad Auto-Start Control")
    print("===============================")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('usb_keypad_auto_start.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Check if evdev is available
    if not EVDEV_AVAILABLE:
        print("❌ Cannot start - evdev not available")
        print("   Install with: sudo apt install python3-evdev")
        sys.exit(1)
    
    # Wait for USB keypad to be available
    device_path = wait_for_usb_keypad()
    if not device_path:
        print("❌ Failed to detect USB keypad")
        sys.exit(1)
    
    # Start the control script
    process = start_keypad_control(device_path)
    if not process:
        print("❌ Failed to start keypad control")
        sys.exit(1)
    
    try:
        # Wait for the process to complete
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping USB keypad control...")
        process.terminate()
        process.wait()
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Auto-start error: {e}")
        process.terminate()
        process.wait()
        sys.exit(1)

if __name__ == "__main__":
    main()
