import time

from .. import console, screen
from . import options

PAUSE = 1.0


def from_menu():
    if options.food_first():
        console.info("Restoring ACT with food")
        screen.tap("level_food")
        time.sleep(PAUSE)
        screen.tap_image("level_food_ok")
        time.sleep(PAUSE)
        screen.wait_color("level_refill_button")
        time.sleep(PAUSE)
        screen.tap("level_refill_button")
    elif options.dragon_stones():
        console.info("Restoring ACT with Dragon Stones")
        screen.tap("level_stone")
        time.sleep(PAUSE)
        screen.tap_image("level_stone_ok")
    else:
        options.refuse()

    time.sleep(PAUSE)
    screen.tap_image("level_refill_ok")
    time.sleep(PAUSE)
    screen.tap("level_refill_close")
    time.sleep(PAUSE * 2)
    screen.tap("level_refill_dismiss")


def from_dialog():
    if not options.dragon_stones():
        screen.stop("Out of ACT, and use_dragon_stones is false in config.json")

    console.info("Restoring ACT with Dragon Stones")
    screen.tap_image("dialog_stone_ok")
    time.sleep(PAUSE)
    screen.tap_image("dialog_stone_confirm_ok")
    time.sleep(PAUSE * 2)
    screen.tap("dialog_stone_close")
