# Sony VPL-PHZ61 Projector Control System

A robust Python application for controlling multiple Sony VPL-PHZ61 projectors via PJLink protocol. This system can turn projectors on/off and blank/unblank screens, making it perfect for venues that need to manage multiple projectors simultaneously.

**NEW: Now supports independent control of front and rear projectors!**

## Features

- **Multi-projector support**: Control 2+ projectors simultaneously
- **Independent group control**: Control front, rear, or all projectors separately
- **PJLink protocol**: Industry-standard protocol for reliable communication
- **Power management**: Turn projectors on/off remotely
- **Screen blanking**: Mute/unmute video for seamless content switching
- **Status monitoring**: Real-time status of all projectors
- **Error handling**: Robust connection management with automatic reconnection
- **Logging**: Comprehensive logging for troubleshooting
- **CLI interface**: Easy command-line control for automation
- **Raspberry Pi ready**: Lightweight and efficient for embedded systems

## Why PJLink?

After testing multiple protocols, **PJLink** is the best choice for Sony VPL-PHZ61 projectors because:

- ✅ **Industry standard** - Widely supported and documented
- ✅ **Sony compatibility** - Excellent support in Sony projectors
- ✅ **Reliability** - More stable than proprietary protocols
- ✅ **Community support** - Better troubleshooting resources
- ✅ **Future-proof** - Standard that will continue to be supported

## Installation

1. **Clone or download** the project files
2. **Ensure Python 3.6+** is installed
3. **No external dependencies** required - uses only Python standard library

```bash
# Check Python version
python3 --version

# Make scripts executable (Linux/Mac)
chmod +x projector_control.py projector_cli.py
```

## Configuration

Edit `config.py` to configure your projectors with friendly nicknames:

```python
PROJECTORS = [
    {
        'ip': '10.10.10.2',      # Your first projector IP
        'port': 4352,            # PJLink port (usually 4352)
        'name': 'Left',           # Friendly name
        'nickname': 'left',       # Short nickname for CLI
        'location': 'Main Hall - Left Side',  # Location description
        'group': 'front'          # Group assignment
    },
    {
        'ip': '10.10.10.3',      # Your second projector IP
        'port': 4352,
        'name': 'Right',          # Friendly name
        'nickname': 'right',      # Short nickname for CLI
        'location': 'Main Hall - Right Side',
        'group': 'front'          # Group assignment
    },
    {
        'ip': '10.10.10.4',      # Your rear projector IP
        'port': 4352,
        'name': 'Rear',           # Friendly name
        'nickname': 'rear',       # Short nickname for CLI
        'location': 'Main Hall - Rear',
        'group': 'rear'           # Group assignment
    }
]

# Nickname aliases for easy reference
PROJECTOR_ALIASES = {
    'left': '10.10.10.2',
    'right': '10.10.10.3',
    'rear': '10.10.10.4',
    'l': '10.10.10.2',           # Shorthand
    'r': '10.10.10.3',           # Shorthand
    'b': '10.10.10.4'            # Shorthand for back/rear
}

# Group-based aliases for controlling multiple projectors
PROJECTOR_GROUPS = {
    'front': ['left', 'right'],      # Front projectors (left and right)
    'rear': ['rear'],                # Rear projector only
    'all': ['left', 'right', 'rear'] # All projectors
}
```

**Benefits of nicknames:**
- **Easy to remember**: Use `left` instead of `10.10.10.2`
- **Location-based**: `left`, `right`, `front`, `rear`
- **Shorthand**: `l`, `r`, `f`, `b` for quick commands
- **Flexible**: Add as many aliases as you need

**Group-based control:**
- **Front projectors**: Control left and right projectors together
- **Rear projector**: Control rear projector independently
- **All projectors**: Control all three projectors simultaneously

## Usage

### Quick Start

1. **Test your connection first:**
   ```bash
   python3 test_connection.py
   ```

2. **Run the interactive control system:**
   ```bash
   python3 projector_control.py
   ```

**Note:** This setup works with any user account, not just the default "pi" user. The setup script automatically detects the current user and configures everything accordingly.

3. **Use command-line interface with nicknames:**
   ```bash
   # Check status of all projectors
   python3 projector_cli.py status
   
   # Control specific projectors by nickname
python3 projector_cli.py power --action on --projectors left right
python3 projector_cli.py mute --action on --projectors left
python3 projector_cli.py mute --action off --projectors right
python3 projector_cli.py free --projectors left right
python3 projector_cli.py freeze --action on --projectors left right

# Use shorthand nicknames
python3 projector_cli.py power --action off --projectors l r
   ```

### Interactive Mode

Run the main application for an interactive menu:

```bash
python3 projector_control.py
```

This provides a menu-driven interface:
- View status of all projectors
- Turn all projectors on/off
- Mute/unmute all projectors (blank screen)
- Real-time status updates

### Command Line Interface

For automation and scripting, use the CLI version:

#### Standard CLI (All Projectors)

