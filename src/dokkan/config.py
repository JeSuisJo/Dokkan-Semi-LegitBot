"""Single source of truth for user configuration (config.json).

Everything that reads or writes config.json goes through here: the file is
parsed once, kept in memory, and written back from that same dict.
"""

import json
import os

from .paths import CONFIG_FILE

_cache = None


def _load():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Warning: invalid JSON in config.json")
        return {}


def exists():
    """True when config.json is on disk (false on a fresh install)."""
    return os.path.exists(CONFIG_FILE)


def get_config():
    """Return the cached config dict, loading it on first use."""
    global _cache
    if _cache is None:
        _cache = _load()
    return _cache


def reload():
    """Drop the cache so the next :func:`get_config` re-reads the file."""
    global _cache
    _cache = None
    return get_config()


def save(key, value):
    """Persist one key to config.json and to the live config."""
    save_many({key: value})


def save_many(values):
    """Persist several keys to config.json and to the live config.

    A write failure is not fatal: the values still apply to this session.
    """
    data = get_config()
    data.update(values)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except OSError as exc:
        print(f"Warning: could not save to config.json ({exc})")
