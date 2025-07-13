"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.utilities.localized_enum import LocalizedEnum


class Source(LocalizedEnum):
    """
    Enum for different Sources (for eg. Nexus Mods or Confrérie des Traducteurs).
    """

    NexusMods = "NexusMods"
    """
    Translation is downloaded and installed from Nexus Mods.
    """

    Confrerie = "Confrérie des Traducteurs"
    """
    Translation is downloaded and installed from Confrérie des Traducteurs.
    """

    Local = "Local"
    """
    Translation is either imported from local disk or created from database.
    """

    def get_icon(self) -> Optional[QIcon]:
        """
        Returns the icon for the source.

        Returns:
            Optional[QIcon]: Icon or None.
        """

        ICONS: dict[Source, QIcon] = {
            Source.NexusMods: QIcon(":/icons/nexus_mods.svg"),
            Source.Confrerie: QIcon(":/icons/cdt.svg"),
        }

        return ICONS.get(self)

    @override
    def get_localized_name(self) -> str:
        locs: dict[Source, str] = {
            Source.NexusMods: QApplication.translate("Source", "Nexus Mods"),
            Source.Confrerie: QApplication.translate(
                "Source", "Confrérie des Traducteurs"
            ),
            Source.Local: QApplication.translate("Source", "Local"),
        }

        return locs[self]

    @override
    def get_localized_description(self) -> str:
        return self.get_localized_name()
