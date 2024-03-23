"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import jstyleson as json
from qtpy.QtWidgets import QTreeWidgetItem

from nm_api import Download
from utilities import String


@dataclass
class Translation:
    """
    Class for mod translations.
    """

    name: str

    mod_id: int
    file_id: int
    version: str

    original_mod_id: int
    original_file_id: int
    original_version: str

    path: Path = None

    _original_path: Path = None
    _download: Download = None

    strings: dict[str, list[String]] = None
    """
    `{plugin name: list of strings}`
    """

    class Status(StrEnum):
        """
        Enum for different Statuses
        """

        Ok = "Ok"
        WaitingForDownload = "Waiting for Download"
        Downloading = "Downloading"
        DownloadSuccess = "Download successful"
        DownloadFailed = "Download failed"
        UpdateAvailable = "Update available"
        UpdateIgnored = "Update ignored"
        Processing = "Processing"

    status: Status = None

    tree_item: QTreeWidgetItem = None

    def load_translation(self):
        """
        Loads strings from translation.
        """

        if self.strings is None:
            translation_paths = list(self.path.glob("*.json"))

            self.strings = {}
            for translation_path in translation_paths:
                with open(translation_path, "r", encoding="utf8") as translation_file:
                    strings_data: list[dict[str, str]] = json.load(translation_file)
                strings = [
                    String.from_string_data(string_data) for string_data in strings_data
                ]
                strings = list(set(strings))  # Remove duplicates
                self.strings[translation_path.stem.lower()] = strings

    def save_translation(self):
        """
        Saves strings to folder.
        """

        if not self.path.is_dir():
            os.mkdir(self.path)

        for plugin_name, plugin_strings in self.strings.items():
            plugin_name = plugin_name.lower()
            plugin_strings = list(set(plugin_strings))  # Remove duplicates
            string_data = [string.to_string_data() for string in plugin_strings]
            with open(
                self.path / (plugin_name + ".json"), "w", encoding="utf8"
            ) as file:
                json.dump(string_data, file, indent=4, ensure_ascii=False)

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
