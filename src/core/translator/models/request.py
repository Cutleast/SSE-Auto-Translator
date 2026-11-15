"""
Copyright (c) Cutleast
"""

from typing import Optional

from cutleast_core_lib.core.utilities.hash import sha256_hash
from pydantic import BaseModel

from core.translation_context.context import TranslationContext
from core.utilities.game_language import GameLanguage

from .excerpt import TranslationExcerpt


class TranslationRequest(BaseModel, frozen=True):
    """
    Model for a single translation request containing the original text, destination
    language, context and additional instructions.
    """

    text: str
    """The text to translate."""

    dst: GameLanguage
    """The destination language."""

    context: TranslationContext
    """The translation context of the text."""

    instructions: Optional[str] = None
    """Optional additional instructions for the translation."""

    old_translation: Optional[str] = None
    """
    A previous translation of the text. If given, the translator is instructed to
    improve or correct it.
    """

    excerpt: Optional[TranslationExcerpt] = None
    """
    The selected part of an existing translation, if only that part should be
    translated. In this case, `text` contains only the selected part.
    """

    @property
    def id(self) -> str:
        """A generated identifier for this request."""

        return sha256_hash(self.model_dump_json().encode())
