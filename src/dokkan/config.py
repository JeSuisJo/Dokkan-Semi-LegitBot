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
    return os.path.exists(CONFIG_FILE)


def get_config():
    global _cache
    if _cache is None:
        _cache = _load()
    return _cache


def reload():
    global _cache
    _cache = None
    return get_config()


def save(key, value):
    save_many({key: value})


def save_many(values):
    data = get_config()
    data.update(values)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except OSError as exc:
        print(f"Warning: could not save to config.json ({exc})")
