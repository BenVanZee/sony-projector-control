# Macropad Setup Guide

Complete guide for setting up macropads (Adafruit Macropad RP2040 and other HID macropads) to control your Sony projector system.

## Adafruit Macropad RP2040

### Quick Start

1. **Install CircuitPython** on the macropad (if not already installed)
2. **Copy `macropad/boot.py` and `macropad/code.py`** to the CIRCUITPY drive
3. **Install `adafruit_hid` library** to `CIRCUITPY/lib/`
4. **Unplug and replug** the macropad (boot.py runs on power-up)

The macropad display will show button function labels via print() statements at startup and when buttons are pressed.

The macropad now sends **raw HID reports** (not keyboard F-keys), which:
- ✅ Won't interfere with terminal input
- ✅ Works headless as a systemd service
- ✅ Can be read directly via `/dev/hidraw*`

### Button Mappings

| Button | Raw HID Value | Function |
|--------|---------------|----------|
| 1 | 0x01 | All On |
| 2 | 0x02 | All Off |
| 3 | 0x03 | Toggle Power |
| 4 | 0x04 | Blank Front |
| 5 | 0x05 | Unblank Front |
| 6 | 0x06 | Toggle Blank |
| 7 | 0x07 | Freeze Front |
| 8 | 0x08 | Unfreeze Front |
| 9 | 0x09 | Toggle Freeze |
| 10-12 | 0x0A-0x0C | (Reserved) |

### Usage

#### Raspberry Pi (Headless Service) - Recommended
```bash
# Run the setup script (installs deps, creates service, sets permissions)
./scripts/create_macropad_service.sh

# Start the service
sudo systemctl start macropad-control.service

# View logs
journalctl -u macropad-control.service -f
```

#### Manual Testing
```bash
python3 macropad/macropad_service_control.py
```

### Troubleshooting

**Macropad in REPL mode?**
- Press CTRL+D on computer keyboard to reload
- Or re-save `code.py` to trigger auto-reload

**Trackpad stops working?**
- Use `macropad/macropad_keyboard_listener.py` instead of `macropad/hid_macropad_control.py`
- The keyboard listener approach doesn't block other HID devices

**Permission errors?**
- System Settings → Privacy & Security → Input Monitoring
- Enable Terminal or Python
- Restart Terminal after enabling

**Code keeps crashing?**
- Check that `adafruit_hid` library is in `CIRCUITPY/lib/`
- Download from: https://circuitpython.org/libraries

**Display not showing button labels?**
- The display automatically shows print() output, including button function labels at startup
- Button labels are printed when the macropad starts up
- When you press a button, it shows "Button X pressed: Function Name"

## Service Setup (Raspberry Pi)

### How It Works

The service uses `macropad/macropad_service_control.py` which:

- ✅ Tries **evdev** first (best for Linux headless)
- ✅ Falls back to **raw HID** via direct `/dev/hidraw*` access
- ✅ Works headless (no display needed)
- ✅ Won't interfere with terminal input
- ✅ Auto-restarts on failure

### Quick Setup

Run the setup script (recommended):

```bash
./scripts/create_macropad_service.sh
```

This will:
1. Install `python3-evdev` and `python3-hidapi`
2. Create udev rules for HID permissions
3. Create and enable the systemd service

### Manual Setup

#### 1. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3-evdev python3-hidapi
```

#### 2. Set Up HID Permissions

```bash
# Create udev rule (or run setup_hid_permissions.sh)
echo 'KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0666"' | sudo tee /etc/udev/rules.d/99-hidraw-permissions.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

See [HID_PERMISSIONS.md](HID_PERMISSIONS.md) for more details.

#### 3. Create Service

```bash
sudo nano /etc/systemd/system/macropad-control.service
```

Add this content (update paths/user as needed):

```ini
[Unit]
Description=Adafruit Macropad RP2040 Control for Sony Projectors
After=network.target
Wants=network.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/opt/projector-control
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 /opt/projector-control/macropad/macropad_service_control.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
```

#### 4. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable macropad-control.service
sudo systemctl start macropad-control.service
sudo systemctl status macropad-control.service
```

#### 5. View Logs

```bash
# Follow logs in real-time
journalctl -u macropad-control.service -f

# View last 50 lines
journalctl -u macropad-control.service -n 50
```

### Service Management

```bash
# Start service
sudo systemctl start macropad-control.service

# Stop service
sudo systemctl stop macropad-control.service

# Restart service
sudo systemctl restart macropad-control.service

# Disable auto-start
sudo systemctl disable macropad-control.service