```bash
# Check status of all projectors
python3 projector_cli.py status

# Turn all projectors ON
python3 projector_cli.py power --action on

# Turn all projectors OFF  
python3 projector_cli.py power --action off

# Blank all screens (mute video)
python3 projector_cli.py mute --action on

# Unblank all screens
python3 projector_cli.py mute --action off

# Free all screens (clear any blanking)
python3 projector_cli.py free

# Freeze all screens (pause video)
python3 projector_cli.py freeze --action on

# Unfreeze all screens (resume video)
python3 projector_cli.py freeze --action off

# Toggle freeze state
python3 projector_cli.py freeze --action toggle

**✅ Note:** Freeze now uses the correct PJLink FREZ command (`%2FREZ 1`/`%2FREZ 0`) 
which properly pauses video without causing a black screen.

# Toggle power state
python3 projector_cli.py power --action toggle

# Toggle mute state
python3 projector_cli.py mute --action toggle

# Control specific projectors by nickname
python3 projector_cli.py status --projectors left right
python3 projector_cli.py power --action on --projectors left
python3 projector_cli.py mute --action off --projectors right

# Use shorthand nicknames
python3 projector_cli.py power --action toggle --projectors l r
```

#### Group-based Control

Control projectors by group (front, rear, or all):

```bash
# Front projectors only (left + right)
python3 projector_cli.py power --action on --group front
python3 projector_cli.py mute --action off --group front
python3 projector_cli.py freeze --action on --group front

# Rear projector only
python3 projector_cli.py power --action on --group rear
python3 projector_cli.py mute --action off --group rear
python3 projector_cli.py freeze --action on --group rear

# All projectors
python3 projector_cli.py power --action on --group all
python3 projector_cli.py mute --action off --group all
python3 projector_cli.py freeze --action on --group all
```

#### Rear Projector Only

Control just the rear projector independently:

```bash
# Check rear projector status
python3 rear_projector_cli.py status

# Power control
python3 rear_projector_cli.py power --action on
python3 rear_projector_cli.py power --action off
python3 rear_projector_cli.py power --action toggle

# Screen control
python3 rear_projector_cli.py mute --action on
python3 rear_projector_cli.py mute --action off
python3 rear_projector_cli.py freeze --action on
python3 rear_projector_cli.py freeze --action off
```

# Control projectors by group
python3 projector_cli.py power --action on --group front    # Front projectors only
python3 projector_cli.py power --action on --group rear     # Rear projector only
python3 projector_cli.py power --action on --group all      # All projectors

# Control rear projector independently
python3 rear_projector_cli.py power --action on
python3 rear_projector_cli.py mute --action off
python3 rear_projector_cli.py freeze --action toggle
```

### Common Use Cases

#### 1. Daily Operations
```bash
# Morning: Turn on all projectors
python3 projector_cli.py power --action on

# During breaks: Blank screens
python3 projector_cli.py mute --action on

# Resume: Unblank screens  
python3 projector_cli.py mute --action off

# Evening: Turn off all projectors
python3 projector_cli.py power --action off
```

#### 2. Automation Scripts
```bash
#!/bin/bash
# Example automation script

# Turn on projectors 30 minutes before event
python3 projector_cli.py power --action on

# Wait for warm-up
sleep 300

# Unblank screens
python3 projector_cli.py mute --action off
```

#### 3. Status Monitoring
```bash
# Check status every 5 minutes
while true; do
    python3 projector_cli.py status
    sleep 300
done
```

## Network Requirements

- **Port 4352** must be open on projectors (PJLink default)
- **Network connectivity** between control system and projectors
- **Static IP addresses** recommended for projectors
- **Firewall rules** may need adjustment

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify projector IP addresses
   - Check network connectivity (`ping 10.10.10.2`)
   - Ensure port 4352 is open
   - Check firewall settings

2. **Commands Not Working**
   - Verify projector is powered on
   - Check PJLink is enabled in projector settings
   - Try reconnecting with `python3 projector_cli.py status`

3. **Partial Control**
   - Some projectors may have PJLink disabled
   - Check projector network settings
   - Verify PJLink authentication if enabled

### Debug Mode

Enable detailed logging by editing `projector_control.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    # ... rest of config
)
```

### Network Testing

Test basic connectivity:

```bash
# Test network connectivity
telnet 10.10.10.2 4352

# Test with netcat (if available)
nc -zv 10.10.10.2 4352
```

### Testing Rear Projector

Test the rear projector connection specifically:

```bash
# Test rear projector connection and PJLink functionality
python3 test_rear_connection.py

# Test basic rear projector control
python3 rear_projector_cli.py status
```

## Raspberry Pi Deployment

This system is designed to run efficiently on Raspberry Pi:

1. **Install Python 3** (usually pre-installed on Raspberry Pi OS)
2. **Copy files** to your Pi
3. **Set up network** with static IPs
4. **Test connectivity** to projectors
5. **Run as service** for automatic startup

### Service Setup (Optional)

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/projector-control.service
```

