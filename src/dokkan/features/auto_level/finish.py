"""Sit through the fight and its reward screens, up to the replay prompt."""

import time

from ... import console, screen

PAUSE = 0.4
POLL = 0.5


def wait_for_end(replay):
    """Tap through the fight until the end-of-level prompt, then answer it.

    ``replay`` taps its OK, which starts the stage again; without it the prompt
    is left on screen for the caller to leave.
    """
    while True:
        with screen.freeze():
            friend = screen.see_image("friend_add_ok")
            ended = screen.see_image("level_end_ok")

        if friend:
            screen.tap("friend_add_ok")
            console.info("Friend request cancelled")
            time.sleep(PAUSE)
            continue

        # Blind tap: the fight, the reward reel and the item drops all advance
        # on a tap in the top corner, and none of them is worth recognising.
        screen.tap("dismiss_result")

        if ended:
            if replay:
                screen.tap("level_end_ok")
                console.info("Restarting level")
            else:
                console.info("Level completed")
            time.sleep(PAUSE)
            return

        time.sleep(POLL)
