#!/usr/bin/env python3
"""Deprecated alias of bin/show-annotations.py (kept until 1.1).

Thin wrapper: `python -m html_annotator show`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from html_annotator.cli import main

if __name__ == "__main__":
    sys.exit(main(["show"] + sys.argv[1:]))
