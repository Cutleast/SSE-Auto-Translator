"""
Copyright (c) Cutleast
"""


from pydantic import BaseModel

from .request import TranslationRequest


class TranslationResult(BaseModel, frozen=True):
    """
    The result of a translation request.
    """

    request: TranslationRequest
    """The original translation request."""

    translated_text: str
    """The translated text."""
