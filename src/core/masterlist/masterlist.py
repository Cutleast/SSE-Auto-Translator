"""
Copyright (c) Cutleast
"""

from typing import Any, Optional

from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass

from app_context import AppContext

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

    @property
    def user_ignore_list(self) -> list[str]:
        """
        User-configured ignore list for file names.
        """

        if AppContext.has_app():
            return AppContext.get_app().user_config.plugin_ignorelist
        else:
            return []

    def is_ignored(self, file_name: str) -> bool:
        """
        Checks if a file is on the ignore list (masterlist or user).

        Args:
            file_name (str): Name of the file.

        Returns:
            bool: Whether the file is ignored.
        """

        masterlist_entry: Optional[MasterlistEntry] = self.entries.get(
            file_name.lower()
        )

        return file_name.lower() in self.user_ignore_list or (
            masterlist_entry is not None
            and masterlist_entry.type == MasterlistEntry.Type.Ignore
        )

    def add_to_ignore_list(self, file_name: str) -> None:
        """
        Adds a file to the user ignore list if it doesn't already exist.

        Args:
            file_name (str): Name of the file.
        """

        if file_name.lower() not in self.user_ignore_list:
            self.user_ignore_list.append(file_name.lower())

    def remove_from_ignore_list(self, file_name: str) -> None:
        """
        Removes a file from the user ignore list if it exists.

        Args:
            file_name (str): Name of the file.
        """

        if file_name.lower() in self.user_ignore_list:
            self.user_ignore_list.remove(file_name.lower())
