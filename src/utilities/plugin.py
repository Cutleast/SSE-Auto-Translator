"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QTreeWidgetItem
from qtpy.QtCore import Qt


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

        TranslationInstalled = 1
        """
        Translation for Plugin is already installed in Database (green).
        """

        TranslationAvailableInDatabase = 2
        """
        Translation for Plugin is available in Database (cyan).
        """

        TranslationAvailableAtNexusMods = 3
        """
        Translation for Plugin is available at Nexus Mods (cyan).
        """

        TranslationIncomplete = 4
        """
        Translation for Plugin is installed but incomplete (magenta).
        """

        RequiresTranslation = 5
        """
        Plugin has Strings and requires translation (yellow).
        """

        NoTranslationAvailable = 6
        """
        No Translation for Plugin at Nexus Mods or in Database (red).
        """

        @classmethod
        def get_color(cls, status: int) -> QColor | None:
            COLORS = {
                cls.NoneStatus: None,
                cls.NoStrings: None,
                cls.TranslationInstalled: QColor.fromString("#8be248"),
                cls.TranslationIncomplete: QColor.fromString("#c24cd4"),
                cls.RequiresTranslation: QColor.fromString("#e9e042"),
                cls.TranslationAvailableInDatabase: QColor.fromString("#51c6d9"),
                cls.TranslationAvailableAtNexusMods: QColor.fromString("#51c6d9"),
                cls.NoTranslationAvailable: QColor.fromString("#d74343"),
            }

            return COLORS.get(status)

    status: Status = Status.NoneStatus

    tree_item: QTreeWidgetItem = None