```ini
[Unit]
Description=Sony Projector Control System
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/projector-control
Environment=PATH=/opt/projector-control/venv/bin
ExecStart=/opt/projector-control/venv/bin/python3 projector_control.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note:** Replace `YOUR_USERNAME` with your actual username. The setup script automatically detects the current user and creates the service file with the correct username.

Enable and start the service:

```bash
sudo systemctl enable projector-control
sudo systemctl start projector-control
```

## Advanced Features

### Macropad Control

Control projectors with physical buttons using `macropad_control.py`:

```bash
# Start 9-button macropad control system
python3 macropad_control.py

# Start 4-button macropad control system (essential functions only)
python3 macropad_4button.py

# Or use the flexible layout option
python3 macropad_control.py --layout 4  # 4 buttons
python3 macropad_control.py --layout 9  # 9 buttons (default)
```

**4-Button Layout (Essential Functions):**
- **Button 1**: Power ON all projectors
- **Button 2**: Power OFF all projectors
- **Button 3**: Toggle screen blank/unblank
- **Button 4**: Toggle freeze (pause/resume video)

**9-Button Layout (Full Features):**
- **Button 1**: Toggle screen blank/unblank
- **Button 2**: Toggle projector power
- **Button 3**: Power ON all projectors
- **Button 4**: Status check
- **Button 5**: Force blank screen
- **Button 6**: Free screen (clear blanking)
- **Button 7**: Toggle freeze (pause/resume video)
- **Button 8**: Power OFF all projectors
- **Button 9**: Toggle debug mode

**Hardware Options:**
- **Raspberry Pi + GPIO buttons** (recommended)
- **USB HID macropad** (easier setup)
- **Web interface** (most flexible)

See `hardware_setup_guide.md` for detailed hardware instructions.

### Debug Monitor

Advanced debugging and monitoring with `debug_monitor.py`:

```bash
# Start interactive debug mode
python3 debug_monitor.py
```

**Features:**
- Real-time status monitoring
- Command history tracking
- Raw network testing
- PJLink command testing
- Export debug data to JSON

### GPIO Testing

Test your Raspberry Pi hardware setup:

```bash
# Test buttons and LEDs
python3 test_gpio.py
```

### Example Usage

See nickname functionality in action:

```bash
# Run examples with nicknames
python3 example_usage.py
```

## File Structure

```
projector-control/
├── projector_control.py      # Main application
├── projector_cli.py          # Command-line interface

├── rear_projector_control.py # Interactive rear projector control
├── rear_projector_cli.py     # CLI for rear projector only
├── macropad_control.py       # 9-button physical button control
├── macropad_4button.py      # 4-button essential functions control
├── debug_monitor.py          # Advanced debugging
├── test_gpio.py             # Hardware testing
├── test_connection.py        # Network testing
├── test_rear_connection.py   # Test rear projector connection
├── test_freeze.py           # Freeze functionality testing
├── example_usage.py         # Nickname examples
├── config.py                # Configuration file
├── hardware_setup_guide.md  # Hardware setup guide
├── requirements.txt          # Dependencies (none required)
├── REAR_PROJECTOR_SETUP.md  # Rear projector setup guide
├── README.md                # This file
└── projector_control.log    # Log file (created automatically)
```

## Protocol Details

The system uses PJLink protocol commands:

- `%1POWR 1` - Power ON
- `%1POWR 0` - Power OFF  
- `%1POWR ?` - Power status query
- `%1AVMT 31` - Mute video/audio
- `%1AVMT 30` - Unmute video/audio
- `%1AVMT ?` - Mute status query
- `%2FREZ 1` - Freeze video (pause)
- `%2FREZ 0` - Unfreeze video (resume)
- `%2FREZ ?` - Freeze status query

## Contributing

This system is designed to be easily extensible:

- Add new commands in `ProjectorController` class
- Modify configuration in `config.py`
- Extend CLI options in `projector_cli.py`

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs in `projector_control.log`
3. Test network connectivity to projectors
4. Verify PJLink is enabled on projectors

## New: Independent Rear Projector Control

The system now supports independent control of your rear projector (10.10.10.4) while maintaining full control of your front projectors. This allows you to:

- **Control front projectors together**: Left and right projectors can be controlled as a group
- **Control rear projector independently**: Rear projector can be operated separately from front projectors
- **Control all projectors together**: All three projectors can be controlled simultaneously when needed

### Quick Start for Rear Projector

1. **Test connection:**
   ```bash
   python3 test_rear_connection.py
   ```

2. **Interactive control:**
   ```bash
   python3 rear_projector_control.py
   ```

3. **Command-line control:**
   ```bash
   python3 rear_projector_cli.py power --action on
   python3 rear_projector_cli.py mute --action off
   ```

4. **Group-based control:**
   ```bash
   python3 group_projector_control.py power --action on --group rear
   python3 group_projector_control.py power --action on --group front
   python3 group_projector_control.py power --action on --group all
   ```

---

**Note**: This system has been tested with Sony VPL-PHZ61 projectors but should work with any PJLink-compatible projector. Always test in your environment before production use.
