"""
Copyright (c) Cutleast
"""

from typing import Optional

from pydantic.dataclasses import dataclass

from core.translation_provider.mod_id import ModId
from core.translation_provider.source import Source


@dataclass(frozen=True)
class ModInfo:
    """
    Dataclass for a mod's display name and its mod id.
    """

    display_name: str
    """The display name of the mod."""

    mod_id: Optional[ModId]
    """The mod's id at its source."""

    source: Source
    """The mod's source."""
