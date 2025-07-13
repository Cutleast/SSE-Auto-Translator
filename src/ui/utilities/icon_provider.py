"""
Copyright (c) Cutleast
"""

from enum import Enum

import qtawesome as qta
from PySide6.QtCore import QFile
from PySide6.QtGui import QIcon


class ResourceIcon(Enum):
    """Enum for icons from the resource file."""

    ArrowDown = "arrow_down.svg"
    ArrowLeft = "arrow_left.svg"
    ArrowRight = "arrow_right.svg"
    ArrowUp = "arrow_up.svg"
    Confrerie = "cdt.svg"
    Checkmark = "checkmark.svg"
    Close = "close.svg"
    DetectLang = "detect_lang.svg"
    Discord = "discord.png"
    Exit = "exit.svg"
    Grip = "grip.png"
    SSEAT = "icon.svg"
    KoFi = "ko-fi.png"
    NexusMods = "nexus_mods.svg"
    NexusModsColored = "nexus_mods.png"
    Plugin = "plugin.svg"
    ScanOnline = "scan_online.svg"
    Search = "search.svg"


class IconProvider:
    """
    Class for providing icons from either qtawesome or the resource file.
    """

    ICON_COLOR: str = "#ffffff"
    """Regular icon color."""

    ACCENT_ICON_COLOR: str = "#000000"
    """Color for icons on an accent background."""

    DISABLED_ICON_COLOR: str = "#666666"
    """Disabled icon color."""

    @staticmethod
    def get_qta_icon(icon_name: str, accent_background: bool = False) -> QIcon:
        """
        Gets the specified icon from qtawesome and returns it with the correct colors.

        Args:
            icon_name (str): The name of the icon to get.
            accent_background (bool, optional):
                Whether the icon color should fit an accent background. Defaults to
                False.

        Returns:
            QIcon: The icon with the correct colors.
        """

        return qta.icon(
            icon_name,
            color=(
                IconProvider.ACCENT_ICON_COLOR
                if accent_background
                else IconProvider.ICON_COLOR
            ),
            color_disabled=IconProvider.DISABLED_ICON_COLOR,
        )

    @staticmethod
    def get_res_icon(resource_icon: ResourceIcon) -> QIcon:
        """
        Gets the specified icon from the resource file and returns it.

        Args:
            resource_icon (ResourceIcon): The icon to get.

        Raises:
            FileNotFoundError: When the icon does not exist.

        Returns:
            QIcon: The icon.
        """

        path: str = ":/icons/" + resource_icon.value

        if not QFile.exists(path):
            raise FileNotFoundError(f"The icon '{path}' does not exist!")

        return QIcon(path)
