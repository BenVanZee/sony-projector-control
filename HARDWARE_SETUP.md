# Hardware Setup Guide for Projector Control Macropad

This guide shows you how to build a custom macropad for controlling your Sony projectors. You have several options depending on your budget and technical skills.

## Option 1: Raspberry Pi + GPIO Buttons (Recommended)

### Parts Needed
- Raspberry Pi (any model with GPIO pins)
- 9x Tactile push buttons
- 9x LEDs (any color)
- 9x 220Ω resistors
- Breadboard and jumper wires
- Enclosure/case (optional)

### Wiring Diagram
```
Button Layout (9 buttons):
┌─────┬─────┬─────┐
│  1  │  2  │  3  │  ← Row 1: Screen, Power, Emergency
├─────┼─────┼─────┤
│  4  │  5  │  6  │  ← Row 2: Status, Blank, Unblank  
├─────┼─────┼─────┤
│  7  │  8  │  9  │  ← Row 3: Power On, Power Off, Debug
└─────┴─────┴─────┘

GPIO Pin Mapping:
Button 1 → GPIO 5   LED → GPIO 17
Button 2 → GPIO 6   LED → GPIO 18  
Button 3 → GPIO 13  LED → GPIO 27
Button 4 → GPIO 19  LED → GPIO 22
Button 5 → GPIO 26  LED → GPIO 23
Button 6 → GPIO 16  LED → GPIO 24
Button 7 → GPIO 20  LED → GPIO 25
Button 8 → GPIO 21  LED → GPIO 8
Button 9 → GPIO 12  LED → GPIO 7
```

### Wiring Instructions
1. **Connect buttons**: Each button connects between a GPIO pin and ground
2. **Connect LEDs**: Each LED connects through a 220Ω resistor to a GPIO pin
3. **Power**: Connect 3.3V and ground from Pi to breadboard
4. **Pull-up resistors**: Pi has internal pull-ups, so buttons work when pressed

### Button Functions
- **Button 1**: Toggle screen blank/unblank
- **Button 2**: Toggle projector power
- **Button 3**: Emergency power off
- **Button 4**: Status check
- **Button 5**: Force blank screen
- **Button 6**: Free screen (clear blanking)
- **Button 7**: Toggle freeze (pause/resume video)
- **Button 8**: Power off all projectors
- **Button 9**: Toggle debug mode

## Option 2: USB Macropad (Easier)

### Recommended Devices
- **Stream Deck** (expensive but professional)
- **Elgato Stream Deck Mini** (good value)
- **Generic USB macropad** (cheapest option)
- **Corsair K95 RGB** (keyboard with macro keys)

### Setup
1. Install the macropad software
2. Program the keys with the commands:
   - Key 1: `python3 projector_cli.py mute --action toggle`
   - Key 2: `python3 projector_cli.py power --action toggle`
   - Key 3: `python3 projector_cli.py power --action off`
   - Key 4: `python3 projector_cli.py status`
   - Key 5: `python3 projector_cli.py mute --action on`
   - Key 6: `python3 projector_cli.py mute --action off`
   - Key 7: `python3 projector_cli.py power --action on`
   - Key 8: `python3 projector_cli.py power --action off`

## Option 3: Web Interface (Most Flexible)

### Features
- Accessible from any device on network
- Real-time status updates
- Touch-friendly interface
- No hardware required

### Setup
```bash
# Install Flask
pip install flask

# Run web interface
python3 web_interface.py
```

## Installation Steps

### 1. Install Dependencies
```bash
# For Raspberry Pi GPIO
sudo apt-get update
sudo apt-get install python3-pip python3-dev
sudo pip3 install RPi.GPIO

# For USB HID support (optional)
sudo pip3 install hidapi
```

### 2. Test Hardware
```bash
# Test GPIO buttons
python3 test_gpio.py

# Test macropad
python3 macropad_control.py
```

### 3. Run the System
```bash
# Start macropad control
python3 macropad_control.py

# Or start debug monitor
python3 debug_monitor.py
```

## Troubleshooting

### Common Issues

1. **Buttons not responding**
   - Check wiring connections
   - Verify GPIO pin numbers
   - Test with `python3 test_gpio.py`

2. **LEDs not lighting**
   - Check resistor values (220Ω)
   - Verify LED polarity
   - Test individual LEDs

3. **Permission errors**
   - Run with `sudo` for GPIO access
   - Add user to `gpio` group

4. **Network issues**
   - Test with `python3 test_connection.py`
   - Check firewall settings
   - Verify projector IP addresses

### Testing Commands

```bash
# Test basic connectivity
python3 test_connection.py

# Test macropad
python3 macropad_control.py

# Test debugging
python3 debug_monitor.py

# Test CLI commands
python3 projector_cli.py status
```

## Customization

### Button Labels
Create custom labels for your buttons:
- Use label maker or printed labels
- Color-code by function (red for power, green for screen, etc.)
- Add icons or symbols

### LED Colors
Use different LED colors for different functions:
- **Green**: Success/ready
- **Yellow**: Warning/processing  
- **Red**: Error/emergency
- **Blue**: Status/info

### Enclosure
- 3D printed case
- Wooden box
- Plastic project box
- Professional rack-mount unit

## Safety Features

### Emergency Stop
- Button 3 provides emergency power off
- All projectors shut down immediately
- Visual and audio feedback

### Status Monitoring
- Continuous status checking
- Automatic error detection
- Logging of all operations

### Fail-Safe Operation
- Commands only execute when projectors are online
- Automatic retry on failures
- Graceful error handling

## Cost Breakdown

### Raspberry Pi Setup
- Raspberry Pi: $35-50
- Buttons and LEDs: $10-20
- Resistors and wires: $5-10
- Enclosure: $10-30
- **Total: $60-110**

### USB Macropad
- Generic macropad: $20-50
- Stream Deck: $150-300
- **Total: $20-300**

### Web Interface
- No additional hardware needed
- **Total: $0**

## Recommendations

1. **Start with Raspberry Pi** if you want to learn and customize
2. **Use USB macropad** if you want something ready-made
3. **Build web interface** if you need remote access
4. **Combine approaches** for best of all worlds

The Raspberry Pi approach gives you the most control and is perfect for a church environment where you might want to mount it permanently near your AV equipment.
