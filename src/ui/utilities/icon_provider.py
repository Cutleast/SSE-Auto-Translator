"""
Copyright (c) Cutleast
"""

from enum import StrEnum

from cutleast_core_lib.ui.utilities.icon_provider import (
    IconProvider as BaseIconProvider,
)
from PySide6.QtCore import QFile
from PySide6.QtGui import QIcon


class ResourceIcon(StrEnum):
    """Enum for icons from the resource file."""

    Confrerie = "cdt.svg"
    DetectLang = "detect_lang.svg"
    SSEAT = "icon.svg"
    NexusMods = "nexus_mods.svg"
    Plugin = "plugin.svg"
    ScanOnline = "scan_online.svg"


class IconProvider(BaseIconProvider):
    """
    Icon provider for SSE-AT specific icons.
    """

    @classmethod
    def get_res_icon(cls, resource_icon: ResourceIcon) -> QIcon:
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
        disabled_path: str = ":/icons/disabled/" + resource_icon.value

        if not QFile.exists(path):
            raise FileNotFoundError(f"The icon '{path}' does not exist!")

        icon = QIcon(path)

        if QFile.exists(disabled_path):
            icon.addFile(disabled_path, mode=QIcon.Mode.Disabled)

        return icon
