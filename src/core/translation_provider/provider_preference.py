"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from PySide6.QtWidgets import QApplication


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
        match self:
            case ProviderPreference.OnlyNexusMods:
                return QApplication.translate("ProviderPreference", "Only Nexus Mods")
            case ProviderPreference.PreferNexusMods:
                return QApplication.translate("ProviderPreference", "Prefer Nexus Mods")
            case ProviderPreference.OnlyConfrerie:
                return QApplication.translate(
                    "ProviderPreference", "Only Confrérie des Traducteurs"
                )
            case ProviderPreference.PreferConfrerie:
                return QApplication.translate(
                    "ProviderPreference", "Prefer Confrérie des Traducteurs"
                )

    @override
    def get_localized_description(self) -> str:
        return self.get_localized_name()
