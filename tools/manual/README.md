# Manual Hardware Diagnostics

These programs were moved out of `tests/` because some can contact or change real projectors, GPIO devices, or USB hardware.

They are not part of the automated unit suite. Read each program before running it, use an approved projector test window, and prefer reserved Macropad buttons 10–12 for input-only checks.

Everything here is named `check_*.py` or `debug_*.py` rather than `test_*.py` so that no test collector can pick it up. `check_freeze.py` and `check_rear_connection.py` in particular send real PJLink commands the moment they run. Keep that naming for anything added to this directory; the repo-root `conftest.py` backs it up.
