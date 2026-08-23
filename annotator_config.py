"""Eén plek voor host, poort, annotatie-root en skill-map.

Defaults zijn identiek aan de oude hardcoded waarden. Override alleen via env:
LUC_ANNOTATOR_PORT, LUC_ANNOTATOR_ROOT.
"""

import os

HOST = "127.0.0.1"
PORT = int(os.environ.get("LUC_ANNOTATOR_PORT", "8791"))
ROOT = os.path.expanduser(os.environ.get("LUC_ANNOTATOR_ROOT", "~/Desktop/annotaties"))
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
