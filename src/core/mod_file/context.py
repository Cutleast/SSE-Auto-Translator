"""
Copyright (c) Cutleast
"""

from typing import Optional

from pydantic import BaseModel, Field

from core.translation_context.context_property import ContextProperty
from core.translation_context.related_string import RelatedString


class ModFileContext(BaseModel, frozen=True):
    """
    The mod file-specific context for a string translation.
    """

    string_kind: Optional[str] = None
    """A localized description of what the string is, for eg. "Weapon - Name"."""

    properties: list[ContextProperty] = Field(default_factory=list[ContextProperty])
    """Labeled facts about the string, like its speaker or quest."""

    notes: list[str] = Field(default_factory=list[str])
    """Free-form notes from the mod author, like voice acting directions."""

    related_strings: list[RelatedString] = Field(default_factory=list[RelatedString])
    """Strings related to the string, like other strings of the same record."""
