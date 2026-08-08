"""Answer the end-of-run prompt, refilling ACT when the game asks for it."""

import time

from ... import console, screen
from ...stamina import level as stamina

PAUSE = 0.4
# The prompt slides in after the replay tap, so a first capture that shows
# nothing means "not yet", not "no prompt": giving up on it lets the next run
# tap Start on the out-of-ACT dialog, which spends a Dragon Stone.
TIMEOUT = 8.0


def settle():
    """Confirm the prompt and return to the team selection screen.

    Replaying always draws an OK, whether the run can start again or the game
    is asking to restore ACT first. The two are the same frame, so the title
    printed behind the OK is what tells them apart: with it, the OK spends a
    Dragon Stone and the config decides; without it, it just replays.

    With food in the inventory the game skips that dialog and opens the
    recovery menu instead, which the meat icon gives away.
    """
    deadline = time.time() + TIMEOUT

    while True:
        with screen.freeze():
            menu = screen.see_image("restore_act_food") or screen.see_color(
                "stamina_menu"
            )
            confirm = None if menu else screen.find_image("not_enough_act_ok")
            out_of_act = confirm is not None and screen.see_image(
                "restore_act_title"
            )

        if menu or out_of_act:
            console.warn("Out of ACT")
            if menu:
                stamina.from_menu()
            else:
                stamina.from_dialog()
            deadline = time.time() + TIMEOUT
            time.sleep(PAUSE)
            continue

        if confirm is not None:
            screen.tap_at(confirm)
            console.info("Returning to team selection")
            time.sleep(PAUSE)
            return

        if time.time() >= deadline:
            return

        time.sleep(PAUSE)
