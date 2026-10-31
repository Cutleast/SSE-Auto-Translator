"""
Copyright (c) Cutleast
"""

from pathlib import Path

from pydantic import BaseModel

from core.string.types import String


class RelatedString(BaseModel, frozen=True):
    """
    A string that is related to a string being edited, like the name of the item whose
    description is being edited.
    """

    relation: str
    """The localized description of how the string is related."""

    string: String
    """The related string."""

    mod_file: Path
    """The mod file that the related string originates from."""
