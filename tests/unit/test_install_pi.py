import subprocess
import tempfile
import unittest
from pathlib import Path


class PiInstallerTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[2]

    def run_installer(self, action, root, firmware_mount=None):
        command = [
            "bash",
            str(self.repo / "scripts" / "install_pi.sh"),
            action,
            "--root",
            str(root),
        ]
        if firmware_mount is not None:
            command.extend(["--firmware-mount", str(firmware_mount)])
        return subprocess.run(
            command,
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_live_install_stops_current_service_before_replacing_tree(self):
        """The new files must never be installed beneath the old running process."""
        script = (self.repo / "scripts" / "install_pi.sh").read_text()
        install_body = script.split("install_files() {", 1)[1].split(
            "restore_file() {", 1
        )[0]

        stop = install_body.index("systemctl stop macropad-control.service")
        replace = install_body.index("safe_remove_deployment")
        self.assertLess(stop, replace)

    def test_preserved_config_local_actually_overrides_config(self):
        """Preserving the file is pointless unless config.py still loads it."""
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            (sandbox / "config.py").write_text(
                (self.repo / "config.py").read_text()
            )
            (sandbox / "config_local.py").write_text(
                "PROJECTORS = [{'ip': '192.168.1.50', 'port': 4352}]\n"
            )

            result = subprocess.run(
                [
                    "python3",
                    "-c",
                    "import config; print(config.PROJECTORS[0]['ip'], len(config.PROJECTORS))",
                ],
                cwd=sandbox,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("192.168.1.50 1", result.stdout.strip())

    def test_backup_failure_aborts_before_the_tree_is_wiped(self):
        """create_backup must not run in a subshell that swallows errexit."""
        script = (self.repo / "scripts" / "install_pi.sh").read_text()

        self.assertNotIn("$(create_backup)", script)
        install_body = script.split("install_files() {", 1)[1].split(
            "restore_file() {", 1
        )[0]
        self.assertLess(
            install_body.index("create_backup"),
            install_body.index("safe_remove_deployment"),
        )

    def test_root_sandbox_rejects_a_path_that_resolves_to_the_live_tree(self):
        """A symlinked component must not redirect the sandboxed rm -rf."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            (real / "opt").mkdir(parents=True)
            elsewhere = root / "elsewhere" / "projector-control"
            elsewhere.mkdir(parents=True)
            (elsewhere / "precious.txt").write_text("must survive\n")
            (real / "opt" / "projector-control").symlink_to(elsewhere)

            result = self.run_installer("install", real)

            self.assertEqual(1, result.returncode, result.stdout)
            self.assertIn("Refusing removal", result.stderr)
            self.assertTrue((elsewhere / "precious.txt").exists())

    def test_root_must_exist_and_cannot_be_the_filesystem_root(self):
        """--root / would wipe the live deployment while skipping systemd."""
        missing = self.run_installer("install", Path("/nonexistent-sandbox-xyz"))
        self.assertEqual(2, missing.returncode)
        self.assertIn("--root does not exist", missing.stderr)

        filesystem_root = self.run_installer("install", Path("/"))
        self.assertEqual(2, filesystem_root.returncode)
        self.assertIn("targets the live system", filesystem_root.stderr)

    def test_installer_refuses_a_firmware_mount_that_is_not_circuitpy(self):
        """Rollback rewrites three fixed filenames there; a typo must not qualify."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            not_circuitpy = root / "some" / "other" / "directory"
            not_circuitpy.mkdir(parents=True)

            result = self.run_installer("install", root, not_circuitpy)

            self.assertEqual(2, result.returncode)
            self.assertIn("boot_out.txt", result.stderr)

    def test_install_warns_about_unmanaged_units_touching_the_tree(self):
        """A scheduled job pointed at this tree can undo an install overnight."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            units = root / "etc" / "systemd" / "system"
            units.mkdir(parents=True)
            (units / "projector-auto-update.timer").write_text(
                "[Service]\nExecStart=/opt/projector-control/scripts/auto_update.sh\n"
            )

            result = self.run_installer("install", root)

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("projector-auto-update.timer", result.stderr)
            self.assertIn("not managed by this installer", result.stderr)

    def test_install_backs_up_replaces_and_rolls_back_production_files(self):
        """One installer run is traceable and can restore the prior Pi state."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deployed = root / "opt" / "projector-control"
            units = root / "etc" / "systemd" / "system"
            rules = root / "etc" / "udev" / "rules.d"
            firmware = root / "mnt" / "CIRCUITPY"
            deployed.mkdir(parents=True)
            units.mkdir(parents=True)
            rules.mkdir(parents=True)
            firmware.mkdir(parents=True)

            (deployed / "config.py").write_text("old config\n")
            (deployed / "legacy_live_service.py").write_text("old legacy code\n")
            (deployed / ".git").mkdir()
            (deployed / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
            (deployed / "config_local.py").write_text("PROJECTORS = []\n")
            for name in (
                "macropad-control.service",
                "projector-control.service",
                "usb-keypad-control.service",
            ):
                (units / name).write_text("old " + name + "\n")
            broad_rule = rules / "99-hidraw-permissions.rules"
            broad_rule.write_text('SUBSYSTEM=="hidraw", MODE="0666"\n')
            (firmware / "boot_out.txt").write_text("Adafruit CircuitPython 10.0.3\n")
            (firmware / "boot.py").write_text("old boot\n")
            (firmware / "code.py").write_text("old firmware\n")

            installed = self.run_installer("install", root, firmware)
            self.assertEqual(0, installed.returncode, installed.stderr)
            self.assertEqual(
                (self.repo / "config.py").read_text(),
                (deployed / "config.py").read_text(),
            )
            self.assertTrue((deployed / "DEPLOYED_MANIFEST").is_file())
            manifest = (deployed / "DEPLOYED_MANIFEST").read_text()
            self.assertIn("systemd/macropad-control.service", manifest)
            self.assertIn("udev/99-sony-macropad.rules", manifest)
            self.assertTrue((deployed / "macropad" / "systemd_notify.py").is_file())
            self.assertFalse((deployed / "legacy_live_service.py").exists())
            self.assertEqual(
                "ref: refs/heads/main\n",
                (deployed / ".git" / "HEAD").read_text(),
            )
            self.assertEqual(
                "PROJECTORS = []\n", (deployed / "config_local.py").read_text()
            )
            self.assertFalse((units / "projector-control.service").exists())
            self.assertFalse((units / "usb-keypad-control.service").exists())
            self.assertFalse(broad_rule.exists())
            self.assertTrue((units / "macropad-control.service").is_file())
            self.assertTrue((rules / "99-sony-macropad.rules").is_file())

            backups = [
                path
                for path in (root / "var" / "backups" / "sony-projector-control").iterdir()
                if path.name != "latest"
            ]
            self.assertEqual(1, len(backups))

            (deployed / "config.py").write_text("broken deployment\n")
            (firmware / "boot.py").write_text("new boot\n")
            (firmware / "code.py").write_text("new firmware\n")
            (firmware / "hid_send.py").write_text("new helper\n")
            rolled_back = self.run_installer("rollback", root, firmware)
            self.assertEqual(0, rolled_back.returncode, rolled_back.stderr)
            self.assertEqual("old config\n", (deployed / "config.py").read_text())
            self.assertEqual(
                "old legacy code\n",
                (deployed / "legacy_live_service.py").read_text(),
            )
            self.assertEqual(
                "old projector-control.service\n",
                (units / "projector-control.service").read_text(),
            )
            self.assertEqual(
                'SUBSYSTEM=="hidraw", MODE="0666"\n', broad_rule.read_text()
            )
            self.assertFalse((rules / "99-sony-macropad.rules").exists())
            self.assertEqual("old boot\n", (firmware / "boot.py").read_text())
            self.assertEqual("old firmware\n", (firmware / "code.py").read_text())
            self.assertFalse((firmware / "hid_send.py").exists())


if __name__ == "__main__":
    unittest.main()
