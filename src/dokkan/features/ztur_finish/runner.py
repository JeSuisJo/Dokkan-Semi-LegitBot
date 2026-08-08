"""ZTUR Finish: run the stage until the enemy reaches the level you want."""

from ... import auto_mode, console, prompts, ztur
from . import fight

TITLE = "ZTUR Finish"

POPUPS = ("finish_too_many_friends_ok", "finish_friend_request_ok", "finish_back")

# Replays allowed after a defeat, counted per enemy level: losing four times in
# a row means the team cannot take that level, and the enemy only gets stronger.
MAX_RETRIES = 3


def prepare():
    console.banner(TITLE)
    target = prompts.ask_int("At which level do you want to finish? ", minimum=1)
    enemy = prompts.ask_int("What is the enemy level now? ", minimum=1)
    return (target, enemy)


def run(target_level, enemy_level):
    # Each clear pushes the enemy up one level, and the target level has to be
    # played too, hence the +1.
    runs = (target_level + 1) - enemy_level
    if runs < 1:
        console.warn(f"Enemy level {enemy_level} is already past {target_level}")
        return

    done = 0
    retries = 0
    auto = True
    while done < runs:
        lines = [f"Run {done + 1}/{runs}", f"Target level {target_level}"]
        if retries:
            lines.append(f"Retry {retries}/{MAX_RETRIES}")
        console.banner(TITLE, *lines)

        ztur.reach(*POPUPS)
        fight.launch()
        if auto:
            auto_mode.enable(auto_mode.BATTLE)
            auto = False
        died = fight.wait_for_clear()
        ztur.reach(*POPUPS)

        if not died:
            done += 1
            retries = 0
            continue

        retries += 1
        if retries > MAX_RETRIES:
            console.warn(
                f"Lost {retries} times on the same level, stopping at run "
                f"{done + 1}/{runs}"
            )
            return

    console.banner(TITLE, f"Enemy level {target_level} reached")
