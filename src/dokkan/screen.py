"""Named screen interactions: map ``coords/*.json`` entries to driver actions.

This is what features are written against. Everything takes a coord *name*, so
a screen change is fixed in JSON instead of in the code.
"""

import time

from .coords import coords
from .driver import driver


def freeze():
    """Answer every check in the ``with`` block from a single capture.

    Never around a tap or a ``wait_*``: the image can no longer change.
    """
    return driver.freeze()


# ---------------- Actions ----------------

def tap(name):
    driver.tap(*coords(name)["tap"])


def tap_at(point):
    """Tap a point a lookup returned (``find_image``, ``find_color``)."""
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


# ---------------- Images ----------------

DEFAULT_THRESHOLD = 0.9
# Every reference here is cropped off the user's own screen by helper/, so it is
# already the right size; searching for shrunken copies too would only invite a
# false match inside the small regions the dialog buttons sit in.
DEFAULT_SCALES = (1.0,)


def _image(name, threshold=None, scales=None, color_threshold=None):
    """The entry's reference, its region, and how loosely to match it.

    A reference that needs a looser threshold says so in its own JSON entry
    rather than at every call site; an argument passed here still wins.
    """
    block = coords(name)
    return (
        block["img"],
        block["region"],
        threshold if threshold is not None else block.get("threshold", DEFAULT_THRESHOLD),
        scales if scales is not None else block.get("scales", DEFAULT_SCALES),
        color_threshold if color_threshold is not None else block.get("color_threshold"),
    )


def find_image(name, threshold=None, scales=None, color_threshold=None):
    """Centre of ``name``'s reference inside its region, or None."""
    img, region, t, s, c = _image(name, threshold, scales, color_threshold)
    return driver.find_image(img, region, t, s, c)


def see_image(name, threshold=None, scales=None, color_threshold=None):
    """True when ``name``'s reference is visible in its region."""
    return find_image(name, threshold, scales, color_threshold) is not None


def wait_image(name, threshold=None, poll=0.5, scales=None, color_threshold=None):
    """Block until ``name`` shows up; return its centre (x, y)."""
    img, region, t, s, c = _image(name, threshold, scales, color_threshold)
    return driver.wait_image(img, region, t, poll, s, c)


def tap_image(name, dx=0, dy=0, threshold=None, poll=0.5, scales=None,
              color_threshold=None):
    """Wait for ``name``, then tap where it matched, shifted by dx/dy.

    The counterpart of :func:`tap` for a target with no fixed position.
    """
    img, region, t, s, c = _image(name, threshold, scales, color_threshold)
    return driver.tap_image(img, region, dx, dy, t, poll, s, c)


def see_any_image(*names, threshold=None):
    """True when any of ``names`` is on screen, from a single capture."""
    with driver.freeze():
        return any(see_image(name, threshold) for name in names)


def wait_any_image(*names, threshold=None, poll=0.5):
    while not see_any_image(*names, threshold=threshold):
        time.sleep(poll)


# ---------------- Colours ----------------

def _probe(block):
    """Where to read the colour: ``rgb_at`` when it differs from the tap point."""
    # Not block.get("rgb_at", block["tap"]): that reads "tap" even when the
    # entry has an "rgb_at", and plenty of them are colour probes with no tap.
    return block["rgb_at"] if "rgb_at" in block else block["tap"]


def see_color(name, tolerance=10):
    """True when ``name``'s probe pixel shows its expected colour."""
    block = coords(name)
    return driver.see_color(*_probe(block), block["rgb"], tolerance)


def wait_color(name, tolerance=10, poll=0.5):
    block = coords(name)
    driver.wait_color(*_probe(block), block["rgb"], tolerance, poll)


def find_color(name, tolerance=10):
    """Where ``name``'s colour shows up inside its own region, or None."""
    block = coords(name)
    return driver.find_color_in(block["region"], block["rgb"], tolerance)


def see_color_in(name, region_name, tolerance=10):
    """True when ``name``'s colour shows up anywhere inside ``region_name``."""
    return driver.see_color_in(
        coords(region_name)["region"], coords(name)["rgb"], tolerance
    )


# ---------------- Loops ----------------

def tap_until(name, target, threshold=None, poll=0.5):
    """Tap ``name`` until ``target`` shows up. Blocks forever."""
    while not see_image(target, threshold):
        tap(name)
        time.sleep(poll)


def tap_until_color(name, target, tolerance=10, poll=0.5):
    """Tap ``name`` until ``target``'s probe pixel matches its colour."""
    while not see_color(target, tolerance):
        tap(name)
        time.sleep(poll)
