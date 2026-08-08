"""Create config.json on a fresh install, backfill what is missing on upgrade.

One ordered list of questions (:data:`QUESTIONS`) serves three cases, checked
before every start:

* **no config.json**: ask everything and write the file;
* **a key is absent** (a release added an option): ask only that one;
* **a key holds a value no feature understands** (a typo, or an option that
  disappeared): show it and ask again.

Without this the script runs on silent fallbacks. To expose a new option, add
one :class:`Question` row and its default in :mod:`.defaults`; all three cases
pick it up.
"""

import os
from dataclasses import dataclass

from .. import config
from .. import console
from ..language import LANGUAGES, LANGUAGE_LABELS
from ..paths import CONFIG_FILE
from ..prompts import ask_choice
from .defaults import BOOLEAN, BOOLEAN_LABELS, DEFAULTS


@dataclass(frozen=True)
class Question:
    """One config key: what to ask, and which values are accepted."""

    key: str
    prompt: str
    options: tuple
    labels: tuple = None

    def ask(self, current):
        default = current if current in self.options else DEFAULTS[self.key]
        return ask_choice(self.prompt, list(self.options), default, self.labels)


QUESTIONS = [
    Question(
        "language",
        "Which language is the game set to?",
        LANGUAGES,
        LANGUAGE_LABELS,
    ),
    Question(
        "use_meat_first",
        "Restore stamina with food (meat)?",
        BOOLEAN,
        BOOLEAN_LABELS,
    ),
    Question(
        "use_dragon_stones",
        "Restore stamina with Dragon Stones when there is no food?",
        BOOLEAN,
        BOOLEAN_LABELS,
    ),
]


def ensure_config():
    """Make sure config.json exists and every key holds a value we understand."""
    first_run = not config.exists()
    data = config.get_config()
    pending = [q for q in QUESTIONS if data.get(q.key) not in q.options]

    if not first_run and not pending:
        return

    console.banner(
        "First run: configuration" if first_run else "New options to configure"
    )
    answers = {q.key: q.ask(data.get(q.key)) for q in pending}
    # Backfill the keys nobody asks about, added by a later release.
    answers.update(
        {k: v for k, v in DEFAULTS.items() if k not in data and k not in answers}
    )

    config.save_many(answers)
    console.info(f"\nSaved to {os.path.relpath(CONFIG_FILE)}\n")
