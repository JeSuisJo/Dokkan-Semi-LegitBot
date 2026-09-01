import time
from dataclasses import dataclass

from ... import console, screen, ztur

PAUSE = 0.4
AFTER_CONFIRM = 1.0


@dataclass(frozen=True)
class Medal:
    label: str
    row: str
    runs: int
    delay: float = 5.0


MEDALS = (
    Medal("Bronze", "medal_bronze", 6, delay=0),
    Medal("Silver", "medal_silver", 5),
    Medal("Gold", "medal_gold", 3),
    Medal("Rainbow", "medal_rainbow", 3),
)


def select(medal):
    console.banner("ZTUR Retry", f"{medal.label} medal selection")

    while not ztur.on_list():
        time.sleep(PAUSE)

    if medal.delay:
        time.sleep(medal.delay)

    screen.tap("medal_list")
    time.sleep(PAUSE)

    if screen.see_color("medal_selected"):
        screen.tap(medal.row)
    else:
        screen.tap("medal_list")
    time.sleep(PAUSE)

    screen.tap_image("medal_confirm_ok")
    time.sleep(AFTER_CONFIRM)
