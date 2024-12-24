"""
Copyright (c) Cutleast
"""

from typing import Any

from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass

from .masterlist_entry import MasterlistEntry


@dataclass
class Masterlist:
    """
    Class for translation masterlists.
    """

    entries: dict[str, MasterlistEntry]
    """
    Map of file names and their masterlist entries.
    """

    @staticmethod
    def from_data(data: dict[str, dict[str, Any]]) -> "Masterlist":
        return Masterlist(TypeAdapter(dict[str, MasterlistEntry]).validate_python(data))
