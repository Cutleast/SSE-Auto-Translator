"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.qt_res_provider import read_resource
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.theme_manager import (
    ThemeManager as BaseThemeManager,
)
from cutleast_core_lib.ui.utilities.ui_mode import UIMode
from PySide6.QtGui import QColor, QPalette


class ThemeManager(BaseThemeManager):
    """
    An example ThemeManager implementation.
    """

    @override
    def _get_stylesheet(self) -> str:
        ui_mode: str = self.ui_mode.name.lower()
        base_stylesheet_file: str = ":/base_stylesheet.qss"
        stylesheet_file: str = ":/" + ui_mode + "_stylesheet.qss"

        base_stylesheet: str = read_resource(base_stylesheet_file)
        raw_stylesheet: str = read_resource(stylesheet_file)
        sse_at_stylesheet: str = read_resource(":/style.qss")
        final_stylesheet: str = (
            base_stylesheet + "\n" + raw_stylesheet + "\n" + sse_at_stylesheet
        )

        colors: dict[str, str] = self.__get_colors()
        for placeholder_name, color in colors.items():
            final_stylesheet = final_stylesheet.replace(f"<{placeholder_name}>", color)

        return final_stylesheet

    def __get_colors(self) -> dict[str, str]:
        accent_color: str = self._accent_color
        highlighted_accent: str = (
            QColor(accent_color).lighter(110).name()
            if self.ui_mode == UIMode.Dark
            else QColor(accent_color).darker(110).name()
        )

        colors: dict[str, str] = {
            "accent_color": accent_color,
            "highlighted_accent": highlighted_accent,
            "text_color": "#ffffff" if self.ui_mode == UIMode.Dark else "#000000",
        }

        return colors

    @override
    def _apply_to_palette(self, palette: QPalette) -> None:
        colors: dict[str, str] = self.__get_colors()

        palette.setColor(QPalette.ColorRole.Text, colors["text_color"])
        palette.setColor(QPalette.ColorRole.Accent, colors["accent_color"])
        palette.setColor(QPalette.ColorRole.Highlight, colors["highlighted_accent"])
        palette.setColor(QPalette.ColorRole.Link, colors["accent_color"])

    @override
    def _init_icon_provider(self) -> IconProvider:
        return IconProvider(self.ui_mode, self.__get_colors()["text_color"])
