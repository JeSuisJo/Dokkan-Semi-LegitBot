import time

from . import console, screen

BATTLE = ("auto_battle_on", "auto_battle_off", "Auto battle")
NAVIGATION = ("auto_navigation_on", "auto_navigation_off", "Auto navigation")

TOLERANCE = 15
PAUSE = 0.4
POLL = 0.5


def enable(*toggles):
    for on_name, off_name, label in toggles:
        tapped = False
        while True:
            with screen.freeze():
                on = screen.see_color(on_name, TOLERANCE)
                off = screen.see_color(off_name, TOLERANCE)

            if on:
                if tapped:
                    console.info(f"{label} on")
                break

            if off:
                screen.tap(off_name)
                tapped = True
                time.sleep(PAUSE)
                continue

            time.sleep(POLL)
