"""Platform-independent screen matching, on top of a driver's ``screenshot()``.

Everything here works on raw coordinates. The named layer lives in
``screen.py``, which reads ``coords/*.json`` and calls into these.
"""

import contextlib
import io
import os
import time
from functools import lru_cache

from PIL import Image

from ..paths import resolve

# Tried in order when a reference was captured at another resolution.
_SCALES = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5)


class StopScript(Exception):
    """Raised to abort a run cleanly (nothing left to do, unexpected screen...)."""

    def __init__(self, msg="Script stopped"):
        super().__init__(msg)


@lru_cache(maxsize=None)
def load_image(reference_path):
    """Return a reference image, decoded once and kept in memory."""
    path = resolve(reference_path)
    if not os.path.exists(path):
        # Named here rather than left as a bare FileNotFoundError: a reference
        # is captured per screen, so a fresh clone is missing several.
        raise StopScript(
            f"Missing reference image '{reference_path}'. Capture it with "
            "helper/crop_by_clicks.py, then run helper/check_coords.py to see "
            "what else is missing."
        )
    return Image.open(path).convert("RGB")


@lru_cache(maxsize=None)
def _load_bgr(reference_path):
    """Return a reference as the BGR array OpenCV matches against, cached."""
    import cv2
    import numpy as np

    return cv2.cvtColor(np.array(load_image(reference_path)), cv2.COLOR_RGB2BGR)


def remove(path):
    """Delete a file, ignoring a missing one or a lock we cannot beat."""
    with contextlib.suppress(OSError):
        os.remove(path)


