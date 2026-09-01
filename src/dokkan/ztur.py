import time

from . import console, screen

PAUSE = 0.4


def on_list():
    return screen.see_image("ztur_stage")


def lost():
    return screen.see_any_image("loss_ztur", "loss_ztur_pop_up")


def dismiss_loss():
    found = screen.find_image("loss_ztur_pop_up")
    if found is not None:
        screen.tap_at(found)
        time.sleep(PAUSE)


def reach(too_many_friends, friend_request, back):
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
