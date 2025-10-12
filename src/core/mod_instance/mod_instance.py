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

    def __init__(self, display_name: str, mods: list[Mod]) -> None:
        self.display_name = display_name
        self.mods = mods

    @property
    def modfiles(self) -> list[ModFile]:
        """
        List of all translatable mod files in this instance.
        """

        return [modfile for mod in self.mods for modfile in mod.modfiles]

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

        modfiles: list[ModFile] = self.get_modfiles(modfile, ignore_mods, ignore_states)
        return modfiles[-1] if modfiles else None

    def get_modfiles(
        self,
        modfile: Path,
        ignore_mods: list[Mod] = [],
        ignore_states: list[TranslationStatus] = [],
    ) -> list[ModFile]:
        """
        Gets a list of mod files that match a given path. Returns them sorted in order
        of modlist index (higher index overwrites lower index).

        Args:
            modfile (Path): Path of the mod file, relative to the game's "Data" folder.
            ignore_mods (list[Mod], optional): List of mods to ignore. Defaults to [].
            ignore_states (list[TranslationStatus], optional):
                List of mod file states to ignore. Defaults to [].

        Returns:
            list[ModFile]: List of mod files
        """

        mods: dict[Mod, ModFile] = {
            mod: mf
            for mod in filter(lambda m: m not in ignore_mods, self.mods)
            for mf in filter(lambda mf: mf.status not in ignore_states, mod.modfiles)
            if mf.path == modfile
        }

        return [
            mf
            for _, mf in sorted(mods.items(), key=lambda item: self.mods.index(item[0]))
        ]

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
