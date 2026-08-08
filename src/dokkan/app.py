"""Entry point: check the config, then open the menu."""

from .cli import main as menu
from .setup import ensure_config


def main():
    ensure_config()
    menu()


if __name__ == "__main__":
    main()
