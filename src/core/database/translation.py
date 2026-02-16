"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, override

from cutleast_core_lib.core.filesystem.scanner import DirectoryScanner
from pydantic import BaseModel, Field, ValidationError

from core.string.string_utils import StringUtils
from core.string.types import StringList
from core.translation_provider.cdt_api.cdt_id import CdtModId
from core.translation_provider.mod_id import ModId
from core.translation_provider.nm_api.nxm_id import NxmModId
from core.translation_provider.source import Source

from .translation_service import TranslationService


class Translation(BaseModel):
    """
    Class for mod translations.
    """

    name: str
    """The name of the translation."""

    path: Path = Field(exclude=True)
    """The path to the translation."""

    mod_id: Optional[ModId] = None
    """The mod identifier of the translation at its source."""

    version: Optional[str] = None
    """The version of the translation at its source."""

    strings_: Optional[dict[Path, StringList]] = Field(default=None, exclude=True)
    """Map of mod file names to list of strings."""

    source: Source = Source.Local
    """The source of the translation."""

    timestamp: int = Field(default_factory=lambda: int(time.time()))
    """The creation timestamp of the translation."""

    def to_index_data(self) -> dict[str, Any]:
        """
        Generates index data for the index.json file in the database.

        Returns:
            dict[str, Any]: Index data.
        """

        return self.model_dump(mode="json", exclude_defaults=True)

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

        try:
            data: dict[str, Any] = index_data.copy()
            data["path"] = database_path / data["name"]

            return Translation.model_validate(data)
        except ValidationError:
            pass

        name: str = index_data["name"]
        raw_mod_id: Optional[int] = index_data.pop("mod_id", None)
        raw_file_id: Optional[int] = index_data.pop("file_id", None)
        raw_orig_mod_id: Optional[int] = index_data.pop("original_mod_id", None)

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

        mod_id: Optional[ModId] = None
        if raw_mod_id and raw_file_id and source == Source.NexusMods:
            mod_id = NxmModId(mod_id=raw_mod_id, file_id=raw_file_id)
        elif raw_mod_id and source == Source.Confrerie and raw_orig_mod_id is not None:
            mod_id = CdtModId(mod_id=raw_mod_id, nm_mod_id=raw_orig_mod_id)

        return Translation(
            path=translation_path, mod_id=mod_id, **index_data, source=source
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

        if self.strings_ is None:
            self.strings_ = TranslationService.load_translation_strings(self.path)

        return self.strings_

    @strings.setter
    def strings(self, strings: dict[Path, StringList]) -> None:
        self.strings_ = strings

    @lru_cache
    def get_size(self) -> int:
        """
        Returns the size of the translation in bytes.

        Returns:
            int: Size of the translation in bytes.
        """

        return DirectoryScanner.get_folder_size(self.path)

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
