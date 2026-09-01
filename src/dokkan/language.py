from . import config

LANGUAGES = ("french", "english", "spanish", "german", "chinese", "korean")
LANGUAGE_LABELS = ("French", "English", "Spanish", "German", "Chinese", "Korean")

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
    return VARIANTS.get(path, {}).get(current(), path)


def files(path):
    return {path, *VARIANTS.get(path, {}).values()}
