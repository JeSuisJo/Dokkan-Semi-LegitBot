"""Auto Level: replay the stage the team selection screen is showing."""

import time

from ... import auto_mode, console, prompts
from . import act, finish, launch

TITLE = "Auto Level"

BETWEEN_RUNS = 2.0


def prepare():
    console.banner(TITLE)
    runs = prompts.ask_int("How many times to repeat the level? ", minimum=1)
    return (runs,)


def run(runs=1):
    for index in range(1, runs + 1):
        console.banner(TITLE, f"Run {index}/{runs}")

        launch.launch()
        if index == 1:
            auto_mode.enable(auto_mode.BATTLE, auto_mode.NAVIGATION)

        finish.wait_for_end(replay=index < runs)
        act.settle()

        console.info(f"\nRun {index}/{runs} completed")
        if index < runs:
            time.sleep(BETWEEN_RUNS)

    console.banner(TITLE, f"All {runs} level(s) completed")
