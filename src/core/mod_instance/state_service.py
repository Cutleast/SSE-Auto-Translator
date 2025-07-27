"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.cache.cache import Cache
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus

from .mod_instance import ModInstance


class StateService(QObject):
    """
    Class for managing and updating the mod file states of a modinstance.
    """

    update_signal = Signal()
    """Signal emitted everytime when the mod file states are updated."""

    cache: Cache
    """The application cache."""

    mod_instance: ModInstance
    """The modinstance with the mod files to update."""

    database: TranslationDatabase
    """The database with the installed translations."""

    log: logging.Logger = logging.getLogger("StateService")

    def __init__(
        self, cache: Cache, modinstance: ModInstance, database: TranslationDatabase
    ) -> None:
        """
        Args:
            cache (Cache): The application cache.
            modinstance (ModInstance): The modinstance with the mod files to update.
            database (TranslationDatabase): The database with the installed translations.
        """

        super().__init__()

        self.cache = cache
        self.mod_instance = modinstance
        self.database = database

        self.database.add_signal.connect(self.__on_translation_added)
        self.database.remove_signal.connect(self.__on_translation_removed)

    def __on_translation_added(self, translation: Translation) -> None:
        """
        Handles the event when a translation is added to the database.

        Args:
            translation (Translation): The added translation.
        """

        self.log.debug(
            f"Translation '{translation.name}' added to database. Updating affected "
            "mod file states..."
        )

        modfile_states: dict[ModFile, TranslationStatus] = {}
        for modfile in translation.strings:
            original_modfile: Optional[ModFile] = self.mod_instance.get_modfile(
                modfile,
                ignore_states=[
                    TranslationStatus.TranslationInstalled,
                    TranslationStatus.IsTranslated,
                ],
            )

            if original_modfile is not None:
                modfile_states[original_modfile] = (
                    TranslationStatus.TranslationInstalled
                )

        self.set_modfile_states(modfile_states)

    def __on_translation_removed(self, translation: Translation) -> None:
        """
        Handles the event when a translation is removed from the database.

        Args:
            translation (Translation): The removed translation.
        """

        self.log.debug(
            f"Translation '{translation.name}' removed from database. Updating affected "
            "mod file states..."
        )

        modfile_states: dict[ModFile, TranslationStatus] = {}
        for modfile in translation.strings.keys():
            original_modfile: Optional[ModFile] = self.mod_instance.get_modfile(
                modfile, ignore_states=[TranslationStatus.IsTranslated]
            )
            if original_modfile is not None:
                modfile_states[original_modfile] = TranslationStatus.RequiresTranslation

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

        check_state: dict[ModFile, bool] = {}

        for mod in self.mod_instance.mods:
            for modfile in mod.modfiles:
                checked, modfile.status = self.cache.get_from_states_cache(
                    modfile.full_path
                ) or (
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

        self.log.debug(f"Updated states for {len(states)} mod file(s).")

        self.update_signal.emit()

    def reevaluate_states(self) -> None:
        """
        Reevaluates the mod file states and emits the update signal.
        """

        # TODO: Implement this
        raise NotImplementedError
