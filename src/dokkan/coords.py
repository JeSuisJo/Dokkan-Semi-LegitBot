"""Named screen coordinates and reference images (the ``coords/`` folder).

One JSON file per feature plus ``common.json``, merged into a single flat
namespace at import time, so callers look names up globally: ``coords("home")``.

A block holds only what its name needs:

    "home":  {"tap": [540, 1800], "img": "img/home.png", "region": [0, 0, 200, 100]}
    "start": {"tap": [540, 960], "rgb": [255, 0, 0]}
    "list":  {"region": [0, 300, 1080, 1600], "swipe": [540, 1400, 540, 600, 400]}
"""

import glob
import json
import os

from . import language
from .paths import resolve

_COORDS_DIR = resolve("coords")


def _load():
    """Merge every ``coords/*.json`` file, rejecting duplicate names.

    A flat namespace means a name defined twice would silently shadow the
    other, so the clash fails loudly with both filenames.
    """
    merged = {}
    origin = {}
    for path in sorted(glob.glob(os.path.join(_COORDS_DIR, "*.json"))):
        filename = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            entries = json.load(f)
        for name, block in entries.items():
            if name in merged:
                raise ValueError(
                    f"Duplicate coord '{name}' defined in both "
                    f"'{origin[name]}' and '{filename}'"
                )
            merged[name] = block
            origin[name] = filename
    return merged


_COORDS = _load()


def coords(name):
    try:
        block = _COORDS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown coord '{name}' (not defined in coords/*.json)") from exc

    # Read per lookup, not once at import: the wizard can write the language
    # after this module is loaded.
    if "img" not in block:
        return block
    localised = language.image(block["img"])
    return block if localised == block["img"] else {**block, "img": localised}
