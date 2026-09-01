"""Android device backend, driven through the bundled adb binary."""

import re
import subprocess
import sys
import time

from .. import config as config_module
from ..paths import PROJECT_ROOT, resolve
from ..prompts import ask_from_list
from .base import Driver, remove

ADB = resolve("platform-tools/adb.exe")

# MuMu, BlueStacks, Nox and LDPlayer each listen on their own loopback port and
# do not show up in `adb devices` until something connects to them.
EMULATOR_PORTS = (
    "127.0.0.1:7555",
    "127.0.0.1:5555",
    "127.0.0.1:62001",
    "127.0.0.1:21503",
)

# Under pythonw.exe (no console), each adb.exe call would pop up its own console
# window. CREATE_NO_WINDOW keeps those child processes headless.
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

# dumpsys prints the focused activity as "package/activity" inside an
# ActivityRecord{...} blob, on a line carrying one of these markers.
_RESUMED = ("topResumedActivity=", "ResumedActivity:")
_COMPONENT = re.compile(r"([A-Za-z0-9_.]+/[A-Za-z0-9_.$]+)")


class AdbDriver(Driver):
    """Talk to one Android device over adb."""

    def __init__(self, device_id=None):
        # The device is resolved by connect_device() (run start), so building
        # the driver touches neither adb nor config.json.
        self.device_id = device_id

    # ---------------- Device resolution ----------------

    def connect_device(self):
        """Resolve the device to drive, before a run.

        Trusts the saved device while it still answers (no detection at all);
        only scans, auto-selects or asks once it has gone missing.
        """
        configured = config_module.get_config().get("device_id")

        if configured and self._is_online(configured):
            self.device_id = configured
            return

        self._connect_emulator_ports()
        devices = self.list_devices()

        # None found: the adb server may be wedged. Restart it once and retry.
        if not devices:
            print("No ADB device found, restarting ADB server...")
            self._restart_server()
            self._connect_emulator_ports()
            devices = self.list_devices()

        if not devices:
            self.stop("No device detected. Start your emulator, then try again.")

        if len(devices) == 1:
            self._use_device(devices[0], "ADB device auto-selected")
        else:
            # A saved id reaching this point is stale, and adopting it silently
            # would drive whichever emulator now answers to it.
            self._use_device(self._ask_device(devices), "ADB device selected")

    @classmethod
    def _connect_emulator_ports(cls):
        for port in EMULATOR_PORTS:
            cls._adb(["connect", port], timeout=2)

    @classmethod
    def list_devices(cls):
        lines = cls._adb_text(["devices"], timeout=10).strip().split("\n")[1:]
        return [line.split("\t")[0] for line in lines if "\tdevice" in line]

    @classmethod
    def _restart_server(cls):
        cls._adb(["kill-server"], timeout=10)
        time.sleep(1)
        cls._adb(["start-server"], timeout=15)
        time.sleep(2)

    @classmethod
    def _is_online(cls, device_id):
        """True if that one device answers, without scanning the whole list."""
        state = cls._adb_text(["get-state"], device_id=device_id, timeout=10)
        return state.strip() == "device"

    @classmethod
    def _ask_device(cls, devices):
        labels = [cls._device_label(device) for device in devices]
        return devices[ask_from_list("Multiple devices connected:", labels) - 1]

    @classmethod
    def _device_label(cls, device_id):
        package = cls._foreground_package(device_id)
        return f"{device_id} - {package}" if package else device_id

    @classmethod
    def _foreground_package(cls, device_id):
        """The package showing on that device, or "" when none resolves.

        ro.product.model would be shorter and useless: an emulator spoofs a
        real phone, and two instances report the same one.
        """
        dump = cls._adb_text(
            ["shell", "dumpsys", "activity", "activities"], device_id=device_id
        )
        for line in dump.splitlines():
            if not any(marker in line for marker in _RESUMED):
                continue
            match = _COMPONENT.search(line)
            # An idle emulator resumes its launcher. The whole component is
            # tested, app.lawnchair/.LawnchairLauncher says so only in the
            # activity half.
            if match and "launcher" not in match.group(1).lower():
                return match.group(1).split("/")[0]
        return ""

    def _use_device(self, device_id, note):
        self.device_id = device_id
        config_module.save("device_id", device_id)
        print(f"{note}: {device_id}")

    # ---------------- Transport ----------------

    @staticmethod
    def _adb(cmd, device_id=None, text=False, timeout=30):
        """Run one adb command; return the CompletedProcess, or None if it died.

        Single place where the binary, the ``-s <device>`` selector and the
        headless-child flag are spelled out.
        """
        base = [ADB, "-s", device_id] if device_id else [ADB]
        try:
            return subprocess.run(
                base + cmd, capture_output=True, text=text, timeout=timeout,
                cwd=PROJECT_ROOT, creationflags=_NO_WINDOW,
            )
        except (subprocess.SubprocessError, OSError):
            return None

    @classmethod
    def _adb_text(cls, cmd, device_id=None, timeout=30):
        """Run one adb command and return its stdout, "" on any failure."""
        result = cls._adb(cmd, device_id=device_id, text=True, timeout=timeout)
        if result is None or result.returncode != 0:
            return ""
        return result.stdout

    def _run(self, cmd):
        result = self._adb(cmd, device_id=self.device_id, text=True)
        return result is not None and result.returncode == 0

    def _exec_out(self, cmd):
        """Run ``adb exec-out`` and return its raw stdout (empty on failure)."""
        result = self._adb(["exec-out"] + cmd, device_id=self.device_id)
        if result is None or result.returncode != 0:
            return b""
        return result.stdout

    def capture(self):
        """Return the raw PNG bytes of the current screen."""
        # exec-out streams the PNG straight back, so one adb call replaces the
        # screencap + pull + rm round-trip through /sdcard, and nothing has to
        # touch the disk for a check that only reads pixels.
        data = self._exec_out(["screencap", "-p"])
        if data.startswith(b"\x89PNG"):
            return data
        return self._capture_via_pull()

    def _capture_via_pull(self):
        """Capture via /sdcard, for adb daemons whose exec-out returns nothing.

        Every step is checked: an unchecked failure here used to surface far
        away as a confusing "file not found" from the image layer, instead of
        naming the real cause (the device went away mid-run).
        """
        dest = resolve("temp.png")
        if not (
            self._run(["shell", "screencap", "-p", "/sdcard/tmp.png"])
            and self._run(["pull", "/sdcard/tmp.png", dest])
        ):
            self.stop(
                "Lost contact with the ADB device while capturing the screen. "
                "Check that your device is still connected, then try again."
            )
        self._run(["shell", "rm", "/sdcard/tmp.png"])
        try:
            with open(dest, "rb") as f:
                return f.read()
        finally:
            remove(dest)

    # ---------------- Actions ----------------

    def tap(self, x, y):
        self._run(["shell", "input", "tap", str(x), str(y)])

    def hold(self, x, y, ms=500):
        self._run(["shell", "input", "swipe", str(x), str(y), str(x), str(y), str(ms)])

    def swipe(self, x1, y1, x2, y2, ms=300):
        self._run(
            ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms)]
        )

    def swipe_hold(self, x1, y1, x2, y2, move_ms=300, hold_ms=500):
        """Swipe, then hold at the destination before releasing.

        Holding drops the release velocity to zero, which prevents the scroll
        inertia ("fling") from continuing past the target position.
        """
        def motion(action, x, y):
            self._run(["shell", "input", "motionevent", action, str(x), str(y)])

        steps = 8
        motion("DOWN", x1, y1)
        for i in range(1, steps + 1):
            mx = int(x1 + (x2 - x1) * i / steps)
            my = int(y1 + (y2 - y1) * i / steps)
            motion("MOVE", mx, my)
            time.sleep(move_ms / 1000 / steps)
        time.sleep(hold_ms / 1000)
        motion("MOVE", x2, y2)
        motion("UP", x2, y2)

    def write(self, text):
        escaped = text.replace(" ", "\\ ").replace("&", "\\&")
        self._run(["shell", "input", "text", escaped])

    def enter(self):
        self._run(["shell", "input", "keyevent", "66"])

    def delete(self):
        self._run(["shell", "input", "keyevent", "67"])

    def back(self):
        self._run(["shell", "input", "keyevent", "4"])
