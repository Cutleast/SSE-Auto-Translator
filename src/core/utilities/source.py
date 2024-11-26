"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from enum import StrEnum


class Source(StrEnum):
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

    @classmethod
    def get(cls, name: str, default=None, /):
        try:
            return cls[name]
        except KeyError:
            return default
