"""Shared project path definitions for the TESSERACT Python layer.

This module resolves paths relative to the repository layout so scripts do not
hardcode local filesystem locations. Importing this module ensures the standard
data directories exist.
"""

from pathlib import Path


# python/utils/paths.py -> python/utils -> python -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


for directory in (DATA_DIR, RAW_DIR, PROCESSED_DIR):
    directory.mkdir(parents=True, exist_ok=True)
