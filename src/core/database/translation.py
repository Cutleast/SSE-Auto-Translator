"""
Copyright (c) Cutleast
"""

import logging
import os
import pickle
import sys
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional, override

import jstyleson as json

from core import plugin_interface, utilities
from core.database import string
from core.database.string import String
from core.translation_provider.source import Source
from core.utilities.path import Path


@dataclass(kw_only=True)
class Translation:
    """
    Class for mod translations.
    """

    name: str
    """
    The name of the translation.
    """

    path: Path
    """
    The path to the translation.
    """

    mod_id: int = field(default=0)
    """
    The mod id of the translation at its source.
    """

    file_id: Optional[int] = None
    """
    The file id of the translation at its source.

    (Nexus Mods only)
    """

    version: str = field(default="")
    """
    The version of the translation at its source.
    """

    original_mod_id: int = field(default=0)
    """
    The mod id of the original mod.
    """

    original_file_id: int = field(default=0)
    """
    The file id of the original mod.
    """

    original_version: str = field(default="")
    """
    The version of the original mod.
    """

    _strings: Optional[dict[str, list[String]]] = None
    """
    Map of plugin names to list of strings.
    """

    class Status(StrEnum):
        """
        Enum for different Statuses
        """

        Ok = "Ok"
        UpdateAvailable = "Update available"
        UpdateIgnored = "Update ignored"

    status: Optional[Status] = field(default=Status.Ok)
    """
    The (update) status of the translation.
    """

    source: Optional[Source] = field(default=Source.Local)
    """
    The source of the translation.
    """

    timestamp: Optional[int] = field(default_factory=lambda: int(time.time()))
    """
    The install timestamp of the translation.
    """

    log: logging.Logger = logging.getLogger("TranslationDatabase")

    def load_translation(self) -> None:
        """
        Loads strings from translation.
        """

        if self._strings is None:
            self._strings = {}

            translation_paths = list(self.path.glob("*.ats"))

            # Fix translation files that were generated outside of SSE-AT
            # TODO: Improve this
            sys.modules["plugin_parser"] = plugin_interface
            sys.modules["plugin_parser.string"] = string
            sys.modules["utilities"] = utilities
            sys.modules["utilities.string"] = string
            sys.modules["plugin_interface"] = plugin_interface
            for translation_path in translation_paths:
                try:
                    with translation_path.open("rb") as file:
                        self._strings[translation_path.stem.lower()] = pickle.load(file)
                except EOFError as ex:
                    self.log.error(
                        f"Failed to load strings from database file {str(translation_path)!r}",
                        exc_info=ex,
                    )

            sys.modules.pop("plugin_parser.string")
            sys.modules.pop("plugin_parser")
            sys.modules.pop("utilities")
            sys.modules.pop("utilities.string")
            sys.modules.pop("plugin_interface")

            translation_paths = list(self.path.glob("*.json"))

            for translation_path in translation_paths:
                if translation_path.stem.lower() in self._strings:
                    continue

                try:
                    with open(
                        translation_path, "r", encoding="utf8"
                    ) as translation_file:
                        strings_data: list[dict[str, str]] = json.load(translation_file)

                    strings = [
                        String.from_string_data(string_data)
                        for string_data in strings_data
                    ]

                    self._strings[translation_path.stem.lower()] = String.unique(
                        strings
                    )
                except Exception as ex:
                    self.log.error(
                        f"Failed to load strings from database file {str(translation_path)!r}",
                        exc_info=ex,
                    )

            self.optimize_translation()

    def save_translation(self) -> None:
        """
        Saves strings to folder.
        """

        if self._strings is None:
            return

        if not self.path.is_dir():
            os.mkdir(self.path)

        for plugin_name, plugin_strings in self._strings.items():
            plugin_name = plugin_name.lower()
            with open(self.path / (plugin_name + ".ats"), "wb") as file:
                pickle.dump(String.unique(plugin_strings), file)

    def optimize_translation(self) -> None:
        """
        Optimizes translation by converting it from JSON files to pickle files
        if not already done.
        """

        json_files = list(self.path.glob("*.json"))

        if json_files:
            self.save_translation()

            for json_file in json_files:
                os.remove(json_file)

    def to_index_data(self) -> dict[str, Any]:
        """
        Generates index data for the index.json file in the database.

        Returns:
            dict[str, Any]: Index data.
        """

        return {
            "name": self.name,
            "mod_id": self.mod_id,
            "file_id": self.file_id,
            "version": self.version,
            "original_mod_id": self.original_mod_id,
            "original_file_id": self.original_file_id,
            "original_version": self.original_version,
            "source": self.source.name if self.source is not None else None,
            "timestamp": self.timestamp,
        }

    @property
    def id(self) -> str:
        """
        Generates a unique id for the translation.

        Included attributes:
        - `name`
        - `path`
        """

        return f"{self.name}###{self.path}".lower()

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.path))

    @property
    def strings(self) -> dict[str, list[String]]:
        """
        List of strings for each plugin name.
        """

        if self._strings is None:
            self.load_translation()

        return self._strings or {}

    @strings.setter
    def strings(self, strings: dict[str, list[String]]) -> None:
        self._strings = strings

    def remove_duplicates(self, save: bool = True) -> None:
        """
        Removes duplicate strings from the translation.

        Args:
            save (bool, optional): Whether to save the translation. Defaults to True.
        """

        for plugin_name, plugin_strings in self.strings.items():
            self.strings[plugin_name] = String.unique(plugin_strings)

        if save:
            self.save_translation()
