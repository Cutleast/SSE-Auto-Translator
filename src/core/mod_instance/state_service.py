"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.cache.cache import Cache
from PySide6.QtCore import QObject, Signal

from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus

from .mod_instance import ModInstance

StateCache = dict[Path, tuple[bool, TranslationStatus]]


class StateService(QObject):
    """
    Class for managing and updating the mod file states of a modinstance.
    """

    update_signal = Signal()
    """Signal emitted everytime when the mod file states are updated."""

    mod_instance: ModInstance
    """The modinstance with the mod files to update."""

    database: TranslationDatabase
    """The database with the installed translations."""

    CACHE_FILE_NAME = Path("modfile_states.cache")
    """The name of the cache file for the mod file states."""

    log: logging.Logger = logging.getLogger("StateService")

    def __init__(self, modinstance: ModInstance, database: TranslationDatabase) -> None:
        """
        Args:
            modinstance (ModInstance): The modinstance with the mod files to update.
            database (TranslationDatabase): The database with the installed translations.
        """

        super().__init__()

        self.mod_instance = modinstance
        self.database = database

        self.database.add_signal.connect(self.__on_translations_added)
        self.database.remove_signal.connect(self.__on_translations_removed)

    def __on_translations_added(self, translations: list[Translation]) -> None:
        """
        Handles the event when at least one translation is added to the database.

        Args:
            translations (list[Translation]): The added translations.
        """

        self.log.debug(
            f"Updating mod file states for {len(translations)} added translation(s)..."
        )

        modfile_states: dict[ModFile, TranslationStatus] = {}
        for translation in translations:
            self.log.debug(
                f"Translation '{translation.name}' added to database. Updating affected "
                "mod file states..."
            )

            for modfile in translation.strings:
                original_modfiles: list[ModFile] = self.mod_instance.get_modfiles(
                    modfile,
                    ignore_states=[
                        TranslationStatus.TranslationInstalled,
                        TranslationStatus.IsTranslated,
                    ],
                )

                for original_modfile in original_modfiles:
                    modfile_states[original_modfile] = (
                        TranslationStatus.TranslationInstalled
                    )

        self.set_modfile_states(modfile_states)

    def __on_translations_removed(self, translations: list[Translation]) -> None:
        """
        Handles the event when at least one translation is removed from the database.

        Args:
            translations (list[Translation]): The removed translations.
        """

        self.log.debug(
            f"Updating mod file states for {len(translations)} removed translation(s)..."
        )

        modfile_states: dict[ModFile, TranslationStatus] = {}
        for translation in translations:
            self.log.debug(
                f"Translation '{translation.name}' removed from database. Updating "
                "affected mod file states..."
            )

            for modfile in translation.strings.keys():
                original_modfiles: list[ModFile] = self.mod_instance.get_modfiles(
                    modfile, ignore_states=[TranslationStatus.IsTranslated]
                )

                if original_modfiles:
                    for original_modfile in original_modfiles:
                        modfile_states[original_modfile] = (
                            TranslationStatus.RequiresTranslation
                        )
                else:
                    self.log.warning(f"Found no original mod file for '{modfile}'!")

        self.set_modfile_states(modfile_states)

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

        modfiles = modfiles or self.mod_instance.modfiles

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

        modfile_states: StateCache = Cache.get_from_cache(
            StateService.CACHE_FILE_NAME, default={}
        )

        check_state: dict[ModFile, bool] = {}
        for mod in self.mod_instance.mods:
            for modfile in mod.modfiles:
                checked: bool
                modfile_status: TranslationStatus
                if modfile.full_path in modfile_states:
                    checked, modfile_status = modfile_states[modfile.full_path]
                else:
                    checked = True
                    modfile_status = TranslationStatus.NoneStatus

                modfile.status = modfile_status
                check_state[modfile] = checked

        self.update_signal.emit()

        return check_state

    def save_states_to_cache(self, check_states: dict[ModFile, bool]) -> None:
        """
        Saves the mod file states to the cache.

        Args:
            check_states (dict[ModFile, bool]): Dictionary of mod files and their checkstate.
        """

        state_cache: StateCache = {
            modfile.full_path: (check_states.get(modfile, True), modfile.status)
            for modfile in self.mod_instance.modfiles
        }

        Cache.save_to_cache(StateService.CACHE_FILE_NAME, state_cache)

        self.log.info("Saved mod file states to cache.")

    def set_modfile_states(self, states: dict[ModFile, TranslationStatus]) -> None:
        """
        Applies the given mod file states to the modlist and emits the update signal.

        Args:
            states (dict[ModFile, TranslationStatus]):
                Dictionary of mod files and their states
        """

        for modfile, state in states.items():
            modfile.status = state

        self.log.debug(f"Updated states for {len(states)} mod file(s).")

        self.update_signal.emit()

    def reevaluate_states(self) -> None:
        """
        Reevaluates the mod file states and emits the update signal.
        """

        # TODO: Implement this
        raise NotImplementedError
