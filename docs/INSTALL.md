# Installation

## Raspberry Pi host

The production Pi is reachable as `projector-control.local`. The installer preserves the existing `benvanzee` service account, creates a restricted `sony-projector` device group, backs up the current installation, removes the two obsolete crash-looping services, installs the strict udev rule, and starts `macropad-control.service`.

Before changing the host, back up the current Macropad firmware. If `CIRCUITPY` is mounted on the Pi, pass its mount path to the installer so the same transaction captures it:

```bash
sudo bash scripts/install_pi.sh install --firmware-mount /path/to/CIRCUITPY
```

If it is not mounted on the Pi, connect the Macropad to a Mac and copy `boot.py` and `code.py` off `CIRCUITPY` first. Reconnect it to the Pi without installing the new firmware yet.

Copy this checkout to a temporary directory on the Pi, then run the host-only form when the firmware was backed up separately:

```bash
sudo bash scripts/install_pi.sh install
```

The backup is stored under `/var/backups/sony-projector-control/`, with `latest` pointing to the most recent snapshot. The five most recent snapshots are kept. `/opt/projector-control/DEPLOYED_MANIFEST` records the source commit, dirty-state flag, and SHA-256 hashes of every production file.

Run the installer from a git checkout. If `git` cannot read the source tree, the manifest records `source_commit=unknown` and `source_dirty=unknown` rather than claiming a clean build. Under `sudo` against a checkout owned by another user you may need `git config --global --add safe.directory /path/to/checkout` first.

## What the installer replaces and what it keeps

`/opt/projector-control` is **replaced, not merged**, so no archived input implementation can survive an upgrade. Two things inside it are carried across the replacement:

- `.git`, so the tree stays a working checkout
- `config_local.py`, if you have site overrides there

Everything else under `/opt/projector-control` is deleted and rebuilt from the whitelist of production files. Anything you keep in that directory that is not on that list belongs in `PRESERVED_PATHS` in `scripts/install_pi.sh`, or it will be gone after the next install. It is recoverable from the backup tarball, but only if you know to look.

Before it touches anything, the installer scans `/etc/systemd/system` and warns about any unit or timer that references `/opt/projector-control` but is not one of the three it manages. Read those warnings; a scheduled job pointed at this tree can undo an install overnight.

Subsequent updates use the same command. Re-running `install` is the supported path, and it takes a fresh backup each time.

The installer removes these obsolete live units:

- `projector-control.service`
- `usb-keypad-control.service`

It also replaces the world-writable `99-hidraw-permissions.rules` rule with an exact VID/PID/serial rule that creates `/dev/sony-macropad` as group-writable only.

## Validate the host before firmware

Keep the existing Macropad firmware for the first host validation:

```bash
systemctl --no-pager --full status macropad-control.service
ls -l /dev/sony-macropad
journalctl -u macropad-control.service -n 50 --no-pager
```

Use reserved button 10 for the first input test. Do not test buttons 1–9 unless changing projector state is acceptable.

## Macropad firmware

Keep CircuitPython 10.0.3 for this rollout. After the host passes validation, plug the Macropad into a Mac and make one more firmware snapshot before copying:

```bash
mkdir -p /tmp/sony-macropad-firmware-backup
cp /Volumes/CIRCUITPY/boot.py /Volumes/CIRCUITPY/code.py \
  /tmp/sony-macropad-firmware-backup/

cp macropad/boot.py macropad/code.py macropad/hid_send.py \
  /Volumes/CIRCUITPY/
```

Reset the Macropad after `boot.py` is copied. The wire format remains compatible with both host versions: byte 0 is button 1–12 and bytes 1–7 are zero.

### Updating firmware from the Pi

The installer backs up the Macropad's firmware when given `--firmware-mount`, and copies the new firmware to `/opt/projector-control/firmware/`. It does not write to the Macropad. The Macropad's drive appears on the Pi as `/dev/sda1` (label `CIRCUITPY`), so the copy can be done over SSH without unplugging anything:

```bash
sudo mkdir -p /mnt/circuitpy
sudo mount -o uid=$(id -u),gid=$(id -g),flush /dev/sda1 /mnt/circuitpy
cp macropad/hid_send.py macropad/code.py /mnt/circuitpy/
sync
sudo umount /mnt/circuitpy
```

The Macropad reloads `code.py` by itself when the files change. `boot.py` changes need a full reset.

If `mount` warns `source write-protected, mounted read-only`, the Macropad started before the Pi finished enumerating it, which makes CircuitPython keep the drive for itself. `cat /sys/block/sda/ro` prints `1` in that state. Unmount, then reset the Macropad while the Pi is running. This sends the reset through its serial console:

```bash
sudo python3 -c "
import os, time
fd = os.open('/dev/ttyACM0', os.O_RDWR | os.O_NOCTTY)
os.write(fd, b'\x03'); time.sleep(1.5)
os.write(fd, b'\r\n'); time.sleep(1.5)
os.write(fd, b'import microcontroller; microcontroller.reset()\r\n')
"
```

The service logs one disconnect and reconnects within about five seconds. `sudo dmesg | grep 'Write Protect' | tail -1` should then say `off`.

The same console shows what the firmware prints, including `Status lights disabled: ...` if the key lights failed to start:

```bash
sudo timeout 5 cat /dev/ttyACM0
```

## Rollback

From the same copied checkout used for installation:

```bash
sudo bash scripts/install_pi.sh rollback
```

If installation used `--firmware-mount`, use the same option and mount path during rollback. Rollback restores `/opt/projector-control`, all three prior service definitions, both managed udev-rule locations, and the mounted firmware snapshot from the latest backup.
