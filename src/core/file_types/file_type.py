"""
Copyright (c) Cutleast
"""

from enum import auto
from typing import override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from PySide6.QtWidgets import QApplication

from core.mod_file.mod_file import ModFile
from core.string.types import String

from .interface.file import InterfaceFile
from .interface.string import InterfaceString
from .plugin.file import PluginFile
from .plugin.string import PluginString


class FileType(LocalizedEnum):
    """
    Enum for the file types that are supported by SSE-AT.
    """

    PluginFile = auto()
    """Traditional plugin files (.esp, .esm, .esl)."""

    InterfaceFile = auto()
    """Interface translation files (data/interface/translations/*_[language].txt)."""

    @override
    def get_localized_name(self) -> str:
        LOC_NAMES: dict[FileType, str] = {
            FileType.PluginFile: QApplication.translate("FileType", "Plugin File"),
            FileType.InterfaceFile: QApplication.translate(
                "FileType", "Interface File"
            ),
        }

        return LOC_NAMES[self]

    @override
    def get_localized_description(self) -> str:
        LOC_DESCS: dict[FileType, str] = {
            FileType.PluginFile: QApplication.translate(
                "FileType", "Traditional plugin files (.esp, .esm, .esl)."
            ),
            FileType.InterfaceFile: QApplication.translate(
                "FileType",
                "Interface translation files "
                "(data/interface/translations/*_[language].txt).",
            ),
        }

        return LOC_DESCS[self]

    def get_localized_filter_name(self) -> str:
        """
        Returns:
            str: Localized name for filtering this file type.
        """

        LOC_FILTERS: dict[FileType, str] = {
            FileType.PluginFile: QApplication.translate(
                "FileType", "Show plugin files (*.esp, *.esm, *.esl)"
            ),
            FileType.InterfaceFile: QApplication.translate(
                "FileType", "Show interface files (*.txt)"
            ),
        }

        return LOC_FILTERS[self]

    def get_file_type_cls(self) -> type[ModFile]:
        """
        Returns:
            type[ModFile]: The class for this file type.
        """

        CLASSES: dict[FileType, type[ModFile]] = {
            FileType.PluginFile: PluginFile,
            FileType.InterfaceFile: InterfaceFile,
        }

        return CLASSES[self]

    def get_string_type_cls(self) -> type[String]:
        """
        Returns:
            type[String]: The class of the strings for this file type.
        """

        CLASSES: dict[FileType, type[String]] = {
            FileType.PluginFile: PluginString,
            FileType.InterfaceFile: InterfaceString,
        }

        return CLASSES[self]
