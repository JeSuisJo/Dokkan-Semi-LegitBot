import time

from ... import console, screen
from ...stamina import level as stamina

PAUSE = 0.4
TIMEOUT = 8.0


def settle():
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
