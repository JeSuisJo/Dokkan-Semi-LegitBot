"""ZTUR Retry: farm bronze, silver, gold and rainbow medals in that order."""

import time

from ... import console, prompts
from . import fight, medals

TITLE = "ZTUR Retry"

PAUSE = 0.4


def prepare():
    console.banner(TITLE)
    characters = prompts.ask_int("How many characters have a sub ZTUR? ", minimum=1)
    skipped = prompts.ask_many_from_list(
        "Which medals are already done? (nothing = farm them all)",
        [medal.label for medal in medals.MEDALS],
    )
    wanted = tuple(
        medal for i, medal in enumerate(medals.MEDALS, 1) if i not in skipped
    )
    return (characters, wanted)


def run(characters=1, wanted=medals.MEDALS):
    if not wanted:
        console.warn("Every medal was skipped, nothing to farm")
        return

    auto = True
    for medal in wanted:
        _farm(medal, characters, auto)
        auto = False

    farmed = ", ".join(medal.label for medal in wanted)
    console.banner(TITLE, f"{farmed} farmed for {characters} character(s)")


def _farm(medal, characters, auto=False):
    medals.select(medal)

    total = medal.runs * characters
    done = 0
    while done < total:
        console.banner(TITLE, f"{medal.label} medal run {done + 1}/{total}")
        if not fight.run_once(auto):
            done += 1
        auto = False
        time.sleep(PAUSE)
