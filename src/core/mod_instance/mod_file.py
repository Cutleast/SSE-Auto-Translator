"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, override

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from core.utilities.base_enum import BaseEnum
from core.utilities.path import Path


@dataclass
class ModFile:
    """
    Dataclass for translatable mod files.
    """

    name: str
    """
    The filename of this file.
    """

    path: Path
    """
    The full path to the file in its mod instance.
    """

    class Status(IntEnum, BaseEnum):
        """
        Enum for different Status.
        """

        NoneStatus = -1
        """
        None Status (no color).
        """

        NoStrings = 0
        """
        File has no Strings (no color).
        """

        IsTranslated = 1
        """
        File is already in target language (green).
        """

        TranslationInstalled = 2
        """
        Translation for file is already installed in Database (green).
        """

        TranslationAvailableInDatabase = 3
        """
        Translation for file is available in Database (green).
        """

        TranslationAvailableOnline = 4
        """
        Translation for file is available online at Nexus Mods or Confrérie des Traducteurs (cyan).
        """

        TranslationIncomplete = 5
        """
        Translation for file is installed but incomplete (magenta).
        """

        RequiresTranslation = 6
        """
        File has Strings and requires translation (yellow).
        """

        NoTranslationAvailable = 7
        """
        No Translation for file at Nexus Mods or in Database (red).
        """

        @classmethod
        def get_color(cls, status: "ModFile.Status") -> QColor | None:
            COLORS: dict["ModFile.Status", Optional[QColor]] = {
                cls.NoneStatus: None,
                cls.NoStrings: None,
                cls.IsTranslated: QColor.fromString("#8be248"),
                cls.TranslationInstalled: QColor.fromString("#8be248"),
                cls.TranslationIncomplete: QColor.fromString("#c24cd4"),
                cls.TranslationAvailableInDatabase: QColor.fromString("#8be248"),
                cls.TranslationAvailableOnline: QColor.fromString("#51c6d9"),
                cls.RequiresTranslation: QColor.fromString("#e9e042"),
                cls.NoTranslationAvailable: QColor.fromString("#d74343"),
            }

            return COLORS[status]

        def get_localized_name(self) -> str:
            LOC_NAMES: dict["ModFile.Status", str] = {
                ModFile.Status.NoneStatus: QApplication.translate(
                    "mod_file", "No Status (No Color)"
                ),
                ModFile.Status.NoStrings: QApplication.translate(
                    "mod_file", "File has no Strings (No Color)"
                ),
                ModFile.Status.IsTranslated: QApplication.translate(
                    "mod_file", "File is already in target language"
                ),
                ModFile.Status.TranslationInstalled: QApplication.translate(
                    "mod_file", "Translation for file is already installed in Database"
                ),
                ModFile.Status.TranslationIncomplete: QApplication.translate(
                    "mod_file", "Translation for file is installed but incomplete"
                ),
                ModFile.Status.TranslationAvailableInDatabase: QApplication.translate(
                    "mod_file", "Translation for file is available in Database"
                ),
                ModFile.Status.TranslationAvailableOnline: QApplication.translate(
                    "mod_file", "Translation for file is available online"
                ),
                ModFile.Status.RequiresTranslation: QApplication.translate(
                    "mod_file", "File has Strings and requires translation"
                ),
                ModFile.Status.NoTranslationAvailable: QApplication.translate(
                    "mod_file",
                    "No Translation for file available online or in Database",
                ),
            }

            return LOC_NAMES[self]

        def get_localized_filter_name(self) -> str:
            LOC_NAMES: dict["ModFile.Status", str] = {
                ModFile.Status.NoneStatus: QApplication.translate(
                    "mod_file", "No stateless files"
                ),
                ModFile.Status.NoStrings: QApplication.translate(
                    "mod_file", "Show files without strings"
                ),
                ModFile.Status.IsTranslated: QApplication.translate(
                    "mod_file", "Show files that are already in target language"
                ),
                ModFile.Status.TranslationInstalled: QApplication.translate(
                    "mod_file", "Show files with an installed translation"
                ),
                ModFile.Status.TranslationIncomplete: QApplication.translate(
                    "mod_file",
                    "Show files with an installed but incomplete translation",
                ),
                ModFile.Status.TranslationAvailableInDatabase: QApplication.translate(
                    "mod_file", "Show files that can be translated with the database"
                ),
                ModFile.Status.TranslationAvailableOnline: QApplication.translate(
                    "mod_file", "Show files that have a translation available online"
                ),
                ModFile.Status.RequiresTranslation: QApplication.translate(
                    "mod_file", "Show files that require a translation"
                ),
                ModFile.Status.NoTranslationAvailable: QApplication.translate(
                    "mod_file", "Show files without an available translation"
                ),
            }

            return LOC_NAMES[self]

    status: Status = Status.NoneStatus
    """
    Translation status of this file.
    """

    @override
    def __hash__(self) -> int:
        return hash((self.name.lower(), str(self.path).lower()))
