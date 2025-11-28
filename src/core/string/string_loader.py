"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from types import ModuleType

import sse_plugin_interface

from core import utilities
from core.string.string_status import StringStatus
from core.utilities.alias_unpickler import AliasUnpickler

from . import StringList, StringListModel, legacy_string
from .legacy_string import LegacyString
from .plugin_string import PluginString


class StringLoader:
    """
    Factory class for deserializing string objects by auto-detecting their type without
    discrimnator.
    """

    MODULE_ALIASES: dict[str, ModuleType] = {
        "core.database.string": legacy_string,
        "plugin_parser": sse_plugin_interface,
        "plugin_parser.string": legacy_string,
        "utilities": utilities,
        "utilities.string": legacy_string,
        "plugin_interface": sse_plugin_interface,
    }
    """Dict of module aliases required for deserialization of older translations."""

    CLASS_ALIASES: dict[str, str] = {
        "String": "LegacyString",
        "String.Status": "LegacyString.Status",
    }
    """Dict of class aliases required for deserialization of older translations."""

    log: logging.Logger = logging.getLogger("StringLoader")

    @classmethod
    def load_strings_from_json_file(cls, json_file_path: Path) -> StringList:
        """
        Loads strings from a JSON file.

        Args:
            json_file_path (Path): Path to the JSON file.

        Returns:
            StringList: List of strings.
        """

        return StringListModel.validate_json(json_file_path.read_bytes())

    @classmethod
    def load_strings_from_legacy_file(cls, legacy_ats_file_path: Path) -> StringList:
        """
        Deserializes and converts strings from a legacy .ats file to the new String
        class.

        Args:
            legacy_ats_file_path (Path): Path to the legacy .ats file.

        Returns:
            StringList: List of strings.
        """

        strings: list[LegacyString] = AliasUnpickler.load_from_file(
            legacy_ats_file_path, cls.MODULE_ALIASES, cls.CLASS_ALIASES
        )

        return list(map(cls.convert_legacy_string, strings))

    @classmethod
    def convert_legacy_string(cls, legacy_string: LegacyString) -> PluginString:
        """
        Converts a legacy string to the new PluginString class.

        Args:
            legacy_string (LegacyString): Legacy string to convert.

        Returns:
            PluginString: Converted PluginString object.
        """

        return PluginString(
            form_id=legacy_string.form_id,
            editor_id=legacy_string.editor_id,
            index=legacy_string.index,
            type=legacy_string.type,
            original=legacy_string.original_string,
            string=legacy_string.translated_string,
            status=cls.convert_legacy_status(legacy_string.status),
        )

    @classmethod
    def convert_legacy_status(cls, legacy_status: LegacyString.Status) -> StringStatus:
        """
        Converts the status of a legacy string to the new String class.

        Args:
            legacy_status (LegacyString.Status): Legacy status to convert.

        Returns:
            Status: Converted status.
        """

        return StringStatus(legacy_status.value)
