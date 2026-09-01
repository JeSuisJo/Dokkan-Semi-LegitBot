import time

from .coords import coords
from .driver import driver


def freeze():
    return driver.freeze()


def tap(name):
    driver.tap(*coords(name)["tap"])


def tap_at(point):
    driver.tap(*point)


def hold(name, ms=500):
    driver.hold(*coords(name)["tap"], ms=ms)


def swipe(name):
    driver.swipe(*coords(name)["swipe"])


def swipe_hold(name, hold_ms=500):
    driver.swipe_hold(*coords(name)["swipe"], hold_ms=hold_ms)


def write(text):
    driver.write(text)


def enter():
    driver.enter()


def delete():
    driver.delete()


def back():
    driver.back()


def stop(msg="Script stopped"):
    driver.stop(msg)


DEFAULT_THRESHOLD = 0.9
DEFAULT_SCALES = (1.0,)


def _image(name, threshold=None, scales=None, color_threshold=None):
    block = coords(name)
    return (
        block["img"],
        block["region"],
        threshold if threshold is not None else block.get("threshold", DEFAULT_THRESHOLD),
        scales if scales is not None else block.get("scales", DEFAULT_SCALES),
        color_threshold if color_threshold is not None else block.get("color_threshold"),
    )


def find_image(name, threshold=None, scales=None, color_threshold=None):
    img, region, t, s, c = _image(name, threshold, scales, color_threshold)
    return driver.find_image(img, region, t, s, c)


def see_image(name, threshold=None, scales=None, color_threshold=None):
    return find_image(name, threshold, scales, color_threshold) is not None


def wait_image(name, threshold=None, poll=0.5, scales=None, color_threshold=None):
    img, region, t, s, c = _image(name, threshold, scales, color_threshold)
    return driver.wait_image(img, region, t, poll, s, c)


def tap_image(name, dx=0, dy=0, threshold=None, poll=0.5, scales=None,
              color_threshold=None):
    img, region, t, s, c = _image(name, threshold, scales, color_threshold)
    return driver.tap_image(img, region, dx, dy, t, poll, s, c)


def see_any_image(*names, threshold=None):
    with driver.freeze():
        return any(see_image(name, threshold) for name in names)


def wait_any_image(*names, threshold=None, poll=0.5):
    while not see_any_image(*names, threshold=threshold):
        time.sleep(poll)


def _probe(block):
    return block["rgb_at"] if "rgb_at" in block else block["tap"]


def see_color(name, tolerance=10):
    block = coords(name)
    return driver.see_color(*_probe(block), block["rgb"], tolerance)


def wait_color(name, tolerance=10, poll=0.5):
    block = coords(name)
    driver.wait_color(*_probe(block), block["rgb"], tolerance, poll)


def find_color(name, tolerance=10):
    block = coords(name)
    return driver.find_color_in(block["region"], block["rgb"], tolerance)


def see_color_in(name, region_name, tolerance=10):
    return driver.see_color_in(
        coords(region_name)["region"], coords(name)["rgb"], tolerance
    )


def tap_until(name, target, threshold=None, poll=0.5):
    while not see_image(target, threshold):
        tap(name)
        time.sleep(poll)


def tap_until_color(name, target, tolerance=10, poll=0.5):
    while not see_color(target, tolerance):
        tap(name)
        time.sleep(poll)
