"""
Copyright (c) Cutleast
"""

import logging
from concurrent.futures import Future, as_completed
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
    update,
)
from cutleast_core_lib.core.multithreading.progress_executor import ProgressExecutor
from cutleast_core_lib.core.utilities.unique import unique
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from PySide6.QtCore import QObject

from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.translation import Translation
from core.masterlist.masterlist import Masterlist
from core.masterlist.masterlist_entry import MasterlistEntry
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.string.search_filter import SearchFilter, matches_filter
from core.string.string_extractor import StringExtractor
from core.string.string_status import StringStatus
from core.string.string_utils import StringUtils
from core.string.types import StringList
from core.translation_provider.mod_id import ModId
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.source import Source

from .detector import LangDetector, Language


class Scanner(QObject):
    """
    Class for various scanning actions on the loaded modlist.
    """

    log: logging.Logger = logging.getLogger("Scanner")

    mod_instance: ModInstance
    database: TranslationDatabase
    app_config: AppConfig
    user_config: UserConfig
    provider: TranslationProvider
    masterlist: Masterlist
    detector: LangDetector

    def __init__(
        self,
        mod_instance: ModInstance,
        database: TranslationDatabase,
        app_config: AppConfig,
        user_config: UserConfig,
        provider: TranslationProvider,
        masterlist: Masterlist,
    ) -> None:
        """
        Args:
            mod_instance (ModInstance): The loaded mod instance.
            database (TranslationDatabase): The translation database.
            app_config (AppConfig): The application configuration.
            user_config (UserConfig): The user configuration.
            provider (TranslationProvider): The translation provider.
            masterlist (Masterlist): The loaded masterlist.
        """

        super().__init__()

        self.mod_instance = mod_instance
        self.database = database
        self.app_config = app_config
        self.user_config = user_config
        self.provider = provider
        self.masterlist = masterlist
        self.detector = LangDetector(
            self.app_config.detector_confidence,
            getattr(Language, self.user_config.language.id.upper()),
        )

    def run_basic_scan(
        self, items: dict[Mod, list[ModFile]], pdisplay: Optional[ProgressDisplay] = None
    ) -> dict[Mod, dict[ModFile, TranslationStatus]]:
        """
        Scans mods for required and installed translations.
        Automatically imports installed translations if enabled by the user.

        Args:
            items (dict[Mod, list[ModFile]]): The items to scan.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            dict[Mod, dict[ModFile, TranslationStatus]]:
                A dictionary of mods, their mod files and their status.
        """

        total_modfiles: int = sum(len(modfiles) for modfiles in items.values())
        self.log.info(
            f"Scanning {len(items)} mod(s) with {total_modfiles} mod file(s)..."
        )

        if pdisplay is not None:
            pdisplay.updateMainProgress(
                ProgressUpdate(
                    status_text=self.tr("Scanning modlist..."), value=0, maximum=0
                )
            )

        database_strings: StringList = StringUtils.unique(
            string
            for string in self.database.strings
            if string.status != StringStatus.TranslationRequired
        )
        database_originals: list[str] = unique(
            string.original for string in database_strings
        )

        scan_result: dict[Mod, dict[ModFile, TranslationStatus]] = {}
        failed_modfiles: int = 0
        with ProgressExecutor(
            pdisplay, max_workers=self.app_config.worker_thread_num
        ) as executor:
            executor.set_main_progress_text(self.tr("Scanning modlist..."))

            tasks: dict[Future[TranslationStatus], tuple[Mod, ModFile]] = {}
            for mod, modfiles in items.items():
                scan_result[mod] = {}

                for modfile in modfiles:
                    future: Future[TranslationStatus] = executor.submit(
                        lambda ucb, m=mod, mf=modfile: self.__basic_scan_modfile(
                            mod=m,
                            modfile=mf,
                            database_strings=database_strings,
                            database_originals=database_originals,
                            update_callback=ucb,
                        )
                    )
                    tasks[future] = (mod, modfile)

            for future in as_completed(tasks):
                mod, modfile = tasks[future]
                try:
                    scan_result[mod][modfile] = future.result()
                except Exception as ex:
                    failed_modfiles += 1
                    self.log.error(
                        f"Failed to scan '{mod.name}' > '{modfile.name}': {ex}",
                        exc_info=ex,
                    )

        self.log.info("Modlist scan complete.")
        self.log.info(f"Status summary: {self.__create_status_summary(scan_result)}")

        return scan_result

    def __basic_scan_modfile(
        self,
        mod: Mod,
        modfile: ModFile,
        database_strings: StringList,
        database_originals: list[str],
        update_callback: Optional[UpdateCallback] = None,
    ) -> TranslationStatus:
        modfile_path_text: str = f"{mod.name} > {modfile.name}"
        self.log.debug(f"Scanning {modfile_path_text}...")

        update(
            update_callback,
            ProgressUpdate(
                status_text=self.tr("{item_name}: Extracting strings...").format(
                    item_name=modfile_path_text
                ),
                value=0,
                maximum=0,
            ),
        )

        self.log.debug("Extracting strings...")
        modfile_strings: StringList = list(
            filter(
                lambda s: s.status != StringStatus.NoTranslationRequired,
                modfile.get_strings(),
            )
        )
        if not len(modfile_strings):
            return TranslationStatus.NoStrings

        update(
            update_callback,
            ProgressUpdate(
                status_text=self.tr("{item_name}: Detecting language...").format(
                    item_name=modfile_path_text
                ),
            ),
        )

        self.log.debug("Detecting language...")

        status: TranslationStatus
        if self.detector.requires_translation(modfile_strings):
            if self.database.get_translation_by_modfile_path(modfile.path) is not None:
                status = TranslationStatus.TranslationInstalled

            elif any(
                string.original not in database_originals
                and string not in database_strings
                for string in modfile_strings
            ):
                status = TranslationStatus.RequiresTranslation
            else:
                status = TranslationStatus.TranslationAvailableInDatabase

        else:
            status = TranslationStatus.IsTranslated
            self.log.debug("Mod file is already translated.")

        return status

    def run_online_scan(
        self,
        items: dict[Mod, list[ModFile]],
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> dict[Mod, dict[ModFile, TranslationStatus]]:
        """
        Scans online for available translations.

        Args:
            items (dict[Mod, list[ModFile]]): The items to scan.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            dict[Mod, dict[ModFile, TranslationStatus]]:
                A dictionary of mods, their mod files and their status.
        """

        if pdisplay is not None:
            pdisplay.updateMainProgress(
                ProgressUpdate(
                    status_text=self.tr("Scanning online for available translations..."),
                    value=0,
                    maximum=0,
                )
            )

        scan_result: dict[Mod, dict[ModFile, TranslationStatus]] = {}

        relevant_items: dict[Mod, list[ModFile]] = {}
        for mod, modfiles in items.items():
            relevant_modfiles: list[ModFile] = [
                modfile
                for modfile in modfiles
                if modfile.status == TranslationStatus.RequiresTranslation
            ]
            if not relevant_modfiles:
                continue

            if mod.mod_id is not None and self.provider.is_mod_id_valid(
                mod.mod_id, check_online=False
            ):
                relevant_items[mod] = relevant_modfiles

            # mod's source is unknown => no translation available
            else:
                scan_result[mod] = {
                    modfile: TranslationStatus.NoTranslationAvailable
                    for modfile in modfiles
                }

        self.log.info(
            "Scanning online for available translations "
            f"for {len(relevant_items)} mod(s)..."
        )

        with ProgressExecutor(
            pdisplay, max_workers=self.app_config.worker_thread_num
        ) as executor:
            executor.set_main_progress_text(
                self.tr("Scanning online for available translations...")
            )

            tasks: dict[Future[dict[ModFile, TranslationStatus]], Mod] = {}
            for mod, modfiles in relevant_items.items():
                future: Future[dict[ModFile, TranslationStatus]] = executor.submit(
                    # this lambda is necessary as it gets an update callable as first
                    # positional argument
                    lambda ucb, m=mod, mfs=modfiles: self.__online_scan_mod(m, mfs, ucb)
                )
                tasks[future] = mod

            for future in as_completed(tasks):
                mod: Mod = tasks[future]
                try:
                    mod_scan_result: dict[ModFile, TranslationStatus] = future.result()
                    scan_result[mod] = mod_scan_result
                except Exception as ex:
                    self.log.error(f"Failed to scan for '{mod.name}': {ex}", exc_info=ex)

        self.log.info("Online scan complete.")
        self.log.info(f"Status summary: {self.__create_status_summary(scan_result)}")

        return scan_result

    def __online_scan_mod(
        self,
        mod: Mod,
        modfiles: list[ModFile],
        update_callback: Optional[UpdateCallback] = None,
    ) -> dict[ModFile, TranslationStatus]:
        if mod.mod_id is None:
            return {}

        result: dict[ModFile, TranslationStatus] = {}
        for m, modfile in enumerate(modfiles):
            update(
                update_callback,
                ProgressUpdate(
                    status_text=f"{mod.name} > {modfile.name} ({m}/{len(modfiles)})",
                    value=m,
                    maximum=len(modfiles),
                ),
            )

            self.log.debug(f"Scanning for '{mod.name}' > '{modfile.name}'...")
            try:
                result[modfile] = self.__online_scan_modfile(mod.mod_id, modfile)
            except Exception as ex:
                self.log.error(
                    f"Failed to scan for '{mod.name}' > '{modfile.name}': {ex}",
                    exc_info=ex,
                )
                result[modfile] = TranslationStatus.NoTranslationAvailable

        return result

    def __online_scan_modfile(
        self, mod_id: ModId, modfile: ModFile
    ) -> TranslationStatus:
        available_translations: dict[Source, list[ModId]] = (
            self.provider.get_translations(
                mod_id,
                modfile.name,
                self.user_config.language.id,
                self.masterlist,
                self.user_config.author_blacklist,
            )
        )

        masterlist_entry: Optional[MasterlistEntry] = self.masterlist.entries.get(
            modfile.name.lower()
        )

        if (
            masterlist_entry is not None
            and masterlist_entry.type == MasterlistEntry.Type.Route
            and masterlist_entry.targets
        ):
            self.log.debug(
                f"Found route entry for mod file '{modfile.name}' in masterlist."
            )
            return TranslationStatus.TranslationAvailableOnline

        if len(available_translations):
            return TranslationStatus.TranslationAvailableOnline
        else:
            return TranslationStatus.NoTranslationAvailable

    def run_string_search(
        self,
        items_to_search: dict[Mod, list[ModFile]],
        filter: SearchFilter,
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> dict[Path, StringList]:
        """
        Searches the modlist for strings.

        Args:
            items_to_search (dict[Mod, list[ModFile]]): The items to search.
            filter (SearchFilter): The search filter.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            dict[Path, StringList]:
                A dictionary of mod file names and their matching strings.
        """

        relevant_items: dict[Mod, list[ModFile]] = {
            mod: [
                modfile
                for modfile in modfiles
                if modfile.status != TranslationStatus.NoStrings
            ]
            for mod, modfiles in items_to_search.items()
            if any(modfile.status != TranslationStatus.NoStrings for modfile in modfiles)
        }

        self.log.info(f"Searching {len(relevant_items)} mod(s) for strings...")

        results: dict[Path, StringList] = {}
        for m, (mod, modfiles) in enumerate(relevant_items.items()):
            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=self.tr("Searching modlist for strings...")
                        + f" ({m}/{len(relevant_items.items())})",
                        value=m,
                        maximum=len(relevant_items.items()),
                    )
                )

            self.log.debug(f"Searching for strings in '{mod.name}'...")
            mod_result: dict[Path, StringList] = self.__search_mod(
                mod, modfiles, filter, pdisplay
            )
            if mod_result:
                results.update(mod_result)

        self.log.info(
            f"Search modlist for strings complete. Found results in {len(results)} mod "
            "file(s)."
        )

        return results

    def __search_mod(
        self,
        mod: Mod,
        modfiles: list[ModFile],
        filter: SearchFilter,
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> dict[Path, StringList]:
        result: dict[Path, StringList] = {}

        for m, modfile in enumerate(modfiles):
            if pdisplay is not None:
                pdisplay.updateProgress(
                    1,
                    ProgressUpdate(
                        status_text=f"{mod.name} > {modfile.name} ({m}/{len(modfiles)})",
                        value=m,
                        maximum=len(modfiles),
                    ),
                )

            self.log.debug(
                f"Searching for strings in '{mod.name}' > '{modfile.name}'..."
            )
            modfile_result: StringList = self.__search_modfile(modfile, filter)
            if modfile_result:
                result[Path(f"{mod.name} > {modfile.name}")] = modfile_result

        return result

    def __search_modfile(self, modfile: ModFile, filter: SearchFilter) -> StringList:
        result: StringList = []

        strings: StringList = modfile.get_strings()
        for string in strings:
            if matches_filter(filter, string):
                result.append(string)

        return result

    def import_installed_translations(
        self, mods: list[Mod], pdisplay: Optional[ProgressDisplay] = None
    ) -> None:
        """
        Scans for and imports installed translations. Creates database translations for
        mod files that are entirely covered by installed translations if enabled.

        Args:
            mods (list[Mod]): The mods to scan.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.
        """

        installed_translations: dict[Mod, Mod] = self.run_translation_scan(
            mods, pdisplay
        )

        self.log.info(
            f"Importing {len(installed_translations)} installed translation(s)..."
        )

        new_translations: list[Translation] = []
        for m, (installed_translation, original_mod) in enumerate(
            installed_translations.items()
        ):
            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=self.tr("Importing translations...")
                        + f" ({m}/{len(installed_translations)})",
                        value=m,
                        maximum=len(installed_translations),
                    ),
                )
                pdisplay.updateProgress(
                    1,
                    ProgressUpdate(
                        status_text=installed_translation.name, value=0, maximum=0
                    ),
                )

            self.log.debug(
                f"Importing translation '{installed_translation.name}' for original "
                f"mod '{original_mod.name}'..."
            )

            translation_strings: dict[Path, StringList] = (
                StringExtractor.map_strings_from_mods(
                    installed_translation, original_mod
                )
            )

            if not translation_strings:
                self.log.warning(
                    f"No additional strings from '{installed_translation.name}'."
                )
                continue

            new_translations.append(
                DatabaseService.create_translation_from_mod(
                    mod=installed_translation,
                    original_mod=original_mod,
                    strings=translation_strings,
                    database=self.database,
                    add_and_save=False,
                )
            )

        self.log.info(f"Imported {len(new_translations)} installed translation(s).")

        if self.app_config.auto_create_database_translations:
            self.log.info("Creating database translations...")
            items: dict[Mod, list[ModFile]] = {
                mod: [
                    modfile
                    for modfile in mod.modfiles
                    if modfile.status == TranslationStatus.TranslationAvailableInDatabase
                ]
                for mod in mods
                if any(
                    modfile.status == TranslationStatus.TranslationAvailableInDatabase
                    for modfile in mod.modfiles
                )
            }

            for m, mod in enumerate(items):
                if pdisplay is not None:
                    pdisplay.updateMainProgress(
                        ProgressUpdate(
                            status_text=self.tr("Creating database translations...")
                            + f" ({m}/{len(items)})",
                            value=m,
                            maximum=len(items),
                        )
                    )
                    pdisplay.updateProgress(
                        1, ProgressUpdate(status_text=mod.name, value=0, maximum=0)
                    )

                self.log.debug(f"Creating database translation for '{mod.name}'...")
                new_translations.append(
                    DatabaseService.create_translation_for_mod(
                        mod,
                        self.database,
                        only_complete_coverage=True,
                        add_and_save=False,
                    )
                )

            self.log.info(
                f"Created {len(new_translations)} new database translation(s)."
            )

        for new_translation in new_translations:
            # remove duplicate strings and save the translation
            new_translation.remove_duplicates()

        if new_translations:
            DatabaseService.add_translations(new_translations, self.database)

    def run_translation_scan(
        self, mods: list[Mod], pdisplay: Optional[ProgressDisplay] = None
    ) -> dict[Mod, Mod]:
        """
        Scans for installed translations.

        Args:
            mods (list[Mod]): The mods to scan.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            dict[Mod, Mod]: Map of translations to their (approximate) original mod.
        """

        result: dict[Mod, Mod] = {}

        self.log.info(f"Scanning {len(mods)} mod(s) for installed translations...")

        for m, mod in enumerate(mods):
            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=self.tr("Scanning for installed translations...")
                        + f" ({m}/{len(mods)})",
                        value=m,
                        maximum=len(mods),
                    ),
                )
                pdisplay.updateProgress(
                    1, ProgressUpdate(status_text=mod.name, value=0, maximum=0)
                )

            original_mod: Optional[Mod] = self.__translation_scan_mod(mod, pdisplay)

            if original_mod is not None:
                result[mod] = original_mod

        self.log.info(
            f"Found {len(result)} installed translation(s) that can be imported."
        )

        return result

    def __translation_scan_mod(
        self, mod: Mod, pdisplay: Optional[ProgressDisplay] = None
    ) -> Optional[Mod]:
        self.log.debug(f"Scanning for installed translations in '{mod.name}'...")

        original_mod: Optional[Mod] = None

        modfile_paths: list[Path] = list(
            filter(
                lambda m: self.database.get_translation_by_modfile_path(m) is None,
                unique(
                    [
                        modfile.path
                        for modfile in mod.modfiles
                        if modfile.status == TranslationStatus.IsTranslated
                    ]
                    + [Path(Path(dsd_file).parent.name) for dsd_file in mod.dsd_files],
                ),
            )
        )
        for m, modfile_path in enumerate(modfile_paths):
            if pdisplay is not None:
                pdisplay.updateProgress(
                    1,
                    ProgressUpdate(
                        status_text=f"{mod.name} > {modfile_path} ({m}/{len(modfile_paths)})",
                        value=m,
                        maximum=len(modfile_paths),
                    ),
                )

            original_mod = self.mod_instance.get_mod_with_modfile(
                modfile_path,
                ignore_mods=[mod],
                ignore_states=[
                    TranslationStatus.IsTranslated,
                    TranslationStatus.TranslationInstalled,
                ],
            )

            if original_mod is not None:
                break

        else:
            if modfile_paths:
                self.log.warning(
                    f"No original mod found for installed translation '{mod.name}'!"
                )

        return original_mod

    def __create_status_summary(
        self, scan_result: dict[Mod, dict[ModFile, TranslationStatus]]
    ) -> str:
        status_counts: dict[TranslationStatus, int] = {}
        for mod_results in scan_result.values():
            for status in mod_results.values():
                status_counts[status] = status_counts.get(status, 0) + 1

        status_summary: str = " | ".join(
            f"{status.name}: {count}"
            for status, count in sorted(
                status_counts.items(), key=lambda item: item[0].value
            )
        )

        return status_summary
