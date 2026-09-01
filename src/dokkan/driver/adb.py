import re
import subprocess
import sys
import time

from .. import config as config_module
from ..paths import PROJECT_ROOT, resolve
from ..prompts import ask_from_list
from .base import Driver, remove

ADB = resolve("platform-tools/adb.exe")

EMULATOR_PORTS = (
    "127.0.0.1:7555",
    "127.0.0.1:5555",
    "127.0.0.1:62001",
    "127.0.0.1:21503",
)

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

_RESUMED = ("topResumedActivity=", "ResumedActivity:")
_COMPONENT = re.compile(r"([A-Za-z0-9_.]+/[A-Za-z0-9_.$]+)")


class AdbDriver(Driver):
    def __init__(self, device_id=None):
        self.device_id = device_id

    def connect_device(self):
        configured = config_module.get_config().get("device_id")

        if configured and self._is_online(configured):
            self.device_id = configured
            return

        self._connect_emulator_ports()
        devices = self.list_devices()

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
        dump = cls._adb_text(
            ["shell", "dumpsys", "activity", "activities"], device_id=device_id
        )
        for line in dump.splitlines():
            if not any(marker in line for marker in _RESUMED):
                continue
            match = _COMPONENT.search(line)
            if match and "launcher" not in match.group(1).lower():
                return match.group(1).split("/")[0]
        return ""

    def _use_device(self, device_id, note):
        self.device_id = device_id
        config_module.save("device_id", device_id)
        print(f"{note}: {device_id}")

    @staticmethod
    def _adb(cmd, device_id=None, text=False, timeout=30):
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
        result = cls._adb(cmd, device_id=device_id, text=True, timeout=timeout)
        if result is None or result.returncode != 0:
            return ""
        return result.stdout

    def _run(self, cmd):
        result = self._adb(cmd, device_id=self.device_id, text=True)
        return result is not None and result.returncode == 0

    def _exec_out(self, cmd):
        result = self._adb(["exec-out"] + cmd, device_id=self.device_id)
        if result is None or result.returncode != 0:
            return b""
        return result.stdout

    def capture(self):
        data = self._exec_out(["screencap", "-p"])
        if data.startswith(b"\x89PNG"):
            return data
        return self._capture_via_pull()

    def _capture_via_pull(self):
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

    def tap(self, x, y):
        self._run(["shell", "input", "tap", str(x), str(y)])

    def hold(self, x, y, ms=500):
        self._run(["shell", "input", "swipe", str(x), str(y), str(x), str(y), str(ms)])

    def swipe(self, x1, y1, x2, y2, ms=300):
        self._run(
            ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms)]
        )

    def swipe_hold(self, x1, y1, x2, y2, move_ms=300, hold_ms=500):
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
