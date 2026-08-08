"""The four medal tiers, and how to pick one in the stage's medal list."""

import time
from dataclasses import dataclass

from ... import console, screen, ztur

PAUSE = 0.4
AFTER_CONFIRM = 1.0


@dataclass(frozen=True)
class Medal:
    label: str
    row: str
    # Runs the game needs per character to hand out that tier.
    runs: int
    # Bronze sits under the thumb already; the others need the list scrolled,
    # and it slides for a good five seconds.
    delay: float = 5.0


MEDALS = (
    Medal("Bronze", "medal_bronze", 6, delay=0),
    Medal("Silver", "medal_silver", 5),
    Medal("Gold", "medal_gold", 3),
    Medal("Rainbow", "medal_rainbow", 3),
)


def select(medal):
    """Open the medal list and pick ``medal``, up to the confirmation."""
    console.banner("ZTUR Retry", f"{medal.label} medal selection")

    while not ztur.on_list():
        time.sleep(PAUSE)

    if medal.delay:
        time.sleep(medal.delay)

    screen.tap("medal_list")
    time.sleep(PAUSE)

    # The marker only shows once the list is unfolded; without it the tap that
    # unfolds it has not landed yet.
    if screen.see_color("medal_selected"):
        screen.tap(medal.row)
    else:
        screen.tap("medal_list")
    time.sleep(PAUSE)

    screen.tap_image("medal_confirm_ok")
    time.sleep(AFTER_CONFIRM)
