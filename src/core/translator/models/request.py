"""
Copyright (c) Cutleast
"""

from typing import TYPE_CHECKING, Optional

from cutleast_core_lib.core.utilities.hash import sha256_hash
from pydantic import BaseModel

from core.translation_context.context import TranslationContext
from core.utilities.game_language import GameLanguage

if TYPE_CHECKING:
    from .result import TranslationResult


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

    old_result: Optional[TranslationResult] = None
    """A previous translation result of the text, if this request is a retry."""

    @property
    def id(self) -> str:
        """A generated identifier for this request."""

        return sha256_hash(self.model_dump_json().encode())
