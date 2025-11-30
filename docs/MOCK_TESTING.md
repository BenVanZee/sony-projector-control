# Mock Testing Guide

This guide explains how to use mock projectors for testing macropad and projector control scripts without real hardware.

## Quick Start

### Run Macropad with Mock Projectors

The easiest way to test your macropad with mock projectors:

```bash
# Run USB keypad control with mocks
python run_macropad_with_mocks.py usb-keypad

# Run macropad control with mocks (4-button layout)
python run_macropad_with_mocks.py macropad --layout 4

# Run HID macropad control with mocks
python run_macropad_with_mocks.py hid-macropad
```

### Customize Initial Projector States

```bash
# Start with projectors OFF
python run_macropad_with_mocks.py macropad --power OFF

# Start with projectors ON, MUTED, and FROZEN
python run_macropad_with_mocks.py macropad --power ON --mute MUTED --freeze FROZEN

# Use 3 mock projectors instead of 2
python run_macropad_with_mocks.py macropad --num-projectors 3
```

## How It Works

When you run `run_macropad_with_mocks.py`:

1. **Mock servers start** - Creates TCP servers that simulate PJLink projectors
2. **Macropad connects** - Your macropad scripts connect to these mock servers instead of real projectors
3. **Commands work** - All projector commands (power, mute, freeze) work normally
4. **Responses are mocked** - The mock servers respond with realistic PJLink responses

## What Gets Tested

✅ **All macropad buttons work** - Power on/off, mute, freeze, etc.  
✅ **Status queries work** - Getting power, mute, freeze status  
✅ **State changes work** - Commands actually change the mock projector state  
✅ **Multiple projectors** - Test with 2, 3, or more mock projectors  
✅ **Error handling** - Test how your scripts handle various states  

## Example Session

```bash
$ python run_macropad_with_mocks.py macropad --power ON

🎭 Starting Macropad Control with MOCK PROJECTORS
============================================================
✅ Created 2 mock projectors:
   Projector 1: 127.0.0.1:54321 (Power: ON)
   Projector 2: 127.0.0.1:54322 (Power: ON)

🎹 4-Button Macropad Control Ready!
   Press buttons on your macropad to test
   (All commands will go to mock projectors)
   Press ESC to exit

🎯 BUTTON 1 ACTIVATED!
   Function: Power ON all projectors
   ✅ All projectors turned ON successfully

🎯 BUTTON 3 ACTIVATED!
   Function: Toggle screen blank
   ✅ All screens muted successfully
```

## Advanced Usage

### Programmatic Usage

You can also use the mock system programmatically:

```python
from tests.mock_macropad_integration import MockMacropadEnvironment
from macropad.usb_keypad_control import USBKeypadController

# Create mock environment
mock_env = MockMacropadEnvironment(num_projectors=2, power="ON")
projectors = mock_env.start()

try:
    # Create controller with mock projectors
    controller = USBKeypadController(
        projectors=[{'ip': ip, 'port': port} for ip, port in projectors],
        keypad_type="cut_copy_paste"
    )
    
    # Run your tests
    controller.run()
    
finally:
    mock_env.stop()
```

### Testing Specific Scenarios

```python
from tests.mock_macropad_integration import create_mock_projector_manager

# Create manager with specific states
manager, mock_env = create_mock_projector_manager(
    num_projectors=2,
    power="OFF",
    mute="MUTED"
)

try:
    # Test power on
    results = manager.power_all(True)
    assert all(results.values()), "All should power on"
    
    # Verify state changed
    status = manager.get_all_status()
    assert status["127.0.0.1"]["power"] == "ON"
    
finally:
    mock_env.stop()
```

## Command Line Options

```
usage: run_macropad_with_mocks.py [-h] [--keypad-type KEYPAD_TYPE]
                                   [--layout {4,9}] [--power {ON,OFF,COOLING,WARMING}]
                                   [--mute {MUTED,UNMUTED}]
                                   [--freeze {FROZEN,NORMAL}]
                                   [--num-projectors NUM_PROJECTORS]
                                   {usb-keypad,macropad,hid-macropad}

positional arguments:
  {usb-keypad,macropad,hid-macropad}
                        Which macropad script to run

optional arguments:
  -h, --help            show this help message and exit
  --keypad-type KEYPAD_TYPE
                        USB keypad type (for usb-keypad script)
  --layout {4,9}        Button layout (for macropad script)
  --power {ON,OFF,COOLING,WARMING}
                        Initial power state
  --mute {MUTED,UNMUTED}
                        Initial mute state
  --freeze {FROZEN,NORMAL}
                        Initial freeze state
  --num-projectors NUM_PROJECTORS
                        Number of mock projectors to create
```

## Troubleshooting

### "Connection refused" errors
- The mock servers need a moment to start. The script includes a small delay, but if you see this, try adding a longer sleep.

### "No response" from projectors
- Make sure the mock servers are running. Check the console output for "Created X mock projectors".

### Buttons not working
- Verify your macropad is connected and recognized by the system
- Check that the correct script type is selected (usb-keypad vs macropad vs hid-macropad)

### Escape sequences appearing in terminal (^[OP, ^[OQ, etc.)
- This happens when your device acts as a keyboard and sends function key codes
- The device `05ac:8104` (Apple) is likely a keyboard/trackpad, not a raw HID macropad
- **Solution**: Use the keyboard listener approach instead:
  ```bash
  python run_macropad_with_mocks.py usb-keypad
  ```
- The `usb-keypad` script uses `pynput` which properly handles keyboard events
- The `hid-macropad` script is for raw HID devices that don't act as keyboards

## Benefits

🎯 **No hardware needed** - Test without real projectors  
⚡ **Fast iteration** - No network delays or hardware setup  
🔄 **Reproducible** - Same initial states every time  
🛡️ **Safe** - No risk of accidentally controlling real projectors  
🧪 **Comprehensive** - Test all states and scenarios  

## See Also

- `tests/README_MOCKING.md` - Detailed mocking API documentation
- `tests/test_with_mocks.py` - Example test suite
- `tests/mock_projector_server.py` - Mock server implementation

