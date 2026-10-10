# HID Macropad Recommendations for Raspberry Pi

## Overview
This guide provides recommendations for HID macropads that work well with the Raspberry Pi projector control system. You need **6-9 buttons** for the following functions:

1. **All On** - Turn on all projectors
2. **All Off** - Turn off all projectors  
3. **Blank Front** - Blank (mute) front projectors
4. **Unblank Front** - Unblank (unmute) front projectors
5. **Freeze Front** - Freeze front projectors
6. **Unfreeze Front** - Unfreeze front projectors

## ✅ Recommended HID Macropads

### **Budget Options ($15-50)**

#### 1. **Generic USB Programmable Keypad** ⭐ Best Value
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

#### 2. **Adafruit Macropad RP2040** ⭐ Best for DIY
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

#### 3. **Pimoroni Keybow** ⭐ Pi-Specific
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

### **Mid-Range Options ($50-150)**

#### 4. **Elgato Stream Deck Mini** ⭐ Most Popular
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

#### 5. **Corsair K95 RGB** (Keyboard with Macro Keys)
- **Price**: $150-200
- **Buttons**: Full keyboard + 6 macro keys
- **Connection**: USB-A
- **Pros**: 
  - Professional build quality
  - Dedicated macro keys
  - RGB lighting
- **Cons**: 
  - Expensive
  - Full keyboard (may be overkill)
- **Where to buy**: Amazon, Corsair website

#### 6. **Razer Tartarus V2** ⭐ Gaming Keypad
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

### **Professional Options ($150+)**

#### 7. **Elgato Stream Deck** ⭐ Best Overall
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

#### 8. **Loupedeck Live**
- **Price**: $200-250
- **Buttons**: 12 programmable keys
- **Connection**: USB-A
- **Pros**: 
  - Professional quality
  - Good for video/photo editing
  - Excellent build quality
- **Cons**: 
  - Very expensive
  - May be overkill
- **Where to buy**: Loupedeck website

## 🎯 **Top Recommendations**

### **For Your Use Case (6 functions, 6' cable):**

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

## 🔧 **Setup Instructions**

### **1. Install Dependencies**
```bash
# On your Raspberry Pi
sudo apt update
sudo apt install -y python3-hidapi
```

### **2. Find Your Macropad's VID/PID**
```bash
# Connect your macropad and run:
lsusb

# Look for your macropad in the output
# Example: Bus 001 Device 003: ID 0c45:8601 Microdia USB Keyboard
# VID = 0c45, PID = 8601
```

### **3. Update the Script (if needed)**
If your macropad isn't automatically detected, edit `macropad/hid_macropad_control.py` and add your VID/PID to the `macropad_ids` list:

```python
macropad_ids = [
    (0x0C45, 0x8601),  # Your macropad VID/PID
    # ... other IDs
]
```

### **4. Test Your Macropad**
```bash
# Run the HID macropad control script
python3 macropad/hid_macropad_control.py

# Press buttons and verify they're detected
```

### **5. Set Up Auto-Start**
```bash
# Create systemd service
sudo nano /etc/systemd/system/hid-macropad-control.service
```

Add this content:
```ini
[Unit]
Description=HID Macropad Control for Projectors
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/projector-control
Environment=PATH=/opt/projector-control/venv/bin
ExecStart=/opt/projector-control/venv/bin/python3 macropad/hid_macropad_control.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hid-macropad-control.service
sudo systemctl start hid-macropad-control.service
```

## 📋 **Button Mapping**

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

## 🔍 **Troubleshooting**

### **Macropad Not Detected**
1. Check USB connection: `lsusb`
2. Verify VID/PID matches in script
3. Check permissions: `sudo chmod 666 /dev/hidraw*`
4. Try running with sudo (temporary test)

### **Buttons Not Working**
1. Check button mapping in script
2. Verify HID data format matches your macropad
3. Enable debug mode: `python3 macropad/hid_macropad_control.py`
4. Check logs: `tail -f logs/hid_macropad_control.log`

### **USB Extension Issues**
1. Use a powered USB hub if needed
2. Try a shorter extension cable
3. Check USB cable quality
4. Verify USB 2.0/3.0 compatibility

## 💡 **Tips**

1. **Label Your Buttons**: Use physical labels or stickers to mark button functions
2. **Test First**: Test all buttons before final installation
3. **Backup Config**: Save your VID/PID configuration
4. **USB Extension**: Use a quality USB extension cable for 6' runs
5. **Power**: Some macropads may need powered USB hub for long cables

## 📚 **Additional Resources**

- **HID Macropad Control Script**: `macropad/hid_macropad_control.py`
- **Projector CLI**: `projector_cli.py` (for testing commands)
- **Configuration**: `config.py` (projector settings)

## 🛒 **Where to Buy**

- **Amazon**: Best selection, fast shipping
- **Adafruit**: Best for DIY/open source options
- **Pimoroni**: Best for Pi-specific hardware
- **AliExpress**: Best prices, longer shipping
- **Local Electronics Stores**: Best for immediate needs

## ✅ **Final Recommendation**

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

