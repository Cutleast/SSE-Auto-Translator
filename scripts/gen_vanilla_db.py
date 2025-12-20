"""
Copyright (c) Cutleast

This script generates the Vanilla database by extracting all strings and their
translations for all supported languages from the base game files.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.utilities.db_gen.main import DbGen

SUPPORTED_LANGUAGES: list[str] = [
    "chinese",
    "french",
    "german",
    "italian",
    "japanese",
    "polish",
    "russian",
    "spanish",
]
"""List of all languages supported by the game."""

logging.basicConfig(level=logging.INFO)
log: logging.Logger = logging.getLogger()


def run(args: argparse.Namespace) -> None:
    game_folder = Path(args.game_folder)
    data_folder = game_folder / "data"
    output_path = Path(args.output_path or "./DbGen-Output")

    if not data_folder.is_dir():
        raise ValueError(f"Invalid game folder: {game_folder}")

    output_path.mkdir(parents=True, exist_ok=True)

    db_gen = DbGen()

    for language in SUPPORTED_LANGUAGES:
        log.info(f"Generating database for language {language}...")
        db_gen.create_database(
            data_folder, data_folder, language, output_path / language
        )

    log.info(f"Database successfully generated at '{output_path}'.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generates the Vanilla database for all supported languages."
    )
    parser.add_argument(
        "game_folder",
        type=str,
        help=(
            "Path to the game folder (e.g. C:\\Program Files (x86)\\Steam\\steamapps"
            "\\common\\Skyrim Special Edition)."
        ),
    )
    parser.add_argument(
        "--output-path",
        type=str,
        help="Path to the output folder. Defaults to ./DbGen-Output.",
    )

    run(parser.parse_args())


if __name__ == "__main__":
    main()
