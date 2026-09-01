import time

from ... import console, screen

PAUSE = 0.4
POLL = 0.5


def wait_for_end(replay):
    while True:
        with screen.freeze():
            friend = screen.see_image("friend_add_ok")
            ended = screen.see_image("level_end_ok")

        if friend:
            screen.tap("friend_add_ok")
            console.info("Friend request cancelled")
            time.sleep(PAUSE)
            continue

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
