"""Which refill the user allows, and what to do when they allow none."""

from .. import config
from .. import screen


def food_first():
    return bool(config.get_config().get("use_meat_first"))


def dragon_stones():
    return bool(config.get_config().get("use_dragon_stones"))


def refuse():
    """Abort the run: out of ACT, with every refill turned off in config.json."""
    screen.stop(
        "Out of ACT, and both use_meat_first and use_dragon_stones are false "
        "in config.json"
    )