# Check if running
sudo systemctl is-active macropad-control.service
```

### Troubleshooting

#### Service Won't Start

1. **Check logs:**
   ```bash
   sudo journalctl -u macropad-control.service -n 50
   ```

2. **Check permissions:**
   - Make sure the user has permission to access HID devices
   - May need to add user to `input` group:
     ```bash
     sudo usermod -a -G input $USER
     ```

3. **Check device detection:**
   ```bash
   # Test if macropad is detected
   python3 macropad/hid_macropad_control.py
   ```

#### Macropad Not Detected

1. **Check USB connection:**
   ```bash
   lsusb | grep -i adafruit
   ```

2. **Check HID devices:**
   ```bash
   python3 -c "import hid; devices = hid.enumerate(); print([d for d in devices if d['vendor_id'] == 0x239a])"
   ```

3. **Verify VID/PID in script:**
   - Check `macropad/hid_macropad_control.py` includes your macropad's PID (0x8108)

#### Trackpad/Keyboard Issues

If the service blocks other HID devices:
- The script uses non-blocking reads with timeout
- Should not interfere with other devices
- If issues persist, check the timeout settings in `read_hid_events()`

### Notes

- **Function keys (F1-F12)**: The macropad sends function keys, which won't appear as text in terminal
- **Headless operation**: Raw HID works without display/X server
- **Auto-restart**: Service automatically restarts if it crashes
- **Logging**: All output goes to systemd journal

### Alternative: Keyboard Listener (Desktop Only)

If you're running on a desktop (not headless), you can use:

```bash
python3 macropad/macropad_keyboard_listener.py
```

But this **won't work as a service** - only for interactive use.

## HID Macropad Recommendations

### Overview
This section provides recommendations for HID macropads that work well with the Raspberry Pi projector control system. You need **6-9 buttons** for the following functions:

1. **All On** - Turn on all projectors
2. **All Off** - Turn off all projectors  
3. **Blank Front** - Blank (mute) front projectors
4. **Unblank Front** - Unblank (unmute) front projectors
5. **Freeze Front** - Freeze front projectors
6. **Unfreeze Front** - Unfreeze front projectors

### ✅ Recommended HID Macropads

#### **Budget Options ($15-50)**

##### 1. **Generic USB Programmable Keypad** ⭐ Best Value
- **Price**: $15-30
- **Buttons**: 4-9 programmable keys
- **Connection**: USB-A
- **Pros**: 
  - Very affordable
  - Works with USB extension cables
  - Simple setup
- **Cons**: 
  - May require VID/PID configuration
  - Basic build quality
- **Where to buy**: Amazon, AliExpress
- **Search terms**: "USB programmable keypad", "HID macropad", "programmable keypad"

##### 2. **Adafruit Macropad RP2040** ⭐ Best for DIY
- **Price**: $25-35
- **Buttons**: 12 keys + rotary encoder
- **Connection**: USB-C
- **Pros**: 
  - Open source firmware
  - Highly customizable
  - Good documentation
  - Works great with Raspberry Pi
- **Cons**: 
  - Requires some setup
  - May need firmware configuration
- **Where to buy**: Adafruit, SparkFun
- **Link**: https://www.adafruit.com/product/5128

##### 3. **Pimoroni Keybow** ⭐ Pi-Specific
- **Price**: $30-40
- **Buttons**: 4-16 keys
- **Connection**: GPIO (plugs directly into Pi)
- **Pros**: 
  - Designed specifically for Raspberry Pi
  - No USB conflicts
  - Excellent build quality
- **Cons**: 
  - Must be close to Pi (GPIO connection)
  - Slightly more expensive
- **Where to buy**: Pimoroni
- **Link**: https://shop.pimoroni.com/products/keybow

#### **Mid-Range Options ($50-150)**

##### 4. **Elgato Stream Deck Mini** ⭐ Most Popular
- **Price**: $80-100
- **Buttons**: 6 LCD keys
- **Connection**: USB-A
- **Pros**: 
  - Professional quality
  - LCD screens on each key (can show labels)
  - Excellent software support
  - Works with USB extension
- **Cons**: 
  - More expensive
  - May need software configuration
- **Where to buy**: Amazon, Best Buy, Elgato website
- **Note**: May require additional setup for Linux/Pi

##### 5. **Razer Tartarus V2** ⭐ Gaming Keypad
- **Price**: $80-100
- **Buttons**: 32 programmable keys
- **Connection**: USB-A
- **Pros**: 
  - Many programmable keys
  - Good build quality
  - Thumb pad for additional controls
- **Cons**: 
  - More than you need
  - Gaming-focused design
- **Where to buy**: Amazon, Razer website

#### **Professional Options ($150+)**

##### 6. **Elgato Stream Deck** ⭐ Best Overall
- **Price**: $150-200
- **Buttons**: 15 LCD keys
- **Connection**: USB-A
- **Pros**: 
  - Professional quality
  - LCD screens show labels/icons
  - Excellent software
  - Industry standard
- **Cons**: 
  - Expensive
  - More buttons than needed
- **Where to buy**: Amazon, Elgato website

### 🎯 **Top Recommendations**

#### **For Your Use Case (6 functions, 6' cable):**

1. **Best Overall**: **Generic USB Programmable Keypad** ($15-30)
   - Affordable
   - Works with USB extension
   - Simple setup
   - Perfect for 6 functions

2. **Best Quality**: **Elgato Stream Deck Mini** ($80-100)
   - Professional build
   - LCD labels on keys
   - Reliable
   - Works great with USB extension

3. **Best for Pi**: **Adafruit Macropad RP2040** ($25-35)
   - Open source
   - Great documentation
   - Works perfectly with Pi
   - Highly customizable

### 🔧 **Setup Instructions**

#### **1. Install Dependencies**
```bash
# On your Raspberry Pi
sudo apt update
sudo apt install -y python3-hidapi
```

#### **2. Find Your Macropad's VID/PID**
```bash
# Connect your macropad and run:
lsusb

