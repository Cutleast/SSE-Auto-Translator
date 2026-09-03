"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class FileManifestFile(BaseModel, frozen=True):
    """
    Model for a single file entry in the file manifest.
    """

    path: Path = Field(alias="file_path")
    """The path to the file, relative to the archive's root."""

    size: int = Field(alias="file_size")
    """The size of the file in bytes."""


class FileManifest(BaseModel, frozen=True):
    """
    Model for the file manifest returned by Nexus Mods' new file content preview system.
    """

    version: Literal[1] = 1
    """The manifest version. Currently, only version 1 is supported."""

    files: list[FileManifestFile]
    """The list of files in the manifest."""
