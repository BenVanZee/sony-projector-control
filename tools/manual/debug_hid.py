#!/usr/bin/env python3
"""Debug script to find and test HID devices"""

import os
import glob

print("=" * 50)
print("HID Device Debug Script")
print("=" * 50)

# Part 1: Check hidraw devices
print("\n1. Checking /dev/hidraw* devices:\n")
for dev in sorted(glob.glob("/dev/hidraw*")):
    basename = os.path.basename(dev)
    uevent_path = f"/sys/class/hidraw/{basename}/device/uevent"
    try:
        with open(uevent_path) as f:
            content = f.read()
            name = ""
            product = ""
            for line in content.split('\n'):
                if line.startswith("HID_NAME="):
                    name = line.split("=", 1)[1]
                if line.startswith("PRODUCT="):
                    product = line.split("=", 1)[1]
            print(f"  {dev}: {name} ({product})")
    except Exception as e:
        print(f"  {dev}: (couldn't read info)")

# Part 2: Try hid library
print("\n2. Enumerating ALL Adafruit interfaces:\n")
try:
    import hid
    
    adafruit_devices = [d for d in hid.enumerate() if d['vendor_id'] == 0x239a]
    
    if not adafruit_devices:
        print("  No Adafruit devices found (vendor 239a)")
        print("\n  All HID devices:")
        for d in hid.enumerate():
            print(f"    {d['vendor_id']:04x}:{d['product_id']:04x} - {d['product_string']} (interface {d['interface_number']})")
    else:
        print(f"  Found {len(adafruit_devices)} Adafruit interface(s):\n")
        
        working_path = None
        for d in adafruit_devices:
            print(f"  Interface {d['interface_number']}:")
            print(f"    VID:PID = {d['vendor_id']:04x}:{d['product_id']:04x}")
            print(f"    Path = {d['path']}")
            print(f"    Product = {d['product_string'] or '(none)'}")
            print(f"    Usage Page = {d.get('usage_page', 'N/A')}")
            print(f"    Usage = {d.get('usage', 'N/A')}")
            
            # Try to open by path
            try:
                dev = hid.device()
                dev.open_path(d['path'])
                print(f"    ✅ Opened successfully!")
                working_path = d['path']
                
                # Try a test read
                dev.set_nonblocking(True)
                data = dev.read(64)
                if data:
                    print(f"    📥 Got data: {bytes(data).hex()}")
                else:
                    print(f"    📭 No data (press a button and re-run)")
                dev.close()
            except Exception as e:
                print(f"    ❌ Failed to open: {e}")
            print()
        
        if working_path:
            print("=" * 50)
            print(f"✅ WORKING PATH FOUND: {working_path}")
            print("=" * 50)
            print("\nUpdate hid_macropad_control.py to use open_path() instead of open()")
            print(f"Or try reading directly:")
            print(f"  python3 -c \"import hid; d=hid.device(); d.open_path({working_path}); print('OK')\"")

except ImportError:
    print("  ERROR: hid module not installed")
    print("  Install with: pip3 install hidapi")

# Part 3: Try direct hidraw access
print("\n3. Trying direct /dev/hidraw access:\n")
for dev in sorted(glob.glob("/dev/hidraw*")):
    try:
        with open(dev, 'rb') as f:
            import select
            # Non-blocking check if readable
            r, _, _ = select.select([f], [], [], 0.1)
            if r:
                data = f.read(64)
                print(f"  {dev}: ✅ Readable, got {len(data)} bytes")
            else:
                print(f"  {dev}: ✅ Opened (no data ready)")
    except PermissionError:
        print(f"  {dev}: ❌ Permission denied")
    except Exception as e:
        print(f"  {dev}: ❌ {e}")

print("\n" + "=" * 50)
