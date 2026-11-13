"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel


class ContextProperty(BaseModel, frozen=True):
    """
    A single labeled fact describing the context of a string, like its speaker.
    """

    label: str
    """The localized label of the property."""

    value: str
    """The display value of the property."""
