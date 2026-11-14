"""
Copyright (c) Cutleast
"""

from pathlib import Path

TESTS_PATH: Path = Path(__file__).resolve().parent.parent
"""The root folder of the test suite."""

PROJECT_PATH: Path = TESTS_PATH.parent
"""The root folder of the project."""

DATA_PATH: Path = TESTS_PATH / "data"
"""The folder with the (read-only) test data."""

RES_PATH: Path = DATA_PATH / "res"
"""
The folder with the application resources for tests. It contains a small vanilla
translation database instead of the full one shipped with the application.
"""

DICTIONARY_PATH: Path = PROJECT_PATH / "res" / "hunspell"
"""The (read-only) folder with the Hunspell dictionaries of the application."""
