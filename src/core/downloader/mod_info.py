"""
Copyright (c) Cutleast
"""

from typing import Optional

from pydantic import BaseModel

from core.translation_provider.mod_id import ModId
from core.translation_provider.source import Source


class ModInfo(BaseModel, frozen=True):
    """
    Model for a mod's display name and its mod id.
    """

    display_name: str
    """The display name of the mod."""

    mod_id: Optional[ModId]
    """The mod's id at its source."""

    source: Source
    """The mod's source."""
