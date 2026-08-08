"""Central registry of the modes shown in the menu.

Adding a mode: create ``features/<name>/``, re-export ``prepare`` and ``run``
from its ``__init__``, then add one line here.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from . import auto_level, ztur_finish, ztur_retry


@dataclass
class Feature:
    label: str
    run: Callable
    # Runs before `run`, after the menu choice; returns the args passed to `run`.
    prepare: Optional[Callable] = None


# Keys are the strings typed at the menu; insertion order defines menu order.
FEATURES = {
    "1": Feature("Auto Level", auto_level.run, prepare=auto_level.prepare),
    "2": Feature("ZTUR Finish", ztur_finish.run, prepare=ztur_finish.prepare),
    "3": Feature("ZTUR Retry", ztur_retry.run, prepare=ztur_retry.prepare),
}
