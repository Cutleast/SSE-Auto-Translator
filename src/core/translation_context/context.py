"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel

from core.mod_file.context import ModFileContext

from .similar_string import SimilarString


class TranslationContext(BaseModel, frozen=True):
    """
    The translation context for a string being edited.
    """

    similar_strings: list[SimilarString]
    """A list of similar strings."""

    mod_file_context: ModFileContext
    """The mod file-specific context."""

    placeholders: list[str]
    """Placeholders and markup in the original string that have to be kept."""
