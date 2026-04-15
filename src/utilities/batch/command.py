"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class BatchCommand(BaseModel, frozen=True):
    """
    Model for a batch run command passed via CLI or JSON file.
    """

    run_basic_scan: bool = True
    """Whether to run the basic modlist scan."""

    translation_archives: list[Path] = []
    """
    List of translation archive paths (.7z, .zip, .rar) to import into the database
    before building the output mod.
    """

    build_output_mod: bool = True
    """Whether to build the output mod after all other steps."""

    output_path: Optional[Path] = None
    """Override for the output mod path. Falls back to app config if None."""
