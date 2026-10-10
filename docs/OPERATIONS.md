# Operations and Recovery

## Projectors

All three projectors are controlled over PJLink on TCP port 4352. Addresses come from `config.py`, with site overrides in `config_local.py`.

| Name | Address | Macropad controls |
|---|---|---|
| Left | `10.10.10.2` | Power, blank, freeze |
| Right | `10.10.10.3` | Power, blank, freeze |
| Rear | `10.10.10.4` | Power only |

The rear projector is a Sony VPL-PHZ51, installed October 2026. Power, blank and freeze were all tested on it over PJLink on 2026-10-10, so the rear can be added to the blank and freeze buttons later without protocol work. A replacement projector needs the same static address, PJLink enabled, and PJLink authentication off. The service refuses to connect to a projector that asks for a PJLink password.

The PHZ51 accepts one PJLink connection at a time. A second connection opened while the first is still held timed out after 3 seconds (tested 2026-10-10). Anything that talks to a projector must close its connection promptly, and two programs must not hold connections to the same projector at once.

## Normal health checks

```bash
systemctl --no-pager --full status macropad-control.service
journalctl -u macropad-control.service -n 100 --no-pager
cat /opt/projector-control/DEPLOYED_MANIFEST
```

Healthy behavior:

- The service remains active when the Macropad is absent.
- CPU usage stays low while disconnected.
- `/dev/sony-macropad` appears when the exact configured device is connected.
- Disconnect and reconnect produce one state transition each, not an `EIO` flood.
- The service can reconnect without changing PID or rebooting the Pi.

## USB inspection

```bash
ls -l /dev/sony-macropad /dev/hidraw* 2>&1
cat /sys/class/hidraw/$(basename "$(readlink -f /dev/sony-macropad)")/device/uevent
```

The expected identity is:

- Vendor: `239a`
- Product: `8108`
- Serial: `DF641C0547692E2E`

## Recovery

If the Macropad is present but controls do not respond, inspect logs first. Restarting only the service is the preferred recovery:

```bash
sudo systemctl restart macropad-control.service
```

A Pi power cycle should not be required for an HID disconnect. If a service restart is needed, capture the preceding journal first, because that is where the service logs:

```bash
journalctl -u macropad-control.service --since "1 hour ago" --no-pager > ~/macropad-incident.log
```

## Hardware acceptance checklist

1. Boot with the Macropad disconnected. Confirm the service remains active and quiet.
2. Connect the Macropad. Confirm `/dev/sony-macropad` appears.
3. Follow the service journal and press reserved button 10. Confirm the service reports `BUTTON 10 PRESSED` without changing a projector.
4. Unplug and reconnect the Macropad. Confirm the service logs a disconnect and reconnect without an error flood.
5. Repeat the disconnect/reconnect cycle at least 25 times.
6. Leave the complete system idle for 24 hours, then retest reserved button 10.
7. During an approved projector test window, make one projector unreachable and confirm a newer pending button replaces an older waiting action.

## Manual diagnostics

Programs under `tools/manual/` may contact or change real projectors. Run them only during an approved test window. The safe automated suite is:

```bash
python3 -m unittest discover -s tests/unit -p 'test_*.py' -v
```
