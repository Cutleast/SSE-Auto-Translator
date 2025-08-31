"""
Copyright (c) Cutleast
"""

from enum import IntEnum
from typing import Optional, override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication


class TranslationStatus(IntEnum, LocalizedEnum):
    """
    Enum for different translation status of mod files.
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
    def get_color(cls, status: "TranslationStatus") -> QColor | None:
        COLORS: dict["TranslationStatus", Optional[QColor]] = {
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

    @override
    def get_localized_name(self) -> str:
        LOC_NAMES: dict["TranslationStatus", str] = {
            TranslationStatus.NoneStatus: QApplication.translate(
                "mod_file", "No Status (No Color)"
            ),
            TranslationStatus.NoStrings: QApplication.translate(
                "mod_file", "File has no Strings (No Color)"
            ),
            TranslationStatus.IsTranslated: QApplication.translate(
                "mod_file", "File is already in target language"
            ),
            TranslationStatus.TranslationInstalled: QApplication.translate(
                "mod_file", "Translation for file is already installed in Database"
            ),
            TranslationStatus.TranslationIncomplete: QApplication.translate(
                "mod_file", "Translation for file is installed but incomplete"
            ),
            TranslationStatus.TranslationAvailableInDatabase: QApplication.translate(
                "mod_file", "Translation for file is available in Database"
            ),
            TranslationStatus.TranslationAvailableOnline: QApplication.translate(
                "mod_file", "Translation for file is available online"
            ),
            TranslationStatus.RequiresTranslation: QApplication.translate(
                "mod_file", "File has Strings and requires translation"
            ),
            TranslationStatus.NoTranslationAvailable: QApplication.translate(
                "mod_file",
                "No Translation for file available online or in Database",
            ),
        }

        return LOC_NAMES[self]

    @override
    def get_localized_description(self) -> str:
        return self.get_localized_name()

    def get_localized_filter_name(self) -> str:
        LOC_NAMES: dict["TranslationStatus", str] = {
            TranslationStatus.NoneStatus: QApplication.translate(
                "mod_file", "No stateless files"
            ),
            TranslationStatus.NoStrings: QApplication.translate(
                "mod_file", "Show files without strings"
            ),
            TranslationStatus.IsTranslated: QApplication.translate(
                "mod_file", "Show files that are already in target language"
            ),
            TranslationStatus.TranslationInstalled: QApplication.translate(
                "mod_file", "Show files with an installed translation"
            ),
            TranslationStatus.TranslationIncomplete: QApplication.translate(
                "mod_file",
                "Show files with an installed but incomplete translation",
            ),
            TranslationStatus.TranslationAvailableInDatabase: QApplication.translate(
                "mod_file", "Show files that can be translated with the database"
            ),
            TranslationStatus.TranslationAvailableOnline: QApplication.translate(
                "mod_file", "Show files that have a translation available online"
            ),
            TranslationStatus.RequiresTranslation: QApplication.translate(
                "mod_file", "Show files that require a translation"
            ),
            TranslationStatus.NoTranslationAvailable: QApplication.translate(
                "mod_file", "Show files without an available translation"
            ),
        }

        return LOC_NAMES[self]
