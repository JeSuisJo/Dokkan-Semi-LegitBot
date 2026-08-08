"""Launcher kept at the project root so `python main.py` still works.

The package itself lives in `src/dokkan`; install it with `pip install -e .`
to use `python -m dokkan` instead.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from dokkan.app import main  # noqa: E402

if __name__ == "__main__":
    main()
