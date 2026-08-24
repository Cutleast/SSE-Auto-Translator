"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from enum import auto
from typing import override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from PySide6.QtWidgets import QApplication

from core.mod_file.mod_file import ModFile
from core.string.types import String

from .bestiary.file import BestiaryFile
from .bestiary.string import BestiaryString
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

    BestiaryFile = auto()
    """Dragonborn's Bestiary translation files (data/interface/creatures/**/*.json)"""

    @override
    def get_localized_name(self) -> str:
        match self:
            case FileType.PluginFile:
                return QApplication.translate("FileType", "Plugin File")
            case FileType.InterfaceFile:
                return QApplication.translate("FileType", "Interface File")
            case FileType.BestiaryFile:
                return QApplication.translate("FileType", "Dragonborn's Bestiary File")

    @override
    def get_localized_description(self) -> str:
        match self:
            case FileType.PluginFile:
                return QApplication.translate(
                    "FileType", "A traditional plugin file (.esp, .esm, .esl)."
                )
            case FileType.InterfaceFile:
                return QApplication.translate(
                    "FileType",
                    "An interface translation file "
                    "(data/interface/translations/*_[language].txt).",
                )
            case FileType.BestiaryFile:
                return QApplication.translate(
                    "FileType",
                    "A Dragonborn's Bestiary file (data/interface/creatures/**/*.json).",
                )

    def get_file_type_cls(self) -> type[ModFile]:
        """
        Returns:
            type[ModFile]: The class for this file type.
        """

        match self:
            case FileType.PluginFile:
                return PluginFile
            case FileType.InterfaceFile:
                return InterfaceFile
            case FileType.BestiaryFile:
                return BestiaryFile

    def get_string_type_cls(self) -> type[String]:
        """
        Returns:
            type[String]: The class of the strings for this file type.
        """

        match self:
            case FileType.PluginFile:
                return PluginString
            case FileType.InterfaceFile:
                return InterfaceString
            case FileType.BestiaryFile:
                return BestiaryString

    @classmethod
    def get_file_type(cls, mod_file: ModFile) -> FileType:
        """
        Returns:
            FileType: The file type for the given mod file.
        """

        match mod_file:
            case PluginFile():
                return FileType.PluginFile
            case InterfaceFile():
                return FileType.InterfaceFile
            case BestiaryFile():
                return FileType.BestiaryFile

        raise ValueError(f"Unknown mod file type: {type(mod_file)}")

    def get_file_dialog_filter(self) -> str:
        """
        Returns:
            str: Localized file name filter for a QFileDialog.
        """

        match self:
            case FileType.PluginFile:
                return FileType.PluginFile.get_localized_name() + " (*.esp *.esm *.esl)"
            case FileType.InterfaceFile:
                return FileType.InterfaceFile.get_localized_name() + " (*.txt)"
            case FileType.BestiaryFile:
                return FileType.BestiaryFile.get_localized_name() + " (*.json)"
