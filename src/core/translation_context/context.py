"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel, Field

from core.mod_file.context import ModFileContext

from .glossary import TranslationGlossary
from .similar import SimilarString


class TranslationContext(BaseModel, frozen=True):
    """
    The translation context for a string being edited.
    """

    similar_strings: list[SimilarString]
    """A list of similar strings."""

    mod_file_context: ModFileContext
    """The mod file-specific context."""

    glossary_terms: list[TranslationGlossary.Term] = Field(default_factory=list)
    """List of translation terms to be followed in the translation."""
