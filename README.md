# Sony Projector Control

This project uses an Adafruit Macropad RP2040 to control three Sony projectors through PJLink. The Macropad sends an 8-byte raw HID report to a Raspberry Pi. A single systemd service reads the reports and executes projector commands.

The production design has one supported input path:

- `macropad/boot.py`, `macropad/code.py`, and `macropad/hid_send.py` run on the Macropad.
- `macropad/macropad_service_control.py` is the Raspberry Pi service entry point.
- `macropad/hid_macropad_control.py` owns USB discovery, recovery, and button dispatch.
- `projector_control.py` owns PJLink networking.
- `scripts/install_pi.sh` installs, backs up, and rolls back the Pi service.

Unsupported historical GPIO, keyboard, and generic USB-keypad approaches are retained under `archive/legacy-inputs/` for reference only. They are not installed or tested.

## Button map

| Button | Action |
|---|---|
| 1 | All projectors on |
| 2 | All projectors off |
| 3 | Toggle all-projector power |
| 4 | Blank front projectors |
| 5 | Unblank front projectors |
| 6 | Toggle front blanking |
| 7 | Freeze front projectors |
| 8 | Unfreeze front projectors |
| 9 | Toggle front freeze |
| 10–12 | No action; safe for input testing. Their lights show Left, Right and Rear power status |

See [Installation](docs/INSTALL.md) and [Operations and recovery](docs/OPERATIONS.md).

## Safe local tests

```bash
python3 -m unittest discover -s tests/unit -p 'test_*.py' -v
```

Hardware-affecting diagnostics are isolated under `tools/manual/` and never run as part of the unit suite.
