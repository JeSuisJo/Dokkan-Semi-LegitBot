from .adb import AdbDriver
from .base import Driver, StopScript

driver = AdbDriver()

__all__ = ["Driver", "StopScript", "driver"]
