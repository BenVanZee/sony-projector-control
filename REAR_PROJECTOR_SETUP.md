# Rear Projector Setup Guide

## Overview

Your Sony projector control system now supports independent control of your rear projector (10.10.10.4) while maintaining full control of your front projectors (10.10.10.2 and 10.10.10.3).

## What's New

✅ **Independent rear projector control** - Control rear projector separately from front projectors  
✅ **Group-based control** - Control front, rear, or all projectors as groups  
✅ **All existing functionality preserved** - Your current setup continues to work exactly as before  

## Quick Start

### 1. Test Connection
```bash
python3 test_rear_connection.py
```

### 2. Interactive Control
```bash
python3 rear_projector_control.py
```

### 3. Command Line Control
```bash
# Check status
python3 rear_projector_cli.py status

# Turn on/off
python3 rear_projector_cli.py power --action on
python3 rear_projector_cli.py power --action off

# Mute/unmute (blank screen)
python3 rear_projector_cli.py mute --action on
python3 rear_projector_cli.py mute --action off

# Freeze/unfreeze video
python3 rear_projector_cli.py freeze --action on
python3 rear_projector_cli.py freeze --action off
```

## Group Control

### Front Projectors Only (Left + Right)
```bash
python3 projector_cli.py power --action on --group front
python3 projector_cli.py mute --action off --group front
```

### Rear Projector Only
```bash
python3 projector_cli.py power --action on --group rear
python3 projector_cli.py mute --action off --group rear
```

### All Projectors
```bash
python3 projector_cli.py power --action on --group all
python3 projector_cli.py mute --action off --group all
```

## Configuration

The system automatically uses your rear projector configuration:
- **IP**: 10.10.10.4
- **Port**: 4352 (PJLink default)
- **Nickname**: `rear`
- **Shorthand**: `b` (for back/rear)

## Files Created

- `rear_projector_control.py` - Interactive control for rear projector
- `rear_projector_cli.py` - Command-line interface for rear projector
- `test_rear_connection.py` - Test rear projector connectivity
- `rear_projector_examples.py` - Examples and demonstrations

## Enhanced Main CLI

The main `projector_cli.py` now supports group-based control:
- `--group front` - Control front projectors (left + right)
- `--group rear` - Control rear projector only
- `--group all` - Control all projectors

## Examples

### Morning Setup
```bash
# Turn on front projectors for main content
python3 group_projector_control.py power --action on --group front

# Turn on rear projector for additional content
python3 group_projector_control.py power --action on --group rear
```

### During Event
```bash
# Blank front screens for presentation
python3 group_projector_control.py mute --action on --group front

# Keep rear projector active for background content
python3 group_projector_control.py mute --action off --group rear
```

### Evening Shutdown
```bash
# Turn off all projectors
python3 group_projector_control.py power --action off --group all
```

## Troubleshooting

### Connection Issues
1. Verify network connectivity: `ping 10.10.10.4`
2. Check PJLink port: `telnet 10.10.10.4 4352`
3. Run connection test: `python3 test_rear_connection.py`

### Command Issues
1. Check projector power status
2. Verify PJLink is enabled on the projector
3. Check network firewall settings

## Support

- All existing scripts continue to work
- New functionality is additive, not replacing
- Test in your environment before production use
- Check logs in `rear_projector_control.log` for detailed information

---

**Ready to use!** Your rear projector is now fully integrated into the control system while maintaining independent operation.
