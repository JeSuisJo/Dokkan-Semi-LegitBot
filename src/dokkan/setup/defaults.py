"""Default config values and the option lists the wizard offers."""

# Booleans are stored as real JSON booleans; the labels are display only.
BOOLEAN = (True, False)
BOOLEAN_LABELS = ("Yes", "No")

# Used as the pre-selected answer of every question, and written as-is for the
# keys the wizard never asks about.
DEFAULTS = {
    # Resolved and saved by the ADB driver before each run, so never asked.
    "device_id": "",
    "language": "french",
    "use_meat_first": False,
    "use_dragon_stones": False,
}
