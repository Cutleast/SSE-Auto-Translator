"""
Copyright (c) Cutleast
"""

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from .request import TranslationRequest


class TranslationResult(BaseModel, frozen=True):
    """
    The result of a translation request.
    """

    request: TranslationRequest
    """The original translation request."""

    translated_text: str
    """The translated text."""
