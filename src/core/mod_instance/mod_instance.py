"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import QObject, Signal

from app_context import AppContext
from core.cache.cache import Cache
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.translation_provider.mod_id import ModId
from core.utilities.container_utils import unique

from .mod import Mod


class ModInstance(QObject):
    """
    Class to represent a loaded modlist.
    """

    update_signal = Signal()
    """
    This signal gets emitted everytime, the status of one or more mod files changes.
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
        super().__init__()

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
        modfile_name: str,
        ignore_mods: list[Mod] = [],
        ignore_states: list[TranslationStatus] = [],
        ignore_case: bool = False,
    ) -> Optional[ModFile]:
        """
        Get a mod file by its name or None if it doesn't exist.
        Returns the mod file with the highest index if there are
        multiple mod files with the same name.

        Args:
            modfile_name (str): Name of the mod file
            ignore_mods (list[Mod], optional): List of mods to ignore. Defaults to [].
            ignore_states (list[TranslationStatus], optional):
                List of mod file states to ignore. Defaults to [].
            ignore_case (bool, optional): Whether to ignore case. Defaults to False.

        Returns:
            Optional[ModFile]: Mod file or None
        """

        mods: dict[Mod, ModFile] = {
            mod: modfile
            for mod in filter(lambda m: m not in ignore_mods, self.mods)
            for modfile in filter(lambda m: m.status not in ignore_states, mod.modfiles)
            if modfile.name == modfile_name
            or (ignore_case and modfile.name.lower() == modfile_name.lower())
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
        modfile_name: str,
        ignore_mods: list[Mod] = [],
        ignore_states: list[TranslationStatus] = [],
        ignore_case: bool = False,
    ) -> Optional[Mod]:
        """
        Get a mod that has the specified mod file or None if it doesn't exist.
        Returns the mod with the highest index if there are
        multiple mods with the same mod file.

        Args:
            modfile_name (str): Name of the mod file
            ignore_mods (list[Mod], optional): List of mods to ignore. Defaults to [].
            ignore_states (list[TranslationStatus], optional):
                List of mod file states to ignore. Defaults to [].
            ignore_case (bool, optional): Whether to ignore case. Defaults to False.

        Returns:
            Optional[Mod]: Mod or None
        """

        mods: list[Mod] = unique(
            mod
            for mod in filter(lambda m: m not in ignore_mods, self.mods)
            for modfile in filter(lambda m: m.status not in ignore_states, mod.modfiles)
            if modfile.name == modfile_name
            or (ignore_case and modfile.name.lower() == modfile_name.lower())
        )

        # Get the mod with the highest modlist index
        return max(mods, key=lambda m: self.mods.index(m), default=None)

    def get_modfile_state_summary(
        self, modfiles: Optional[list[ModFile]] = None
    ) -> dict[TranslationStatus, int]:
        """
        Gets a summary of the mod file states.

        Args:
            modfiles (Optional[list[ModFile]], optional):
                List of mod files to count. Defaults to the entire modlist.

        Returns:
            dict[TranslationStatus, int]: Summary of the mod file states
        """

        modfiles = modfiles or self.modfiles

        return {
            state: len([modfile for modfile in modfiles if modfile.status == state])
            for state in TranslationStatus
        }

    def load_states_from_cache(self) -> dict[ModFile, bool]:
        """
        Loads the mod file states from the cache and applies them.

        Returns:
            dict[ModFile, bool]: Dictionary of mod files and their checkstate.
        """

        cache: Cache = AppContext.get_app().cache
        check_state: dict[ModFile, bool] = {}

        for mod in self.mods:
            for modfile in mod.modfiles:
                checked, modfile.status = cache.get_from_states_cache(modfile.path) or (
                    True,
                    TranslationStatus.NoneStatus,
                )
                check_state[modfile] = checked

        self.update_signal.emit()

        return check_state

    def set_modfile_states(self, states: dict[ModFile, TranslationStatus]) -> None:
        """
        Applies the given mod file states to the modlist and emits the update signal.

        Args:
            states (dict[ModFile, TranslationStatus]):
                Dictionary of mod files and their states
        """

        for modfile, state in states.items():
            modfile.status = state

        self.update_signal.emit()
