"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.utilities.icon_provider import IconProvider, ResourceIcon


class Source(str, LocalizedEnum):
    """
    Enum for different Sources (for eg. Nexus Mods or Confrérie des Traducteurs).
    """

    NexusMods = "NexusMods"
    """
    Translation was downloaded and installed from Nexus Mods.
    """

    Confrerie = "Confrérie des Traducteurs"
    """
    Translation was downloaded and installed from Confrérie des Traducteurs.
    """

    Local = "Local"
    """
    Translation was either imported from local disk or created from database.
    """

    def get_icon(self) -> Optional[QIcon]:
        """
        Returns:
            Optional[QIcon]: Icon or None.
        """

        match self:
            case Source.NexusMods:
                return IconProvider.get_res_icon(ResourceIcon.NexusMods)
            case Source.Confrerie:
                return IconProvider.get_res_icon(ResourceIcon.Confrerie)

    @override
    def get_localized_name(self) -> str:
        match self:
            case Source.NexusMods:
                return QApplication.translate("Source", "Nexus Mods")
            case Source.Confrerie:
                return QApplication.translate("Source", "Confrérie des Traducteurs")
            case Source.Local:
                return QApplication.translate("Source", "Local")
