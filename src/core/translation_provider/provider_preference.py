"""
Copyright (c) Cutleast
"""

from core.utilities.base_enum import BaseEnum


class ProviderPreference(BaseEnum):
    """User preference for translation providers."""

    OnlyNexusMods = "OnlyNexusMods"
    """Only Nexus Mods is used as a translation provider."""

    PreferNexusMods = "PreferNexusMods"
    """Nexus Mods is preferred over Confrérie des Traducteurs."""

    OnlyConfrerie = "OnlyConfrerie"
    """Only Confrérie des Traducteurs is used as a translation provider."""

    PreferConfrerie = "PreferConfrerie"
    """Confrérie des Traducteurs is preferred over Nexus Mods."""
