"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel


class DatabaseReloadResult(BaseModel, frozen=True):
    """
    Summarizes the outcome of reloading a translation database from disk.
    """

    reloaded: int
    """The number of translations that were already in the database and got reloaded."""

    added: int
    """The number of translations that were added to the database."""

    removed: int
    """The number of translations that were removed from the database."""

    failed: int
    """The number of translations that failed to load and were left unchanged."""
