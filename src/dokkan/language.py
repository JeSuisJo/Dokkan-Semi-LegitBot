"""The game's language, and the reference images that change with it.

Dokkan prints its buttons and dialog titles in the account's language, so a few
references exist in several files. Coord entries always name the French one and
:func:`image` swaps in the variant the configured language needs, which keeps
``coords/*.json`` to one entry per screen element.
"""

from . import config

LANGUAGES = ("french", "english", "spanish", "german", "chinese", "korean")
LANGUAGE_LABELS = ("French", "English", "Spanish", "German", "Chinese", "Korean")

# Reference named in coords/ -> the file each language uses instead. A language
# absent from a row reads the same file as French.
VARIANTS = {
    "img/ok_button.png": {
        "chinese": "img/ok_button_asian.png",
        "korean": "img/ok_button_asian.png",
    },
    "img/restore_act_title.png": {
        "english": "img/restore_act_title_english.png",
        "spanish": "img/restore_act_title_spanish.png",
        "german": "img/restore_act_title_german.png",
        "chinese": "img/restore_act_title_asian.png",
        "korean": "img/restore_act_title_asian.png",
    },
}


def current():
    return config.get_config().get("language", LANGUAGES[0])


def image(path):
    """The file ``path`` becomes in the configured language."""
    return VARIANTS.get(path, {}).get(current(), path)


def files(path):
    """Every file ``path`` can resolve to, French included."""
    return {path, *VARIANTS.get(path, {}).values()}
