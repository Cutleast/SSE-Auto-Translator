"""
Copyright (c) Cutleast
"""

from abc import ABC
from typing import Literal, Optional

from pydantic import BaseModel

from .source import Source


class BaseModId(BaseModel, ABC, frozen=True):
    """
    Dataclass for identifying mods at their source.
    """

    installation_file_name: Optional[str] = None
    """The full name of the original download archive, if available."""

    source: Literal[Source.NexusMods, Source.Confrerie]
    """The source of the mod."""
