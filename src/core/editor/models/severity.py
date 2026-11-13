"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.colored_enum import ColoredEnum
from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.models.theme import Theme
from cutleast_core_lib.ui.theme.models.types import ThemeAlias
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QApplication

from ui.utilities.icon_provider import IconProvider


class Severity(int, LocalizedEnum, ColoredEnum):
    """
    The severity of a result or issue.
    """

    Passed = 0
    """The item passed all validation checks."""

    Notice = 1
    """The item could have some minor issues that should be looked at."""

    Warning = 2
    """The item has some issues that should be looked at."""

    Error = 3
    """The item has some major issues that should definitely be fixed."""

    @override
    def get_localized_name(self) -> str:
        match self:
            case Severity.Passed:
                return QApplication.translate("Severity", "Passed")
            case Severity.Notice:
                return QApplication.translate("Severity", "Notice")
            case Severity.Warning:
                return QApplication.translate("Severity", "Warning")
            case Severity.Error:
                return QApplication.translate("Severity", "Error")

    @override
    def get_localized_description(self) -> str:
        match self:
            case Severity.Passed:
                return QApplication.translate(
                    "Severity",
                    "The item passed all validation checks.",
                )
            case Severity.Notice:
                return QApplication.translate(
                    "Severity",
                    "The item could have some minor issues that should be looked at.",
                )
            case Severity.Warning:
                return QApplication.translate(
                    "Severity",
                    "The item has some issues that should be looked at.",
                )
            case Severity.Error:
                return QApplication.translate(
                    "Severity",
                    "The item has some major issues that should definitely be fixed.",
                )

    @override
    def get_base_color(self) -> QColor:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case Severity.Passed:
                token = theme.colors.success
            case Severity.Notice:
                token = theme.colors.information
            case Severity.Warning:
                token = theme.colors.warning
            case Severity.Error:
                token = theme.colors.error

        return QColor.fromString(theme.resolve(token))

    @override
    def get_bg_color(self) -> QColor:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case Severity.Passed:
                token = theme.colors.success_bg
            case Severity.Notice:
                token = theme.colors.information_bg
            case Severity.Warning:
                token = theme.colors.warning_bg
            case Severity.Error:
                token = theme.colors.error_bg

        return QColor.fromString(theme.resolve(token))

    @override
    def get_highlighted_bg_color(self) -> QColor:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case Severity.Passed:
                token = theme.colors.success_bg_hover
            case Severity.Notice:
                token = theme.colors.information_bg_hover
            case Severity.Warning:
                token = theme.colors.warning_bg_hover
            case Severity.Error:
                token = theme.colors.error_bg_hover

        return QColor.fromString(theme.resolve(token))

    @override
    def get_fg_color(self) -> QColor:
        theme: Theme = ThemeManager.get().theme

        token: ThemeAlias
        match self:
            case Severity.Passed:
                token = theme.colors.success_fg
            case Severity.Notice:
                token = theme.colors.information_fg
            case Severity.Warning:
                token = theme.colors.warning_fg
            case Severity.Error:
                token = theme.colors.error_fg

        return QColor.fromString(theme.resolve(token))

    def get_icon(self) -> QIcon:
        """
        Returns:
            QIcon: An icon for this severity in the severity's foreground color.
        """

        icon: QIcon
        match self:
            case Severity.Passed:
                icon = IconProvider.get_qta_icon(
                    "mdi6.check", color=IconProvider.Color.Success
                )
            case Severity.Notice:
                icon = IconProvider.get_qta_icon(
                    "mdi6.information-outline", color=IconProvider.Color.Information
                )
            case Severity.Warning:
                icon = IconProvider.get_qta_icon(
                    "mdi6.alert-outline", color=IconProvider.Color.Warning
                )
            case Severity.Error:
                icon = IconProvider.get_qta_icon(
                    "mdi6.alert-octagon-outline", color=IconProvider.Color.Error
                )

        return icon
