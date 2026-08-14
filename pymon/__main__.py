"""Main entry point for pymon."""
import os
import sys

# Support running as `python pymon/__main__.py` directly
if __name__ == "__main__":
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent not in sys.path:
        sys.path.insert(0, parent)

from pymon.tui import main

if __name__ == '__main__':
    main()