"""
Copyright (c) Cutleast
"""

from enum import auto

from core.utilities.base_enum import BaseEnum


class ProviderPreference(BaseEnum):
    """User preference for translation providers."""

    OnlyNexusMods = auto()
    """Only Nexus Mods is used as a translation provider."""

    PreferNexusMods = auto()
    """Nexus Mods is preferred over Confrérie des Traducteurs."""

    OnlyConfrerie = auto()
    """Only Confrérie des Traducteurs is used as a translation provider."""

    PreferConfrerie = auto()
    """Confrérie des Traducteurs is preferred over Nexus Mods."""
