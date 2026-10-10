# Project Cleanup and Reorganization Plan

## Overview

This plan will clean up the project by removing unused files (4-button keypad, USB keypad alternatives), reorganizing the structure to separate CircuitPython firmware from Raspberry Pi control scripts, add a main entry point, and improve documentation.

## Architecture Understanding

- **Hardware**: Adafruit Macropad RP2040 (12-button) - settled on this
- **Firmware**: CircuitPython code (`code.py`, `boot.py`) that runs ON the macropad device
- **Control Software**: Python scripts that run ON the Raspberry Pi to read HID input and control projectors
- **Service**: systemd service runs `macropad/macropad_service_control.py` on boot

## Tasks

### 1. Remove Unused Files

Remove all files related to 4-button keypad and USB keypad alternatives since we've settled on the 12-button Adafruit Macropad RP2040:

**Files to delete:**

- `macropad/macropad_4button.py` - 4-button GPIO control (not used)
- `macropad/usb_keypad_control.py` - USB keypad alternative
- `macropad/usb_keypad_control_headless.py` - USB keypad headless
- `macropad/usb_keypad_control_macos.py` - USB keypad macOS
- `macropad/usb_keypad_control_specific.py` - USB keypad specific device
- `macropad/usb_keypad_auto_start.py` - USB keypad auto-start
- `macropad/usb_keypad_config.py` - USB keypad config
- `macropad/macropad_control.py` - GPIO-based macropad (not HID)
- `macropad/macropad_keyboard_listener.py` - Keyboard listener alternative
- `run_macropad_with_mocks.py` - Mock testing script (if not needed)
- `debug_hid.py` - Debug script (if not needed)

**Documentation to update/remove:**

- Remove references to 4-button and USB keypad from `docs/README.md`
- Remove or archive `docs/USB_KEYPAD_SETUP.md`
- Update `docs/HARDWARE_SETUP.md` to remove 4-button references
- Update `docs/MACROPAD_SETUP.md` to focus only on Adafruit Macropad RP2040

**Scripts to update/remove:**

- `scripts/fix_usb_keypad_pi.sh` - Remove if USB keypad not used
- `scripts/fix_usb_keypad_setup.sh` - Remove if USB keypad not used
- Update `scripts/create_macropad_service.sh` to remove USB keypad references

### 2. Reorganize Project Structure

**Create firmware directory:**

- Create `firmware/` directory at root
- Move `macropad/code.py` → `firmware/code.py`
- Move `macropad/boot.py` → `firmware/boot.py`
- Add `firmware/README.md` explaining these files go on the macropad device and how to install any necessary libraries onto the RP2040

**Reorganize macropad control scripts:**

- Keep `macropad/hid_macropad_control.py` - HID macropad control (used as fallback)
- Keep `macropad/macropad_service_control.py` - Service entry point (used by systemd)
- Add clear comments explaining which script does what

**Create proper Python package structure:**

- Consider if `macropad/` should become a proper package with `__init__.py`
- Keep current structure but add `__init__.py` if needed for imports

### 3. Add Main Entry Point

**Create `main.py` at root:**

- Simple launcher that runs macropad control by default
- Support `--service` flag to run service mode
- Support `--cli` flag to show CLI help
- Support `--help` to show all options
- Provide interactive menu if run without arguments

### 4. Improve Code Organization

**Standardize imports:**

- Ensure all scripts use consistent import patterns
- Add proper docstrings to all modules
- Add type hints where appropriate

**Clean up file structure:**

- Ensure all Python files have proper shebangs
- Ensure all Python files have `if __name__ == "__main__"` blocks
- Add module-level docstrings explaining purpose

### 5. Enhance Documentation

**Create comprehensive setup guide:**

- `docs/SETUP_GUIDE.md` - Complete setup from scratch (1-hour goal)
- Step-by-step instructions for:
  - Installing CircuitPython on macropad
  - Copying firmware files
  - Setting up Raspberry Pi
  - Installing dependencies
  - Configuring systemd service
  - Testing the system

**Update main README:**

- Clear architecture diagram
- Quick start section
- Link to detailed setup guide
- Remove references to unused hardware

**Improve inline documentation:**

- Add docstrings to all classes and functions
- Add comments explaining "why" not just "what"
- Document the HID communication protocol

### 6. Clean Up Configuration

**Review `config.py`:**

- Ensure all settings are well-documented
- Add comments explaining each configuration option
- Verify no unused configuration remains

### 7. Update Scripts

**Update systemd service script:**

- `scripts/create_macropad_service.sh` should reference correct paths
- Remove USB keypad references
- Update to use new structure if paths change

**Review and clean test files:**

- Keep useful tests
- Remove tests for unused hardware
- Update test documentation

## File Structure After Cleanup

```
sony-projector-control/
├── main.py                          # Main entry point
├── config.py                        # Configuration
├── requirements.txt                  # Dependencies
├── README.md                        # Main documentation
│
├── firmware/                        # CircuitPython code for macropad
│   ├── code.py                      # Main macropad firmware
│   ├── boot.py                      # Boot configuration
│   └── README.md                    # Firmware setup instructions
│
├── macropad/                        # Raspberry Pi control scripts
│   ├── __init__.py                  # Package marker
│   ├── hid_macropad_control.py      # HID macropad control (fallback)
│   └── macropad_service_control.py  # Service entry point (systemd)
│
├── projector_control.py             # Core projector control library
├── projector_cli.py                 # CLI interface
├── rear_projector_control.py        # Rear projector control
├── rear_projector_cli.py            # Rear projector CLI
│
├── scripts/                         # Setup and utility scripts
│   ├── create_macropad_service.sh   # Systemd service setup
│   └── setup_pi.sh                  # Pi setup script
│
├── docs/                            # Documentation
│   ├── SETUP_GUIDE.md               # Complete setup guide
│   ├── MACROPAD_SETUP.md            # Macropad-specific setup
│   ├── PI_SETUP_GUIDE.md            # Raspberry Pi setup
│   └── README.md                    # Project overview
│
├── tests/                           # Test files
├── examples/                        # Example usage
└── logs/                            # Log files (gitignored)
```

## Success Criteria

1. ✅ No unused files remain (4-button, USB keypad files removed)
2. ✅ Firmware files clearly separated from control scripts
3. ✅ `main.py` provides clear entry point
4. ✅ Documentation allows 1-hour setup from scratch
5. ✅ All code is well-commented and follows Python conventions
6. ✅ Project structure is intuitive and easy to navigate
7. ✅ Systemd service still works after reorganization