"""
Copyright (c) Cutleast
"""

import logging
from typing import Any, Optional, Self

import jstyleson as json
from cutleast_core_lib.core.utilities.web_utils import get_raw_web_content
from pydantic import BaseModel, PrivateAttr, TypeAdapter

from core.config.user_config import UserConfig
from core.utilities.constants import AE_CC_PLUGINS, BASE_GAME_PLUGINS
from core.utilities.game_language import GameLanguage

from .masterlist_entry import MasterlistEntry

REPOSITORY_URL: str = "https://raw.githubusercontent.com/Cutleast/SSE-Auto-Translator/master/masterlists/index.json"
"""URL to the masterlist index file in the GitHub repository."""

log: logging.Logger = logging.getLogger("Masterlist")


class Masterlist(BaseModel):
    """
    Class for translation masterlists.
    """

    entries: dict[str, MasterlistEntry]
    """
    Map of file names and their masterlist entries.
    """

    __user_config: Optional[UserConfig] = PrivateAttr(default=None)

    @classmethod
    def from_data(cls, data: dict[str, dict[str, Any]]) -> Self:
        """
        Creates a Masterlist instance from a dictionary of data.

        Args:
            data (dict[str, dict[str, Any]]): Dictionary containing masterlist data.

        Returns:
            Self: A Masterlist instance created from the provided data.
        """

        return cls(entries=TypeAdapter(dict[str, MasterlistEntry]).validate_python(data))

    @classmethod
    def load_from_repo(cls, language: GameLanguage) -> Self:
        """
        Loads the masterlist from the repository.

        Args:
            language (GameLanguage): Language to load the masterlist for.

        Returns:
            Masterlist: Loaded masterlist.
        """

        log.info(
            f"Loading masterlist from repository at '{REPOSITORY_URL}' for language "
            f"'{language.name}'..."
        )

        data: bytes = get_raw_web_content(REPOSITORY_URL)
        index: dict[str, str] = json.loads(data.decode())

        url: Optional[str] = index.get(language.id)

        if url is None:
            log.warning(f"No masterlist available for language '{language.name}'.")
            return cls(entries={})

        data = get_raw_web_content(url)
        json_data: dict[str, dict[str, Any]] = json.loads(data.decode())
        masterlist: Self = cls.from_data(json_data)

        log.info(f"Loaded masterlist with {len(masterlist.entries)} entries.")

        return masterlist

    @property
    def user_ignore_list(self) -> list[str]:
        """
        User-configured ignore list for file names.
        """

        if self.__user_config is None:
            return []

        return self.__user_config.modfile_ignorelist

    def set_user_config(self, user_config: UserConfig) -> None:
        """
        Sets the user configuration used by this masterlist.

        Args:
            user_config (UserConfig): User configuration containing the ignore list.
        """

        self.__user_config = user_config

    def is_ignored(self, file_name: str) -> bool:
        """
        Checks if a file is on the ignore list (masterlist or user).

        Args:
            file_name (str): Name of the file.

        Returns:
            bool: Whether the file is ignored.
        """

        masterlist_entry: Optional[MasterlistEntry] = self.entries.get(file_name.lower())

        ignore_list: list[str] = self.user_ignore_list.copy()
        ignore_list.extend(BASE_GAME_PLUGINS)
        ignore_list.extend(AE_CC_PLUGINS)

        return file_name.lower() in ignore_list or (
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
