"""Enter the stage from the list, then sit through the fight."""

import time

from ... import console, screen, ztur

PAUSE = 0.4


def launch():
    """Open the stage and start it."""
    console.info("Opening the ZTUR stage")
    screen.tap("finish_stage")
    time.sleep(PAUSE)

    while True:
        with screen.freeze():
            ready = screen.see_color("finish_start")
            # Still on the list: the tap landed next to the row, not on it.
            missed = not ready and ztur.on_list()

        if ready:
            console.info("Starting level")
            screen.tap("finish_start")
            time.sleep(PAUSE)
            return
        if missed:
            screen.tap("finish_stage_retry")

        time.sleep(PAUSE)


def wait_for_clear():
    """Tap through the fight until its completion prompt, then confirm it.

    Returns True on a defeat instead: the enemy only levels up on a clear, so a
    lost run has to be played again.
    """
    while True:
        with screen.freeze():
            found = screen.find_image("finish_complete_ok")
            defeat = found is None and ztur.lost()

        if found is not None:
            console.info("Level complete")
            screen.tap_at(found)
            time.sleep(PAUSE)
            return False

        if defeat:
            console.warn("Team died, replaying the run")
            ztur.dismiss_loss()
            return True

        screen.tap("finish_back")
        time.sleep(PAUSE)
