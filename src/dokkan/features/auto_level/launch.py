"""Start the stage from the team selection screen."""

import time

from ... import console, screen

PAUSE = 0.4


def launch():
    """Tap the red Start button, wherever it sits in its corner."""
    while True:
        found = screen.find_color("level_start", tolerance=0)
        if found is not None:
            screen.tap_at(found)
            console.info("Starting level")
            time.sleep(PAUSE)
            return
        time.sleep(PAUSE)
