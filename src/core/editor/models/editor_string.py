"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Annotated, Optional

from pydantic import BaseModel, Field

from core.string.types import String
from core.translation_context.context import TranslationContext

from .diagnostics import TranslationDiagnostics


class EditorString(BaseModel):
    """
    An editor string consists of a translation string, context and the diagnostics of
    the translation.
    """

    string: Annotated[String, Field(frozen=True)]
    """The string that is edited."""

    mod_file_path: Annotated[Path, Field(frozen=True)]
    """
    The path of the mod file, that the string belongs to, relative to the game's "Data"
    folder.
    """

    context: Optional[TranslationContext] = None
    """The translation context for the string being edited."""

    diagnostics: Optional[TranslationDiagnostics] = None
    """The diagnostics of the translation, if any."""
