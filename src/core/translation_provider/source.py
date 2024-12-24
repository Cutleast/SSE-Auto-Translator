"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtGui import QIcon

from core.utilities.base_enum import BaseEnum


class Source(BaseEnum):
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
