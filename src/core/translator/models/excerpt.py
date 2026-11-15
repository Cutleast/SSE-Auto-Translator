"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel


class TranslationExcerpt(BaseModel, frozen=True):
    """
    Represents a selected part of an existing translation that should be translated
    separately and replace the selected part afterwards.
    """

    text: str
    """The selected text that should be translated."""

    prefix: str
    """The text of the current translation preceding the selected part."""

    suffix: str
    """The text of the current translation following the selected part."""

    original_text: str
    """The complete original text of the string."""
