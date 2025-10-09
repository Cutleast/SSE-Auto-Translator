"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel, Field

from .file_update import FileUpdate
from .nm_file import NmFile


class NmFiles(BaseModel, frozen=True):
    """
    Model for the combined response returned by the Nexus Mods API "files" endpoint.
    """

    files: list[NmFile]
    """List of the mod files."""

    updates: list[FileUpdate] = Field(alias="file_updates")
    """List of the mod file updates."""
