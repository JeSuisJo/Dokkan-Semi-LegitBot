"""One medal run: enter the stage, fight, come back to the list."""

import time

from ... import console, screen, ztur
from ...stamina import ztur as stamina

PAUSE = 0.4
DEATH_CONFIRM = 2.0

POPUPS = ("retry_too_many_friends_ok", "retry_friend_request_ok", "retry_back")


def run_once():
    """Play one run. Returns True when the team died and it does not count."""
    _launch()
    died = _wait_for_clear()
    ztur.reach(*POPUPS)
    return died


def _launch():
    if not ztur.on_list():
        return

    console.info("Opening the ZTUR stage")
    screen.tap("retry_stage")
    time.sleep(PAUSE)

    while True:
        with screen.freeze():
            ready = screen.see_color("retry_start")
            food = screen.see_color("retry_food_button")
            no_act = screen.see_image("retry_no_act_ok")
            missed = ztur.on_list()

        if ready:
            console.info("Starting level")
            screen.tap("retry_start")
            time.sleep(PAUSE)
            return
        if food:
            console.warn("Out of ACT")
            stamina.from_menu()
        elif no_act:
            console.warn("Out of ACT")
            stamina.from_dialog()
        elif missed:
            screen.tap("retry_stage")

        time.sleep(PAUSE)


def _wait_for_clear():
    """Tap through the fight until it clears. Returns True on a death instead.

    The defeat screen names itself, so it settles the question on its own. Short
    of it, a death also drops straight back to the stage list, which is where a
    tap too many lands too, so there the list has to still be there a moment
    later to count.
    """
    while True:
        with screen.freeze():
            found = screen.find_image("retry_complete_ok")
            defeat = found is None and ztur.lost()
            listed = found is None and not defeat and ztur.on_list()

        if found is not None:
            console.info("Level complete")
            screen.tap_at(found)
            time.sleep(PAUSE)
            return False

        if defeat:
            console.warn("Team died, replaying the run")
            ztur.dismiss_loss()
            return True

        if listed:
            time.sleep(DEATH_CONFIRM)
            if ztur.on_list():
                console.warn("Team died, replaying the run")
                return True

        screen.tap("retry_back")
        time.sleep(PAUSE)
