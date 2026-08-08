"""ACT refills on a normal stage, from either screen the game can show."""

import time

from .. import console, screen
from . import options

# The refill dialogs stack and animate; a tap sent while one is still sliding
# lands on nothing, so these steps wait longer than the rest of the bot.
PAUSE = 1.0


def from_menu():
    """Refill from the recovery menu, the one listing food and Dragon Stones.

    The game only offers that menu when there is food in the inventory; with an
    empty one it goes straight to the Dragon Stone dialog, so :func:`from_dialog`.
    """
    if options.food_first():
        console.info("Restoring ACT with food")
        screen.tap("level_food")
        time.sleep(PAUSE)
        screen.tap_image("level_food_ok")
        time.sleep(PAUSE)
        # The amount to restore has to be picked before confirming; the button
        # only lights up once the menu has finished sliding in.
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
    """Refill from the bare "not enough ACT" dialog, Dragon Stones only.

    That dialog offers no food, so `use_meat_first` cannot apply here.
    """
    if not options.dragon_stones():
        screen.stop("Out of ACT, and use_dragon_stones is false in config.json")

    console.info("Restoring ACT with Dragon Stones")
    screen.tap_image("dialog_stone_ok")
    time.sleep(PAUSE)
    screen.tap_image("dialog_stone_confirm_ok")
    time.sleep(PAUSE * 2)
    screen.tap("dialog_stone_close")
