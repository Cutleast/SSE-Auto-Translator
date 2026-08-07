"""
Copyright (c) Cutleast
"""

import logging
from concurrent.futures import Future, as_completed
from typing import Optional

from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
    update,
)
from cutleast_core_lib.core.multithreading.progress_executor import ProgressExecutor
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from PySide6.QtCore import QObject

from core.database.database_service import DatabaseService
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod_instance import ModInstance
from core.string.string_utils import StringUtils
from core.string.types import StringList

from .database import TranslationDatabase
from .translation import Translation


class DatabaseUpdater(QObject):
    """
    Class for updating the translations of a translation database based on the original
    mod files installed in the loaded mod instance.
    """

    __database: TranslationDatabase
    __mod_instance: ModInstance

    log: logging.Logger = logging.getLogger("DatabaseUpdater")

    def __init__(self, database: TranslationDatabase, mod_instance: ModInstance) -> None:
        """
        Args:
            database (TranslationDatabase): The translation database to update.
            mod_instance (ModInstance):
                The mod instance containing the original mod files.
        """

        super().__init__()

        self.__database = database
        self.__mod_instance = mod_instance

    def update_database_translations(
        self,
        keep_deleted: bool = False,
        add_missing_files: bool = True,
        thread_num: Optional[int] = None,
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> dict[ModFile, TranslationStatus]:
        """
        Updates all installed translations of a database based on the original mod files
        installed in the loaded mod instance.

        Args:
            keep_deleted (bool, optional):
                Whether to keep strings that are no longer present in an original mod
                file. Defaults to False.
            add_missing_files (bool, optional):
                Whether to add missing mod files to an existing translation covering
                their mod. Defaults to True.
            thread_num (Optional[int], optional):
                Maximum number of threads to use. Defaults to None (auto-detect).
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            dict[ModFile, TranslationStatus]:
                A dictionary mapping mod files to their new translation status after the
                update.
        """

        self.log.info(
            f"Updating {len(self.__database.user_translations)} translations in "
            "database..."
        )

        if pdisplay is not None:
            pdisplay.updateMainProgress(
                ProgressUpdate(status_text=self.tr("Updating database translations..."))
            )

        updated_modfile_states: dict[ModFile, TranslationStatus] = {}
        with ProgressExecutor(pdisplay, max_workers=thread_num) as executor:
            executor.set_main_progress_text(self.tr("Updating database translations..."))

            futures: dict[Future[dict[ModFile, TranslationStatus]], Translation] = {}
            for existing_translation in self.__database.user_translations:
                future: Future[dict[ModFile, TranslationStatus]] = executor.submit(
                    lambda uc, t=existing_translation: self.update_translation(
                        translation=t,
                        keep_deleted=keep_deleted,
                        update_callback=uc,
                    )
                )
                futures[future] = existing_translation

            for future in as_completed(futures):
                translation: Translation = futures[future]

                try:
                    updated_modfile_states.update(future.result())
                except Exception as ex:
                    self.log.error(
                        f"Failed to update translation '{translation.name}': {ex}",
                        exc_info=ex,
                    )

        if add_missing_files:
            added_files: list[ModFile] = self.__add_missing_modfiles(pdisplay)
            updated_modfile_states.update(
                {
                    modfile: TranslationStatus.TranslationIncomplete
                    for modfile in added_files
                }
            )

        self.log.info("Finished updating database translations.")

        return updated_modfile_states

    def update_translation(
        self,
        translation: Translation,
        keep_deleted: bool = False,
        update_callback: Optional[UpdateCallback] = None,
    ) -> dict[ModFile, TranslationStatus]:
        """
        Updates the strings of a translation based on the original mod files in the
        loaded mod instance. If `keep_deleted` is False, strings that are no longer
        present in the original mod file will be removed from the translation.

        Args:
            translation (Translation): The translation to update.
            keep_deleted (bool, optional):
                Whether to keep strings that are no longer present in the original mod
                file. Defaults to False.
            update_callback (Optional[UpdateCallback], optional):
                Optional update callback. Defaults to None.

        Returns:
            dict[ModFile, TranslationStatus]:
                A dictionary mapping mod files to their new translation status after the
                update.
        """

        self.log.debug(f"Updating translation '{translation.name}'...")

        updated_modfile_states: dict[ModFile, TranslationStatus] = {}
        for m, (modfile_path, strings) in enumerate(translation.strings.items()):
            modfile: Optional[ModFile] = self.__mod_instance.get_modfile(
                modfile_path, ignore_states=[TranslationStatus.IsTranslated]
            )
            if modfile is None:
                self.log.warning(f"Mod file '{modfile_path}' not found in modlist.")
                continue

            update(
                update_callback,
                ProgressUpdate(
                    status_text=(
                        f"{translation.name}: "
                        + self.tr("Updating translation strings...")
                        + f" ({m + 1}/{len(translation.strings)})"
                    ),
                    value=m,
                    maximum=len(translation.strings),
                ),
            )

            modfile_strings: StringList = modfile.get_strings()
            updated: bool = StringUtils.update_string_list(
                translation_strings=strings,
                original_strings=modfile_strings,
                keep_deleted=keep_deleted,
            )
            if updated:
                updated_modfile_states[modfile] = TranslationStatus.TranslationIncomplete

        if updated_modfile_states:
            translation.save()

        self.log.debug(
            f"Update of '{translation.name}' complete. Changes made: "
            f"{bool(updated_modfile_states)}"
        )

        return updated_modfile_states

    def __add_missing_modfiles(
        self, pdisplay: Optional[ProgressDisplay] = None
    ) -> list[ModFile]:
        if pdisplay is not None:
            pdisplay.updateMainProgress(
                ProgressUpdate(
                    status_text=self.tr("Adding missing mod files to translations..."),
                    value=0,
                    maximum=0,
                )
            )

        modfiles_added: list[ModFile] = []
        for mod in self.__mod_instance.mods:
            existing_translation: Optional[Translation] = (
                self.__database.get_translation_by_mod(mod)
            )
            if existing_translation is None:
                continue

            missing_modfiles: list[ModFile] = [
                modfile
                for modfile in mod.modfiles
                if modfile.path not in existing_translation.strings
                and modfile.status >= TranslationStatus.RequiresTranslation
            ]
            for missing_modfile in missing_modfiles:
                modfile_translation: Translation = (
                    DatabaseService.create_translation_for_modfile(
                        modfile=missing_modfile,
                        database=self.__database,
                        # we just merge it into the existing translation
                        add_and_save=False,
                    )
                )
                existing_translation.strings.update(modfile_translation.strings)
                self.log.debug(
                    f"Created new translation for mod file '{missing_modfile.path}' "
                    f"and added it to translation '{existing_translation.name}'."
                )

            if missing_modfiles:
                existing_translation.save()
                self.__database.changed_signal.emit(existing_translation)

            modfiles_added.extend(missing_modfiles)

        return modfiles_added
