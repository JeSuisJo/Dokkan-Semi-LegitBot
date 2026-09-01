import glob
import json
import os

from . import language
from .paths import resolve

_COORDS_DIR = resolve("coords")


def _load():
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

    if "img" not in block:
        return block
    localised = language.image(block["img"])
    return block if localised == block["img"] else {**block, "img": localised}
