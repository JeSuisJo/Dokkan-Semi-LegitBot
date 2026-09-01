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
    first_run = not config.exists()
    data = config.get_config()
    pending = [q for q in QUESTIONS if data.get(q.key) not in q.options]

    if not first_run and not pending:
        return

    console.banner(
        "First run: configuration" if first_run else "New options to configure"
    )
    answers = {q.key: q.ask(data.get(q.key)) for q in pending}
    answers.update(
        {k: v for k, v in DEFAULTS.items() if k not in data and k not in answers}
    )

    config.save_many(answers)
    console.info(f"\nSaved to {os.path.relpath(CONFIG_FILE)}\n")
