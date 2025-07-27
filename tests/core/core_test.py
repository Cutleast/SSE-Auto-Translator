"""
Copyright (c) Cutleast
"""

import logging

from core.database.string import String
from core.mod_file.mod_file import ModFile
from core.mod_instance.mod import Mod

from ..app_test import AppTest


class CoreTest(AppTest):
    """
    Base class for all core-related tests.
    """

    log: logging.Logger = logging.getLogger("CoreTest")

    def get_mod_by_name(self, mod_name: str) -> Mod:
        """
        Gets a mod by its name from the loaded mod instance.

        Args:
            mod_name (str): The name of the mod

        Raises:
            ValueError: When no mod with the specified name is found

        Returns:
            Mod: The mod
        """

        try:
            mod: Mod = next(
                (mod for mod in self.modinstance().mods if mod.name == mod_name)
            )
        except StopIteration:
            raise ValueError(f"No mod with name {mod_name} found in mod instance.")

        return mod

    def get_modfile_from_mod(self, mod: Mod, modfile_name: str) -> ModFile:
        """
        Gets a mod file by its name from the specified mod.

        Args:
            mod (Mod): Mod to get mod file from
            modfile_name (str): The name of the mod file

        Returns:
            ModFile: The mod file
        """

        try:
            modfile: ModFile = next((m for m in mod.modfiles if m.name == modfile_name))
        except StopIteration:
            raise ValueError(f"No mod file with name {modfile_name} found in mod.")

        return modfile

    def get_modfile_from_mod_name(self, mod_name: str, modfile_name: str) -> ModFile:
        """
        Gets a mod file by its name from the specified mod.

        Args:
            mod_name (str): Name of the mod to get mod file from
            modfile_name (str): The name of the mod file

        Raises:
            ValueError: When no mod with the specified name is found
            ValueError: When no mod file with the specified name is found

        Returns:
            ModFile: The mod file
        """

        mod: Mod = self.get_mod_by_name(mod_name)

        return self.get_modfile_from_mod(mod, modfile_name)

    @staticmethod
    def calc_unique_string_hash(string: String) -> int:
        """
        Calculates a unique hash value from the specified string including all fields.

        Args:
            string (String): The string to calculate the hash value from.

        Returns:
            int: The unique hash value.
        """

        return hash(
            (
                string.form_id,
                string.editor_id,
                string.type,
                string.original,
                string.index,
                string.string,
                string.status,
            )
        )
