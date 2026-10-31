"""
Copyright (c) Cutleast
"""

import logging
import time
from pathlib import Path
from typing import Optional, TypeAlias

from core.file_types.plugin.string import PluginString
from core.string.types import StringList

ResolvedString: TypeAlias = tuple[PluginString, Path]
"""A resolved plugin string and the mod file path that it originates from."""

_IndexKey: TypeAlias = tuple[str, str]


class ReferenceResolver:
    """
    Resolves records referenced by their form ID to their strings, without loading the
    plugins that define the records. This also works for records from masters like
    Skyrim.esm, as their strings are part of the translation database.
    """

    __sources: list[dict[Path, StringList]]
    __index: Optional[dict[_IndexKey, list[ResolvedString]]]

    log: logging.Logger = logging.getLogger("ReferenceResolver")

    def __init__(self, sources: list[dict[Path, StringList]]) -> None:
        """
        Args:
            sources (list[dict[Path, StringList]]):
                Strings per mod file path to resolve references with, in descending
                priority. Strings from the first source that contains a string are used.
        """

        self.__sources = sources
        self.__index = None

    @staticmethod
    def get_record_id(form_id: int, plugin_name: str, masters: list[str]) -> str:
        """
        Creates a load order-independent record ID from a raw plugin-local form ID,
        matching `PluginString.record_id`.

        Args:
            form_id (int): Raw form ID as stored in the plugin.
            plugin_name (str): Name of the plugin containing the form ID.
            masters (list[str]): Masters of the plugin containing the form ID.

        Returns:
            str: The record ID.
        """

        master_index: int = form_id >> 24
        master: str = (
            masters[master_index] if master_index < len(masters) else plugin_name
        )

        return f"{form_id & 0xFFFFFF:06X}|{master}".lower()

    def resolve(self, record_id: str, string_type: str) -> list[ResolvedString]:
        """
        Gets the strings of a specific type from a record.

        Args:
            record_id (str): Record ID as returned by `get_record_id()`.
            string_type (str): Type of the strings, for eg. "NPC_ FULL".

        Returns:
            list[ResolvedString]: The strings ordered by their index.
        """

        if self.__index is None:
            self.__index = self.__build_index()

        return self.__index.get((record_id, string_type), [])

    def __build_index(self) -> dict[_IndexKey, list[ResolvedString]]:
        """
        Indexes all plugin strings of the sources by their record and type.

        Returns:
            dict[_IndexKey, list[ResolvedString]]: The strings per record ID and type.
        """

        start: float = time.time()

        seen: set[tuple[str, str, Optional[int]]] = set()
        index: dict[_IndexKey, list[ResolvedString]] = {}
        for source in self.__sources:
            for mod_file_path, strings in source.items():
                for string in strings:
                    if not isinstance(string, PluginString):
                        continue

                    key: tuple[str, str, Optional[int]] = (
                        string.record_id,
                        string.type,
                        string.index,
                    )
                    if key in seen:
                        continue

                    seen.add(key)
                    index.setdefault((string.record_id, string.type), []).append(
                        (string, mod_file_path)
                    )

        for resolved_strings in index.values():
            resolved_strings.sort(
                key=lambda item: item[0].index if item[0].index is not None else -1
            )

        self.log.debug(
            f"Indexed {len(seen)} string(s) for resolving references in "
            f"{time.time() - start:.2f} second(s)."
        )

        return index
