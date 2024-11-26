"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTreeWidgetItem


@dataclass
class Plugin:
    """
    Class for plugin files.
    """

    name: str
    path: Path

    class Status(IntEnum):
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
        Translation for Plugin is available in Database (cyan).
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
        def get_color(cls, status: int) -> QColor | None:
            COLORS = {
                cls.NoneStatus: None,
                cls.NoStrings: None,
                cls.IsTranslated: QColor.fromString("#8be248"),
                cls.TranslationInstalled: QColor.fromString("#8be248"),
                cls.TranslationIncomplete: QColor.fromString("#c24cd4"),
                cls.TranslationAvailableInDatabase: QColor.fromString("#51c6d9"),
                cls.TranslationAvailableOnline: QColor.fromString("#51c6d9"),
                cls.RequiresTranslation: QColor.fromString("#e9e042"),
                cls.NoTranslationAvailable: QColor.fromString("#d74343"),
            }

            return COLORS.get(status)

        @classmethod
        def get_members(cls):
            result: list[cls] = [
                cls.NoneStatus,
                cls.TranslationInstalled,
                cls.TranslationIncomplete,
                cls.TranslationAvailableOnline,
                cls.RequiresTranslation,
                cls.NoTranslationAvailable,
            ]

            return result

    status: Status = Status.NoneStatus

    tree_item: QTreeWidgetItem = None

    def __hash__(self) -> int:
        return hash((self.name.lower(), str(self.path).lower()))
    
    def __getstate__(self):
        state = self.__dict__.copy()

        # Don't pickle tree_item
        del state["tree_item"]

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
