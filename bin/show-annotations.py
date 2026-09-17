#!/usr/bin/env python3
"""Thin wrapper: `python -m html_annotator show`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from html_annotator.cli import main

if __name__ == "__main__":
    sys.exit(main(["show"] + sys.argv[1:]))
