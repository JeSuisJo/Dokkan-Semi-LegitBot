"""The ZTUR stage list, the screen both ZTUR modes start and end every run on.

It sits beside `features/` rather than inside one of them: ZTUR Finish and ZTUR
Retry enter the same list, and only the popups on the way to it are captured at
different spots, so they are passed in by name.
"""

import time

from . import console, screen

PAUSE = 0.4


def on_list():
    return screen.see_image("ztur_stage")


def lost():
    """True on either screen a defeat puts up, the popup and the one behind it."""
    return screen.see_any_image("loss_ztur", "loss_ztur_pop_up")


def dismiss_loss():
    """Close the defeat popup, which swallows every tap until it is answered."""
    found = screen.find_image("loss_ztur_pop_up")
    if found is not None:
        screen.tap_at(found)
        time.sleep(PAUSE)


def reach(too_many_friends, friend_request, back):
    """Back out of every popup and result screen until the stage list shows."""
    while True:
        with screen.freeze():
            if on_list():
                return
            too_many = screen.find_image(too_many_friends)
            request = screen.see_image(friend_request)

        if too_many is not None:
            console.info("Too many friends")
            screen.tap_at(too_many)
        elif request:
            console.info("Friend request cancelled")
            screen.tap(friend_request)
        else:
            screen.tap(back)

        time.sleep(PAUSE)
