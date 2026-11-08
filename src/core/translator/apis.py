"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from PySide6.QtWidgets import QApplication


class TranslatorApi(LocalizedEnum):
    """Enum for available translator APIs."""

    Google = "Google Translator"
    """Google translator API (free)."""

    DeepL = "DeepL"
    """DeepL translator API (requires API key)."""

    @override
    def get_localized_name(self) -> str:
        match self:
            case TranslatorApi.Google:
                return QApplication.translate(
                    "TranslatorApi", "Google Translator (free)"
                )

            case TranslatorApi.DeepL:
                return QApplication.translate(
                    "TranslatorApi", "DeepL (API key required)"
                )
