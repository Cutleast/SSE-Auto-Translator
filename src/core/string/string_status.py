"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from enum import auto
from typing import Optional, override

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from core.utilities.localized_enum import LocalizedEnum


class StringStatus(LocalizedEnum):
    """
    Enum for string status.
    """

    NoneStatus = auto()
    """String has no particular status."""

    NoTranslationRequired = auto()
    """String is marked as "No Translation Required"."""

    TranslationComplete = auto()
    """String is completely translated and validated."""

    TranslationIncomplete = auto()
    """
    String is automatically translated but not validated or user has partially
    translated this string.
    """

    TranslationRequired = auto()
    """String is not translated."""

    @classmethod
    def get_color(cls, status: StringStatus) -> Optional[QColor]:
        COLORS = {
            cls.NoTranslationRequired: QColor.fromString("#e9e042"),
            cls.TranslationComplete: QColor.fromString("#51c6d9"),
            cls.TranslationIncomplete: QColor.fromString("#c24cd4"),
            cls.TranslationRequired: QColor.fromString("#d74343"),
        }

        return COLORS.get(status)

    @override
    def get_localized_name(self) -> str:
        LOC_NAMES: dict[StringStatus, str] = {
            StringStatus.NoneStatus: QApplication.translate(
                "StringStatus", "No status (no color)"
            ),
            StringStatus.NoTranslationRequired: QApplication.translate(
                "StringStatus", "String does not require a translation"
            ),
            StringStatus.TranslationComplete: QApplication.translate(
                "StringStatus", "String is completely translated"
            ),
            StringStatus.TranslationIncomplete: QApplication.translate(
                "StringStatus", "String is partially translated"
            ),
            StringStatus.TranslationRequired: QApplication.translate(
                "StringStatus", "String requires a translation"
            ),
        }

        return LOC_NAMES[self]

    @override
    def get_localized_description(self) -> str:
        return self.get_localized_name()

    def get_localized_filter_name(self) -> str:
        LOC_NAMES: dict[StringStatus, str] = {
            StringStatus.NoneStatus: QApplication.translate(
                "StringStatus", "Show stateless strings"
            ),
            StringStatus.NoTranslationRequired: QApplication.translate(
                "StringStatus", "Show strings that do not require a translation"
            ),
            StringStatus.TranslationComplete: QApplication.translate(
                "StringStatus", "Show strings that are completely translated"
            ),
            StringStatus.TranslationIncomplete: QApplication.translate(
                "StringStatus", "Show strings that are partially translated"
            ),
            StringStatus.TranslationRequired: QApplication.translate(
                "StringStatus", "Show strings that require a translation"
            ),
        }

        return LOC_NAMES[self]
