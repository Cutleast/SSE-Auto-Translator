"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, override

from pydantic import BaseModel, Field
from PySide6.QtWidgets import QApplication

from core.database.translation_service import TranslationService
from core.string import StringList
from core.string.string_utils import StringUtils
from core.translation_provider.mod_id import ModId
from core.translation_provider.source import Source
from core.utilities.filesystem import get_folder_size
from core.utilities.localized_enum import LocalizedEnum


class Translation(BaseModel):
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

    mod_id: Optional[ModId] = None
    """
    The mod identifier of the translation at its source.
    """

    version: Optional[str] = None
    """
    The version of the translation at its source.
    """

    original_mod_id: Optional[ModId] = None
    """
    The mod id of the original mod.
    """

    original_version: Optional[str] = None
    """
    The version of the original mod.
    """

    _strings: Optional[dict[Path, StringList]] = None
    """
    Map of mod file names to list of strings.
    """

    class Status(LocalizedEnum):
        """
        Enum for different Statuses
        """

        Ok = "Ok"
        UpdateAvailable = "Update available"
        UpdateIgnored = "Update ignored"

        @override
        def get_localized_name(self) -> str:
            locs: dict[Translation.Status, str] = {
                Translation.Status.Ok: QApplication.translate("Translation", "Ok"),
                Translation.Status.UpdateAvailable: QApplication.translate(
                    "Translation", "Update available"
                ),
                Translation.Status.UpdateIgnored: QApplication.translate(
                    "Translation", "Update ignored"
                ),
            }

            return locs[self]

        @override
        def get_localized_description(self) -> str:
            locs: dict[Translation.Status, str] = {
                Translation.Status.Ok: QApplication.translate("Translation", "Ok"),
                Translation.Status.UpdateAvailable: QApplication.translate(
                    "Translation", "An update is available for the translation."
                ),
                Translation.Status.UpdateIgnored: QApplication.translate(
                    "Translation", "Available updates have been ignored."
                ),
            }

            return locs[self]

    status: Status = Status.Ok
    """
    The (update) status of the translation.
    """

    source: Source = Source.Local
    """
    The source of the translation.
    """

    timestamp: int = Field(default_factory=lambda: int(time.time()))
    """
    The install timestamp of the translation.
    """

    def to_index_data(self) -> dict[str, Any]:
        """
        Generates index data for the index.json file in the database.

        Returns:
            dict[str, Any]: Index data.
        """

        return {
            "name": self.name,
            "mod_id": self.mod_id.mod_id if self.mod_id else None,
            "file_id": self.mod_id.file_id if self.mod_id else None,
            "version": self.version,
            "original_mod_id": (
                self.original_mod_id.mod_id if self.original_mod_id else None
            ),
            "original_file_id": (
                self.original_mod_id.file_id if self.original_mod_id else None
            ),
            "original_version": self.original_version,
            "source": self.source.name,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_index_data(index_data: dict[str, Any], database_path: Path) -> Translation:
        """
        Gets a Translation object from the specified index data.

        Args:
            index_data (dict[str, Any]): Entry from the database's index.json file.
            database_path (Path): The path to the database.

        Returns:
            Translation: Translation object.
        """

        name: str = index_data["name"]
        raw_mod_id: Optional[int] = index_data.pop("mod_id", None)
        raw_file_id: Optional[int] = index_data.pop("file_id", None)
        mod_id: Optional[ModId] = None
        if raw_mod_id:
            mod_id = ModId(mod_id=raw_mod_id, file_id=raw_file_id)

        raw_orig_mod_id: Optional[int] = index_data.pop("original_mod_id", None)
        raw_orig_file_id: Optional[int] = index_data.pop("original_file_id", None)
        orig_mod_id: Optional[ModId] = None
        if raw_orig_mod_id:
            orig_mod_id = ModId(mod_id=raw_orig_mod_id, file_id=raw_orig_file_id)

        translation_path: Path = database_path / name
        source_name: str = index_data.pop("source", "")
        source: Optional[Source] = Source.get(source_name)

        if source is None:
            if raw_mod_id and raw_file_id:
                source = Source.NexusMods
            elif raw_mod_id:
                source = Source.Confrerie
            else:
                source = Source.Local

        return Translation(
            path=translation_path,
            mod_id=mod_id,
            original_mod_id=orig_mod_id,
            **index_data,
            source=source,
        )

    @staticmethod
    def create(
        name: str, path: Path, strings: Optional[dict[Path, StringList]] = None
    ) -> Translation:
        """
        Creates a new translation.

        Args:
            name (str): The name of the translation.
            path (Path): The path to the translation's folder.
            strings (Optional[dict[Path, StringList]], optional):
                The initial strings of the translation. Defaults to None.

        Returns:
            Translation: Created translation.
        """

        translation = Translation(name=name, path=path)
        if strings is not None:
            translation.strings = strings
        return translation

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
        return hash(self.id)

    @property
    def strings(self) -> dict[Path, StringList]:
        """
        List of strings for each mod file name.
        """

        if self._strings is None:
            self._strings = TranslationService.load_translation_strings(self.path)

        return self._strings or {}

    @strings.setter
    def strings(self, strings: dict[Path, StringList]) -> None:
        self._strings = strings

    @lru_cache
    def get_size(self) -> int:
        """
        Returns the size of the translation in bytes.

        Returns:
            int: Size of the translation in bytes.
        """

        return get_folder_size(self.path)

    @property
    def size(self) -> int:
        """
        Returns the size of the translation in bytes.

        Returns:
            int: Size of the translation in bytes.
        """

        return self.get_size()

    def remove_duplicates(self, save: bool = True) -> None:
        """
        Removes duplicate strings from the translation.

        Args:
            save (bool, optional): Whether to save the translation. Defaults to True.
        """

        for modfile_name, modfile_strings in self.strings.items():
            self.strings[modfile_name] = StringUtils.unique(modfile_strings)

        if save:
            self.save()

    def save(self) -> None:
        """
        Saves the translation.
        """

        TranslationService.save_translation_strings(self.path, self.strings)
