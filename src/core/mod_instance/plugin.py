"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from core.utilities.base_enum import BaseEnum


@dataclass
class Plugin:
    """
    Class for plugin files.
    """

    name: str
    path: Path

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
        Plugin has no Strings (no color).
        """

        IsTranslated = 1
        """
        Plugin is already in target language (green).
        """

        TranslationInstalled = 2
        """
        Translation for Plugin is already installed in Database (green).
        """

        TranslationAvailableInDatabase = 3
        """
        Translation for Plugin is available in Database (green).
        """

        TranslationAvailableOnline = 4
        """
        Translation for Plugin is available online at Nexus Mods or Confrérie des Traducteurs (cyan).
        """

        TranslationIncomplete = 5
        """
        Translation for Plugin is installed but incomplete (magenta).
        """

        RequiresTranslation = 6
        """
        Plugin has Strings and requires translation (yellow).
        """

        NoTranslationAvailable = 7
        """
        No Translation for Plugin at Nexus Mods or in Database (red).
        """

        @classmethod
        def get_color(cls, status: "Plugin.Status") -> QColor | None:
            COLORS: dict["Plugin.Status", Optional[QColor]] = {
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
            LOC_NAMES: dict["Plugin.Status", str] = {
                Plugin.Status.NoneStatus: QApplication.translate(
                    "plugin", "No Status (No Color)"
                ),
                Plugin.Status.NoStrings: QApplication.translate(
                    "plugin", "Plugin has no Strings (No Color)"
                ),
                Plugin.Status.IsTranslated: QApplication.translate(
                    "plugin", "Plugin is already in target language"
                ),
                Plugin.Status.TranslationInstalled: QApplication.translate(
                    "plugin", "Translation for Plugin is already installed in Database"
                ),
                Plugin.Status.TranslationIncomplete: QApplication.translate(
                    "plugin", "Translation for Plugin is installed but incomplete"
                ),
                Plugin.Status.TranslationAvailableInDatabase: QApplication.translate(
                    "plugin", "Translation for Plugin is available in Database"
                ),
                Plugin.Status.TranslationAvailableOnline: QApplication.translate(
                    "plugin", "Translation for Plugin is available online"
                ),
                Plugin.Status.RequiresTranslation: QApplication.translate(
                    "plugin", "Plugin has Strings and requires translation"
                ),
                Plugin.Status.NoTranslationAvailable: QApplication.translate(
                    "plugin",
                    "No Translation for Plugin available online or in Database",
                ),
            }

            return LOC_NAMES[self]

        def get_localized_filter_name(self) -> str:
            LOC_NAMES: dict["Plugin.Status", str] = {
                Plugin.Status.NoneStatus: QApplication.translate(
                    "plugin", "No stateless plugins"
                ),
                Plugin.Status.NoStrings: QApplication.translate(
                    "plugin", "Show plugins without strings"
                ),
                Plugin.Status.IsTranslated: QApplication.translate(
                    "plugin", "Show plugins that are already in target language"
                ),
                Plugin.Status.TranslationInstalled: QApplication.translate(
                    "plugin", "Show plugins with an installed translation"
                ),
                Plugin.Status.TranslationIncomplete: QApplication.translate(
                    "plugin",
                    "Show plugins with an installed but incomplete translation",
                ),
                Plugin.Status.TranslationAvailableInDatabase: QApplication.translate(
                    "plugin", "Show plugins that can be translated with the database"
                ),
                Plugin.Status.TranslationAvailableOnline: QApplication.translate(
                    "plugin", "Show plugins that have a translation available online"
                ),
                Plugin.Status.RequiresTranslation: QApplication.translate(
                    "plugin", "Show plugins that require a translation"
                ),
                Plugin.Status.NoTranslationAvailable: QApplication.translate(
                    "plugin", "Show plugins without an available translation"
                ),
            }

            return LOC_NAMES[self]

    status: Status = Status.NoneStatus

    def __hash__(self) -> int:
        return hash((self.name.lower(), str(self.path).lower()))
