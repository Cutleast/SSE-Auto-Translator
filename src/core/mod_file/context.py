"""
Copyright (c) Cutleast
"""

from abc import ABC

from pydantic import BaseModel
from PySide6.QtWidgets import QApplication


class ModFileContext(BaseModel, ABC, frozen=True):
    """
    Base model for the mod file context for a string translation.
    """

    @property
    def display_text(self) -> str:
        """A display text (formatted in HTML) describing the context."""

        return (
            "<i>"
            + QApplication.translate("ModFileContext", "No context available.")
            + "</i>"
        )
