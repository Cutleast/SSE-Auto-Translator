"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.qt_res_provider import (
    load_json_resource,
    read_resource,
)
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.ui_theme_manager import UiThemeManager


class ThemeManager(UiThemeManager):
    """
    ThemeManager implementation for SSE-AT.
    """

    @override
    def _get_raw_stylesheet(self) -> str:
        qss_files: list[str] = load_json_resource(":/qss.json")

        combined_qss: str = ""
        for qss_file in qss_files:
            combined_qss += read_resource(f":/{qss_file}") + "\n"

        combined_qss += read_resource(":/style.qss")  # SSE-AT-specific styles

        return combined_qss

    @override
    def _get_raw_theme_string(self) -> str:
        return read_resource(f":/{self.ui_mode.value.lower()}_theme.json")

    @override
    def _init_icon_provider(self) -> IconProvider:
        return IconProvider(self.ui_mode, self._theme.primary_fg_color)
