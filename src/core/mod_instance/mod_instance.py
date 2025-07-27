"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.translation_provider.mod_id import ModId
from core.utilities.container_utils import unique

from .mod import Mod


class ModInstance:
    """
    Class to represent a loaded modlist.
    """

    display_name: str
    """
    Display name of this instance.
    """

    mods: list[Mod]
    """
    List of all installed mods in this instance.
    """

    __selected_modfiles: Optional[list[ModFile]] = None
    __selected_mods: Optional[list[Mod]] = None

    def __init__(self, display_name: str, mods: list[Mod]) -> None:
        self.display_name = display_name
        self.mods = mods

    @property
    def modfiles(self) -> list[ModFile]:
        """
        List of all translatable mod files in this instance.
        """

        return [modfile for mod in self.mods for modfile in mod.modfiles]

    @property
    def selected_modfiles(self) -> list[ModFile]:
        """
        List of all mod files that are currently selected
        or all mod files if none are selected.
        """

        return self.__selected_modfiles or self.modfiles

    @selected_modfiles.setter
    def selected_modfiles(self, value: Optional[list[ModFile]]) -> None:
        self.__selected_modfiles = value

    @property
    def selected_mods(self) -> list[Mod]:
        """
        List of all mods that are currently selected
        or all mods if none are selected.
        """

        return self.__selected_mods or self.mods

    @selected_mods.setter
    def selected_mods(self, value: Optional[list[Mod]]) -> None:
        self.__selected_mods = value

    @property
    def selected_items(self) -> dict[Mod, list[ModFile]]:
        """
        Dictionary of mods and their mod files that are currently selected.
        """

        return {
            mod: [
                modfile for modfile in mod.modfiles if modfile in self.selected_modfiles
            ]
            for mod in self.selected_mods
        }

    def get_modfile(
        self,
        modfile: Path,
        ignore_mods: list[Mod] = [],
        ignore_states: list[TranslationStatus] = [],
    ) -> Optional[ModFile]:
        """
        Get a mod file by its name or None if it doesn't exist.
        Returns the mod file with the highest index if there are
        multiple mod files with the same name.

        Args:
            modfile (Path): Path of the mod file, relative to the game's "Data" folder.
            ignore_mods (list[Mod], optional): List of mods to ignore. Defaults to [].
            ignore_states (list[TranslationStatus], optional):
                List of mod file states to ignore. Defaults to [].

        Returns:
            Optional[ModFile]: Mod file or None
        """

        mods: dict[Mod, ModFile] = {
            mod: mf
            for mod in filter(lambda m: m not in ignore_mods, self.mods)
            for mf in filter(lambda mf: mf.status not in ignore_states, mod.modfiles)
            if mf.path == modfile
        }

        # Get the mod file from the mod with the highest modlist index
        return max(
            mods.items(),
            key=lambda item: self.mods.index(item[0]),
            default=(None, None),
        )[1]

    def get_mod(self, mod_id: ModId) -> Optional[Mod]:
        """
        Get a mod by its id or None if it doesn't exist.
        Returns the mod with the highest index if there are
        multiple mods with the same id.

        Args:
            mod_id (int): Mod identifier.
            file_id (Optional[int], optional): File id. Defaults to None.

        Returns:
            Optional[Mod]: Mod or None
        """

        mods: list[Mod] = unique(
            mod for mod in filter(lambda m: (m.mod_id == mod_id), self.mods)
        )

        # Get the mod with the highest modlist index
        return max(mods, key=lambda m: self.mods.index(m), default=None)

    def get_mod_with_modfile(
        self,
        modfile: Path,
        ignore_mods: list[Mod] = [],
        ignore_states: list[TranslationStatus] = [],
    ) -> Optional[Mod]:
        """
        Get a mod that has the specified mod file or None if it doesn't exist.
        Returns the mod with the highest index if there are
        multiple mods with the same mod file.

        Args:
            modfile_name (Path):
                Path of the mod file, relative to the game's "Data" folder.
            ignore_mods (list[Mod], optional): List of mods to ignore. Defaults to [].
            ignore_states (list[TranslationStatus], optional):
                List of mod file states to ignore. Defaults to [].

        Returns:
            Optional[Mod]: Mod or None
        """

        mods: list[Mod] = unique(
            mod
            for mod in filter(lambda m: m not in ignore_mods, self.mods)
            for mf in filter(lambda mf: mf.status not in ignore_states, mod.modfiles)
            if mf.path == modfile
        )

        # Get the mod with the highest modlist index
        return max(mods, key=lambda m: self.mods.index(m), default=None)
