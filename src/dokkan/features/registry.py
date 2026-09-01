from dataclasses import dataclass
from typing import Callable, Optional

from . import auto_level, ztur_finish, ztur_retry


@dataclass
class Feature:
    label: str
    run: Callable
    prepare: Optional[Callable] = None


FEATURES = {
    "1": Feature("Auto Level", auto_level.run, prepare=auto_level.prepare),
    "2": Feature("ZTUR Finish", ztur_finish.run, prepare=ztur_finish.prepare),
    "3": Feature("ZTUR Retry", ztur_retry.run, prepare=ztur_retry.prepare),
}
