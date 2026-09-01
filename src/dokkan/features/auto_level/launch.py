import time

from ... import console, screen

PAUSE = 0.4


def launch():
    while True:
        found = screen.find_color("level_start", tolerance=0)
        if found is not None:
            screen.tap_at(found)
            console.info("Starting level")
            time.sleep(PAUSE)
            return
        time.sleep(PAUSE)
