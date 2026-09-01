import time

from .. import console, screen
from . import options

PAUSE = 1.0


def from_menu():
    if options.food_first():
        console.info("Restoring ACT with food")
        screen.tap("ztur_food")
        time.sleep(PAUSE)
        for ok in ("ztur_food_ok_1", "ztur_food_ok_2", "ztur_food_ok_3"):
            screen.tap_image(ok)
            time.sleep(PAUSE)
    elif options.dragon_stones():
        console.info("Restoring ACT with Dragon Stones")
        screen.tap("ztur_stone")
        time.sleep(PAUSE)
        for ok in ("ztur_stone_ok_1", "ztur_stone_ok_2"):
            screen.tap_image(ok)
            time.sleep(PAUSE)
    else:
        options.refuse()


def from_dialog():
    if not options.dragon_stones():
        screen.stop("Out of ACT, and use_dragon_stones is false in config.json")

    console.info("Restoring ACT with Dragon Stones")
    screen.tap("ztur_dialog_stone")
    time.sleep(PAUSE)
    screen.tap_image("ztur_dialog_stone_ok")
