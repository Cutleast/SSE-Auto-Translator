"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QApplication

from core.utilities.localized_enum import LocalizedEnum


class ProviderPreference(LocalizedEnum):
    """User preference for translation providers."""

    OnlyNexusMods = "OnlyNexusMods"
    """Only Nexus Mods is used as a translation provider."""

    PreferNexusMods = "PreferNexusMods"
    """Nexus Mods is preferred over Confrérie des Traducteurs."""

    OnlyConfrerie = "OnlyConfrerie"
    """Only Confrérie des Traducteurs is used as a translation provider."""

    PreferConfrerie = "PreferConfrerie"
    """Confrérie des Traducteurs is preferred over Nexus Mods."""

    @override
    def get_localized_name(self) -> str:
        locs: dict[ProviderPreference, str] = {
            ProviderPreference.OnlyNexusMods: QApplication.translate(
                "ProviderPreference", "Only Nexus Mods"
            ),
            ProviderPreference.PreferNexusMods: QApplication.translate(
                "ProviderPreference", "Prefer Nexus Mods"
            ),
            ProviderPreference.OnlyConfrerie: QApplication.translate(
                "ProviderPreference", "Only Confrérie des Traducteurs"
            ),
            ProviderPreference.PreferConfrerie: QApplication.translate(
                "ProviderPreference", "Prefer Confrérie des Traducteurs"
            ),
        }

        return locs[self]

    @override
    def get_localized_description(self) -> str:
        return self.get_localized_name()
