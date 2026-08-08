"""Active driver instance.

Swapping backend is a one-line change here; nothing touches adb at import, the
device is resolved by ``connect_device()``.
"""

from .adb import AdbDriver
from .base import Driver, StopScript

driver = AdbDriver()

__all__ = ["Driver", "StopScript", "driver"]
