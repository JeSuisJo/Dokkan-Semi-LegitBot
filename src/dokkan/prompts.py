from . import console


def ask_int(prompt, minimum=1):
    while True:
        answer = input(f"{prompt}").strip()
        try:
            value = int(answer)
        except ValueError:
            console.error("Please enter a valid number")
            continue
        if value < minimum:
            console.error(f"Please enter a number greater or equal to {minimum}")
            continue
        return value


def ask_text(prompt, default=""):
    answer = input(f"{prompt} [{default}]: ").strip()
    return answer or default


def _show_menu(prompt, labels):
    print(f"\n{prompt}")
    for i, label in enumerate(labels, 1):
        print(f"  [{i}] {label}")


def _index(answer, count):
    if answer.isdigit() and 1 <= int(answer) <= count:
        return int(answer)
    return None


def _out_of_range(count):
    console.error(f"Please enter a number between 1 and {count}")


def ask_from_list(prompt, options):
    _show_menu(prompt, options)
    while True:
        chosen = _index(input(f"Choice (1-{len(options)}): ").strip(), len(options))
        if chosen is not None:
            return chosen
        _out_of_range(len(options))


def ask_choice(prompt, options, default, labels=None):
    shown = labels or options
    _show_menu(prompt, shown)
    hint = shown[options.index(default)] if default in options else default
    while True:
        answer = input(f"Choice (1-{len(options)}) [{hint}]: ").strip()
        if not answer:
            return default
        chosen = _index(answer, len(options))
        if chosen is not None:
            return options[chosen - 1]
        _out_of_range(len(options))


def ask_yes_no(prompt):
    return ask_from_list(prompt, ["Yes", "No"]) == 1


def ask_many_from_list(prompt, options):
    _show_menu(prompt, options)
    while True:
        answer = input(f"Choices (1-{len(options)}, e.g. 1 3) []: ").strip()
        if not answer:
            return set()
        chosen = {_index(t, len(options)) for t in answer.replace(",", " ").split()}
        if None not in chosen:
            return chosen
        console.error(
            f"Please enter numbers between 1 and {len(options)}, separated by spaces"
        )
