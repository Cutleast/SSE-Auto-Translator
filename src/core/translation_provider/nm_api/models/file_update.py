"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel


class FileUpdate(BaseModel, frozen=True):
    """
    Model for file update objects returned by the Nexus Mods API "files" endpoint.
    """

    old_file_id: int
    """The id of the old file."""

    new_file_id: int
    """The id of the new file."""

    uploaded_timestamp: int
    """UTC timestamp when the new file was uploaded."""