# Look for your macropad in the output
# Example: Bus 001 Device 003: ID 0c45:8601 Microdia USB Keyboard
# VID = 0c45, PID = 8601
```

#### **3. Update the Script (if needed)**
If your macropad isn't automatically detected, edit `macropad/hid_macropad_control.py` and add your VID/PID to the `macropad_ids` list:

```python
macropad_ids = [
    (0x0C45, 0x8601),  # Your macropad VID/PID
    # ... other IDs
]
```

#### **4. Test Your Macropad**
```bash
# Run the HID macropad control script
python3 macropad/hid_macropad_control.py

# Press buttons and verify they're detected
```

### 📋 **Button Mapping**

The script maps buttons as follows:

| Button | Function | Description |
|--------|----------|-------------|
| 1 | All On | Turn on all projectors |
| 2 | All Off | Turn off all projectors |
| 3 | Blank Front | Blank (mute) front projectors |
| 4 | Unblank Front | Unblank (unmute) front projectors |
| 5 | Freeze Front | Freeze front projectors |
| 6 | Unfreeze Front | Unfreeze front projectors |
| 7-9 | (Reserved) | Available for future functions |

### 🔍 **Troubleshooting**

#### **Macropad Not Detected**
1. Check USB connection: `lsusb`
2. Verify VID/PID matches in script
3. Check permissions: `sudo chmod 666 /dev/hidraw*`
4. Try running with sudo (temporary test)

#### **Buttons Not Working**
1. Check button mapping in script
2. Verify HID data format matches your macropad
3. Enable debug mode: `python3 macropad/hid_macropad_control.py`
4. Check logs: `tail -f logs/hid_macropad_control.log`

#### **USB Extension Issues**
1. Use a powered USB hub if needed
2. Try a shorter extension cable
3. Check USB cable quality
4. Verify USB 2.0/3.0 compatibility

### 💡 **Tips**

1. **Label Your Buttons**: Use physical labels or stickers to mark button functions
2. **Test First**: Test all buttons before final installation
3. **Backup Config**: Save your VID/PID configuration
4. **USB Extension**: Use a quality USB extension cable for 6' runs
5. **Power**: Some macropads may need powered USB hub for long cables

### 🛒 **Where to Buy**

- **Amazon**: Best selection, fast shipping
- **Adafruit**: Best for DIY/open source options
- **Pimoroni**: Best for Pi-specific hardware
- **AliExpress**: Best prices, longer shipping
- **Local Electronics Stores**: Best for immediate needs

### ✅ **Final Recommendation**

For your specific needs (6 functions, 6' cable, Raspberry Pi):

**Get a Generic USB Programmable Keypad ($15-30) + USB Extension Cable ($10)**

**Total Cost: ~$25-40**

This gives you:
- ✅ Affordable solution
- ✅ Reliable operation
- ✅ Works with USB extension
- ✅ Easy to set up
- ✅ Perfect for 6 functions

If you want better quality and LCD labels, go with the **Elgato Stream Deck Mini** ($80-100).





