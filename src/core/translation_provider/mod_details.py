"""
Copyright (c) Cutleast
"""

from typing import Optional

from pydantic import BaseModel

from .mod_id import ModId


class ModDetails(BaseModel, frozen=True):
    """
    Model for mod details returned by a translation provider.
    """

    display_name: str
    """The display name of the mod or file."""

    mod_display_name: Optional[str] = None
    """The display name of the mod, if applicable."""

    file_name: str
    """The full name of the mod file when downloaded."""

    mod_id: ModId
    """The mod identifier."""

    version: str
    """The version of the mod."""

    timestamp: int
    """The timestamp of the last update of the mod."""

    author: Optional[str]
    """The author of the mod."""

    uploader: Optional[str]
    """The uploader of the mod."""

    modpage_url: str
    """The url to the modpage of the mod."""
