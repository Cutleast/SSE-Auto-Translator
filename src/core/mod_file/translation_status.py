"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from enum import IntEnum
from typing import Optional, override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.models.theme import Theme
from cutleast_core_lib.ui.theme.models.types import ThemeAlias
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from ..utilities.colored_enum import ColoredEnum


class TranslationStatus(IntEnum, LocalizedEnum, ColoredEnum):
    """
    Enum for different translation status of mod files.
    """

    NoneStatus = -1
    """None Status (no color)."""

    NoStrings = 0
    """File has no Strings (no color)."""

    IsTranslated = 1
    """File is already in target language (green)."""

    TranslationInstalled = 2
    """Translation for file is already installed in Database (green)."""

    TranslationAvailableInDatabase = 3
    """Translation for file is available in Database (blue)."""

    TranslationAvailableOnline = 4
    """
    Translation for file is available online at Nexus Mods or Confrérie des Traducteurs
    (blue).
    """

    TranslationIncomplete = 5
    """Translation for file is installed but incomplete (magenta)."""

    RequiresTranslation = 6
    """File has Strings and requires translation (yellow)."""

    NoTranslationAvailable = 7
    """No Translation for file at Nexus Mods or in Database (red)."""

    @override
    def get_base_color(self) -> QColor:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case TranslationStatus.NoneStatus:
                token = theme.texts.text.color
            case TranslationStatus.NoStrings:
                token = theme.texts.text.color
            case TranslationStatus.IsTranslated:
                token = theme.colors.success
            case TranslationStatus.TranslationInstalled:
                token = theme.colors.success
            case TranslationStatus.TranslationIncomplete:
                token = theme.colors.caution
            case TranslationStatus.TranslationAvailableInDatabase:
                token = theme.colors.information
            case TranslationStatus.TranslationAvailableOnline:
                token = theme.colors.information
            case TranslationStatus.RequiresTranslation:
                token = theme.colors.warning
            case TranslationStatus.NoTranslationAvailable:
                token = theme.colors.error

        return QColor.fromString(theme.resolve(token))

    @override
    def get_bg_color(self) -> Optional[QColor]:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case TranslationStatus.NoneStatus:
                return
            case TranslationStatus.NoStrings:
                return
            case TranslationStatus.IsTranslated:
                token = theme.colors.success_bg
            case TranslationStatus.TranslationInstalled:
                token = theme.colors.success_bg
            case TranslationStatus.TranslationIncomplete:
                token = theme.colors.caution_bg
            case TranslationStatus.TranslationAvailableInDatabase:
                token = theme.colors.information_bg
            case TranslationStatus.TranslationAvailableOnline:
                token = theme.colors.information_bg
            case TranslationStatus.RequiresTranslation:
                token = theme.colors.warning_bg
            case TranslationStatus.NoTranslationAvailable:
                token = theme.colors.error_bg

        return QColor.fromString(theme.resolve(token))

    @override
    def get_highlighted_bg_color(self) -> Optional[QColor]:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case TranslationStatus.NoneStatus:
                return
            case TranslationStatus.NoStrings:
                return
            case TranslationStatus.IsTranslated:
                token = theme.colors.success_bg_hover
            case TranslationStatus.TranslationInstalled:
                token = theme.colors.success_bg_hover
            case TranslationStatus.TranslationIncomplete:
                token = theme.colors.caution_bg_hover
            case TranslationStatus.TranslationAvailableInDatabase:
                token = theme.colors.information_bg_hover
            case TranslationStatus.TranslationAvailableOnline:
                token = theme.colors.information_bg_hover
            case TranslationStatus.RequiresTranslation:
                token = theme.colors.warning_bg_hover
            case TranslationStatus.NoTranslationAvailable:
                token = theme.colors.error_bg_hover

        return QColor.fromString(theme.resolve(token))

    @override
    def get_fg_color(self) -> QColor:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case TranslationStatus.NoneStatus:
                token = theme.texts.text.color
            case TranslationStatus.NoStrings:
                token = theme.texts.text.color
            case TranslationStatus.IsTranslated:
                token = theme.colors.success_fg
            case TranslationStatus.TranslationInstalled:
                token = theme.colors.success_fg
            case TranslationStatus.TranslationIncomplete:
                token = theme.colors.caution_fg
            case TranslationStatus.TranslationAvailableInDatabase:
                token = theme.colors.information_fg
            case TranslationStatus.TranslationAvailableOnline:
                token = theme.colors.information_fg
            case TranslationStatus.RequiresTranslation:
                token = theme.colors.warning_fg
            case TranslationStatus.NoTranslationAvailable:
                token = theme.colors.error_fg

        return QColor.fromString(theme.resolve(token))

    @override
    def get_localized_name(self) -> str:
        match self:
            case TranslationStatus.NoneStatus:
                return QApplication.translate("mod_file", "Unknown")
            case TranslationStatus.NoStrings:
                return QApplication.translate("mod_file", "No Strings")
            case TranslationStatus.IsTranslated:
                return QApplication.translate("mod_file", "Translated")
            case TranslationStatus.TranslationInstalled:
                return QApplication.translate("mod_file", "Translation Installed")
            case TranslationStatus.TranslationIncomplete:
                return QApplication.translate("mod_file", "Translation Incomplete")
            case TranslationStatus.TranslationAvailableInDatabase:
                return QApplication.translate("mod_file", "Available in Database")
            case TranslationStatus.TranslationAvailableOnline:
                return QApplication.translate("mod_file", "Available Online")
            case TranslationStatus.RequiresTranslation:
                return QApplication.translate("mod_file", "Requires Translation")
            case TranslationStatus.NoTranslationAvailable:
                return QApplication.translate("mod_file", "No Translation Available")

    @override
    def get_localized_description(self) -> str:
        match self:
            case TranslationStatus.NoneStatus:
                return QApplication.translate(
                    "mod_file", "The status of the file is unknown."
                )
            case TranslationStatus.NoStrings:
                return QApplication.translate(
                    "mod_file", "The file has no translatable strings."
                )
            case TranslationStatus.IsTranslated:
                return QApplication.translate(
                    "mod_file", "The file is already in the target language."
                )
            case TranslationStatus.TranslationInstalled:
                return QApplication.translate(
                    "mod_file",
                    "A translation for the file is already installed in the database.",
                )
            case TranslationStatus.TranslationIncomplete:
                return QApplication.translate(
                    "mod_file", "A translation for the file is installed but incomplete."
                )
            case TranslationStatus.TranslationAvailableInDatabase:
                return QApplication.translate(
                    "mod_file",
                    "A translation for the file is available in the database.",
                )
            case TranslationStatus.TranslationAvailableOnline:
                return QApplication.translate(
                    "mod_file", "A translation for the file is available online."
                )
            case TranslationStatus.RequiresTranslation:
                return QApplication.translate(
                    "mod_file", "The file has strings and requires a translation."
                )
            case TranslationStatus.NoTranslationAvailable:
                return QApplication.translate(
                    "mod_file",
                    "There is no translation available for the file online or in the "
                    "database.",
                )
