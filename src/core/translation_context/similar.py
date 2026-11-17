"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from core.string.types import String


class SimilarString(BaseModel, frozen=True):
    """
    A translated string that is similar to a string being edited.
    """

    string: String
    """The string that is similar."""

    score: Annotated[float, Field(ge=0.0, le=100.0)]
    """The fuzzy similarity score in percent."""

    translation_name: str
    """The name of the translation that the string originates from."""

    mod_file: Path
    """The mod file that the string originates from."""