class Driver:
    """Subclasses implement the transport; everything below is shared."""

    # ---------------- To implement ----------------

    def connect_device(self):
        """Resolve the target device. Called once before each run."""

    def capture(self):
        """Return the current screen as PNG bytes."""
        raise NotImplementedError

    def tap(self, x, y):
        raise NotImplementedError

    def hold(self, x, y, ms=500):
        raise NotImplementedError

    def swipe(self, x1, y1, x2, y2, ms=300):
        raise NotImplementedError

    def swipe_hold(self, x1, y1, x2, y2, move_ms=300, hold_ms=500):
        raise NotImplementedError

    def write(self, text):
        raise NotImplementedError

    def enter(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def back(self):
        raise NotImplementedError

    # ---------------- Screen ----------------

    _frozen = None

    def get_screen(self):
        """Return the screen as an RGB image, the frozen one inside a freeze."""
        if self._frozen is not None:
            return self._frozen
        return Image.open(io.BytesIO(self.capture())).convert("RGB")

    def screenshot(self, dest="temp.png"):
        """Write the current screen to ``dest`` and return its absolute path.

        For the ``helper/`` scripts, which want a file; the checks below read
        pixels straight from :meth:`get_screen` and never touch the disk.
        """
        dest = resolve(dest)
        with open(dest, "wb") as f:
            f.write(self.capture())
        return dest

    @contextlib.contextmanager
    def freeze(self):
        """Capture once and answer every check in the block from that capture.

        Never tap or wait inside a freeze: the image no longer changes, so a
        wait would spin forever and later checks would read a pre-tap screen.
        """
        previous = self._frozen
        self._frozen = self.get_screen()
        try:
            yield
        finally:
            self._frozen = previous

    # ---------------- Image ----------------

    def _match(self, reference_path, region, scales):
        """Yield ``(haystack, ref, tw, th, result)`` for each usable scale.

        Shared by :meth:`find_image` and :meth:`find_images`, which differ only
        in how they read the correlation map back.
        """
        import cv2
        import numpy as np

        if scales is None:
            scales = _SCALES

        shot = self.get_screen().crop(tuple(region))
        haystack = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
        ref = _load_bgr(reference_path)

        h_h, h_w = haystack.shape[:2]
        for scale in scales:
            tw, th = int(ref.shape[1] * scale), int(ref.shape[0] * scale)
            if tw < 1 or th < 1 or tw > h_w or th > h_h:
                continue
            template = cv2.resize(ref, (tw, th), interpolation=cv2.INTER_AREA)
            yield haystack, ref, tw, th, cv2.matchTemplate(
                haystack, template, cv2.TM_CCOEFF_NORMED
            )

    def find_image(self, reference_path, region, threshold=0.9, scales=None,
                   color_threshold=None):
        """Look for the reference inside ``region``; return its centre or None.

        The reference is slid over the region rather than stretched to fit, so
        it may be smaller than the area searched, and may move inside it.
        ``scales`` resizes it for a template captured at another resolution.

        ``color_threshold`` re-scores the match on colour: template matching is
        insensitive to brightness/contrast, so a greyed-out copy still
        correlates highly. Set it to reject the disabled version.
        """
        import cv2

        for haystack, ref, tw, th, result in self._match(
                reference_path, region, scales):
            _, score, _, loc = cv2.minMaxLoc(result)
            if score < threshold:
                continue
            box = (loc[0], loc[1], loc[0] + tw, loc[1] + th)
            # A later scale may find the right colour elsewhere, so keep looking
            # instead of stopping on this rejected match.
            if color_threshold is not None and not _color_match(
                    haystack, ref, box, color_threshold):
                continue
            return (region[0] + loc[0] + tw // 2, region[1] + loc[1] + th // 2)

        return None

    def find_images(self, reference_path, region, threshold=0.9, scales=None,
                    max_results=30, color_threshold=None):
        """Locate every copy of the same image inside ``region``.

        Matches are de-duplicated with non-maximum suppression, so one on-screen
        copy detected across several scales counts once while genuinely separate
        copies are all kept. Returns centres, best score first.
        """
        import numpy as np

        haystack = ref = None
        boxes = []  # (score, x1, y1, x2, y2) in region-local coordinates
        for haystack, ref, tw, th, result in self._match(
                reference_path, region, scales):
            ys, xs = np.where(result >= threshold)
            for x, y in zip(xs.tolist(), ys.tolist()):
                boxes.append((float(result[y, x]), x, y, x + tw, y + th))

        boxes.sort(reverse=True)
        kept = []
        for _score, x1, y1, x2, y2 in boxes:
            if any(_iou((x1, y1, x2, y2), k) > 0.3 for k in kept):
                continue
            if color_threshold is not None and not _color_match(
                    haystack, ref, (x1, y1, x2, y2), color_threshold):
                continue
            kept.append((x1, y1, x2, y2))
            if len(kept) >= max_results:
                break

        return [
            (region[0] + (x1 + x2) // 2, region[1] + (y1 + y2) // 2)
            for x1, y1, x2, y2 in kept
        ]

    def see_image(self, reference_path, region, threshold=0.9, scales=None,
                  color_threshold=None):
        """True when the reference is visible anywhere in the region."""
        return self.find_image(
            reference_path, region, threshold, scales, color_threshold
        ) is not None

    def wait_image(self, reference_path, region, threshold=0.9, poll=0.5, scales=None,
                   color_threshold=None):
        """Block until the reference shows up; return its centre (x, y)."""
        while True:
            found = self.find_image(
                reference_path, region, threshold, scales, color_threshold
            )
            if found is not None:
                return found
            time.sleep(poll)

    def tap_image(self, reference_path, region, dx=0, dy=0, threshold=0.9, poll=0.5,
                  scales=None, color_threshold=None):
        """Wait for the reference, then tap where it matched, shifted by dx/dy."""
        x, y = self.wait_image(
            reference_path, region, threshold, poll, scales, color_threshold
        )
        x, y = x + dx, y + dy
        self.tap(x, y)
        return (x, y)

    # ---------------- Colour ----------------

    def get_color(self, x, y):
        return self.get_screen().getpixel((x, y))

    def see_color(self, x, y, target, tolerance=10):
        return all(abs(a - b) <= tolerance for a, b in zip(self.get_color(x, y), target))

    def find_color_in(self, region, target, tolerance=10):
        """Leftmost pixel of ``region`` matching ``target``, in screen coordinates.

        For a button whose colour identifies it but whose position moves; the
        pixel returned is on the button, so it can be tapped directly.
        """
        import numpy as np

        # Vectorised: a region can hold a million pixels, and this is called in
        # polling loops, so a per-pixel Python comparison is far too slow.
        pixels = np.asarray(
            self.get_screen().crop(tuple(region)), dtype=np.int16
        )
        gaps = np.abs(pixels - np.asarray(target, dtype=np.int16))
        ys, xs = np.where((gaps <= tolerance).all(axis=-1))
        if xs.size == 0:
            return None
        first = np.lexsort((ys, xs))[0]
        return (region[0] + int(xs[first]), region[1] + int(ys[first]))

    def see_color_in(self, region, target, tolerance=10):
        """True when at least one pixel of ``region`` matches ``target``.

        For a marker whose exact spot inside its card is not fixed.
        """
        return self.find_color_in(region, target, tolerance) is not None

    def wait_color(self, x, y, target, tolerance=10, poll=0.5):
        while not self.see_color(x, y, target, tolerance):
            time.sleep(poll)

    # ---------------- Control ----------------

    def stop(self, msg="Script stopped"):
        raise StopScript(msg)


def _color_match(haystack, ref, box, color_threshold):
    """True when the content of ``box`` also matches ``ref`` in *colour*."""
    import cv2
    import numpy as np

    x1, y1, x2, y2 = box
    crop = haystack[y1:y2, x1:x2].astype(np.float32)
    tmpl = cv2.resize(ref, (x2 - x1, y2 - y1)).astype(np.float32)
    rms = np.sqrt(((crop - tmpl) ** 2).mean())
    return 1.0 - rms / 255.0 >= color_threshold


def _iou(a, b):
    """Intersection-over-union of two ``(x1, y1, x2, y2)`` boxes."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)
