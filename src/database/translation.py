"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import pickle
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import jstyleson as json
from qtpy.QtWidgets import QTreeWidgetItem

import plugin_interface
import utilities as utils


@dataclass
class Translation:
    """
    Class for mod translations.
    """

    name: str

    mod_id: int
    file_id: int | None
    version: str

    original_mod_id: int
    original_file_id: int
    original_version: str

    path: Path = None

    _original_path: Path = None

    strings: dict[str, list[utils.String]] = None
    """
    `{plugin name: list of strings}`
    """

    class Status(StrEnum):
        """
        Enum for different Statuses
        """

        Ok = "Ok"
        UpdateAvailable = "Update available"
        UpdateIgnored = "Update ignored"

    status: Status = None

    source: utils.Source = None

    timestamp: int = None

    tree_item: QTreeWidgetItem = None

    log = logging.getLogger("TranslationDatabase")

    def load_translation(self):
        """
        Loads strings from translation.
        """

        if self.strings is None:
            self.strings = {}

            translation_paths = list(self.path.glob("*.ats"))

            # Fix translation files that were generated outside of SSE-AT
            sys.modules["plugin_parser"] = plugin_interface
            sys.modules["plugin_parser.string"] = utils.string
            for translation_path in translation_paths:
                try:
                    with translation_path.open("rb") as file:
                        self.strings[translation_path.stem.lower()] = pickle.load(file)
                except EOFError as ex:
                    self.log.error(
                        f"Failed to load strings from database file {str(translation_path)!r}",
                        exc_info=ex,
                    )

            sys.modules.pop("plugin_parser.string")
            sys.modules.pop("plugin_parser")

            translation_paths = list(self.path.glob("*.json"))

            for translation_path in translation_paths:
                if translation_path.stem.lower() in self.strings:
                    continue

                try:
                    with open(
                        translation_path, "r", encoding="utf8"
                    ) as translation_file:
                        strings_data: list[dict[str, str]] = json.load(translation_file)

                    strings = [
                        utils.String.from_string_data(string_data)
                        for string_data in strings_data
                    ]

                    strings = list(set(strings))  # Remove duplicates
                    self.strings[translation_path.stem.lower()] = strings
                except Exception as ex:
                    self.log.error(
                        f"Failed to load strings from database file {str(translation_path)!r}",
                        exc_info=ex,
                    )

            self.optimize_translation()

    def save_translation(self):
        """
        Saves strings to folder.
        """

        if not self.path.is_dir():
            os.mkdir(self.path)

        for plugin_name, plugin_strings in self.strings.items():
            plugin_name = plugin_name.lower()
            plugin_strings = list(set(plugin_strings))  # Remove duplicates
            with open(self.path / (plugin_name + ".ats"), "wb") as file:
                pickle.dump(plugin_strings, file)

    def optimize_translation(self):
        """
        Optimizes translation by converting it from JSON files to pickle files
        if not already done.
        """

        json_files = list(self.path.glob("*.json"))

        if json_files:
            self.save_translation()

            for json_file in json_files:
                os.remove(json_file)

    def export_translation(self, path: Path):
        """
        Exports translation strings to `path`.
        """

        if not path.is_dir():
            os.makedirs(path)

        for plugin_name, plugin_strings in self.strings.items():
            plugin_folder = (
                path / "SKSE" / "Plugins" / "DynamicStringDistributor" / plugin_name
            )

            if not plugin_folder.is_dir():
                os.makedirs(plugin_folder)

            strings = [
                string.to_string_data()
                for string in plugin_strings
                if string.original_string != string.translated_string
                and string.translated_string
            ]

            translation_path = plugin_folder / "SSE-AT_exported.json"

            with translation_path.open("w", encoding="utf8") as translation_file:
                json.dump(strings, translation_file, indent=4, ensure_ascii=False)

    def __hash__(self):
        return hash((self.name, self.path))
