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


class StringStatus(IntEnum, LocalizedEnum, ColoredEnum):
    """
    Enum for string status.
    """

    NoneStatus = -1
    """String has no particular status."""

    NoTranslationRequired = 0
    """String is marked as "No Translation Required"."""

    TranslationComplete = 1
    """String is completely translated and validated."""

    TranslationIncomplete = 2
    """
    String is automatically translated but not validated or user has partially translated
    this string.
    """

    TranslationRequired = 3
    """String is not translated."""

    @override
    def get_base_color(self) -> QColor:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case StringStatus.NoneStatus:
                token = theme.texts.text.color
            case StringStatus.NoTranslationRequired:
                token = theme.colors.warning
            case StringStatus.TranslationComplete:
                token = theme.colors.information
            case StringStatus.TranslationIncomplete:
                token = theme.colors.caution
            case StringStatus.TranslationRequired:
                token = theme.colors.error

        return QColor.fromString(theme.resolve(token))

    @override
    def get_bg_color(self) -> Optional[QColor]:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case StringStatus.NoTranslationRequired:
                token = theme.colors.warning_bg
            case StringStatus.TranslationComplete:
                token = theme.colors.information_bg
            case StringStatus.TranslationIncomplete:
                token = theme.colors.caution_bg
            case StringStatus.TranslationRequired:
                token = theme.colors.error_bg
            case _:
                return

        return QColor.fromString(theme.resolve(token))

    @override
    def get_highlighted_bg_color(self) -> Optional[QColor]:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case StringStatus.NoTranslationRequired:
                token = theme.colors.warning_bg_hover
            case StringStatus.TranslationComplete:
                token = theme.colors.information_bg_hover
            case StringStatus.TranslationIncomplete:
                token = theme.colors.caution_bg_hover
            case StringStatus.TranslationRequired:
                token = theme.colors.error_bg_hover
            case _:
                return

        return QColor.fromString(theme.resolve(token))

    @override
    def get_fg_color(self) -> QColor:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case StringStatus.NoneStatus:
                token = theme.texts.text.color
            case StringStatus.NoTranslationRequired:
                token = theme.colors.warning_fg
            case StringStatus.TranslationComplete:
                token = theme.colors.information_fg
            case StringStatus.TranslationIncomplete:
                token = theme.colors.caution_fg
            case StringStatus.TranslationRequired:
                token = theme.colors.error_fg

        return QColor.fromString(theme.resolve(token))

    @override
    def get_localized_name(self) -> str:
        match self:
            case StringStatus.NoneStatus:
                return QApplication.translate("StringStatus", "No Status")
            case StringStatus.NoTranslationRequired:
                return QApplication.translate("StringStatus", "No Translation Required")
            case StringStatus.TranslationComplete:
                return QApplication.translate("StringStatus", "Translated")
            case StringStatus.TranslationIncomplete:
                return QApplication.translate("StringStatus", "Partially Translated")
            case StringStatus.TranslationRequired:
                return QApplication.translate("StringStatus", "Untranslated")

    @override
    def get_localized_description(self) -> str:
        match self:
            case StringStatus.NoneStatus:
                return QApplication.translate(
                    "StringStatus", "The status of the string is unknown."
                )
            case StringStatus.NoTranslationRequired:
                return QApplication.translate(
                    "StringStatus", "The string does not require a translation."
                )
            case StringStatus.TranslationComplete:
                return QApplication.translate(
                    "StringStatus", "The string is completely translated."
                )
            case StringStatus.TranslationIncomplete:
                return QApplication.translate(
                    "StringStatus", "The string is partially translated."
                )
            case StringStatus.TranslationRequired:
                return QApplication.translate(
                    "StringStatus", "The string requires a translation."
                )
