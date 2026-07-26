"""
Copyright (c) Cutleast
"""

import logging
from concurrent.futures import Future, as_completed
from copy import copy
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
    update,
)
from cutleast_core_lib.core.multithreading.progress_executor import ProgressExecutor
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
from core.string.types import String, StringList
from core.translation_provider.mod_id import ModId
from core.translation_provider.provider import Provider
from core.translation_provider.source import Source
from core.utilities.container_utils import unique

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
    provider: Provider
    masterlist: Masterlist
    detector: LangDetector

    def __init__(
        self,
        mod_instance: ModInstance,
        database: TranslationDatabase,
        app_config: AppConfig,
        user_config: UserConfig,
        provider: Provider,
        masterlist: Masterlist,
    ) -> None:
        """
        Args:
            mod_instance (ModInstance): The loaded mod instance.
            database (TranslationDatabase): The translation database.
            app_config (AppConfig): The application configuration.
            user_config (UserConfig): The user configuration.
            provider (Provider): The translation provider.
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

        thread_num: Optional[int] = (
            self.app_config.worker_thread_num
            if self.app_config.worker_thread_num > 0
            else None
        )

        self.log.info(f"Scanning {len(items)} mod(s)...")

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
        with ProgressExecutor(pdisplay, max_workers=thread_num) as executor:
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
                    self.log.error(
                        f"Failed to scan {mod.name!r} > {modfile.name!r}: {ex}",
                        exc_info=ex,
                    )

        self.log.info("Modlist scan complete.")

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
        self.log.info(f"Scanning {modfile_path_text}...")

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
            self.log.info("Mod file is already translated.")

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

        # 2 workers seems to be a good balance between speed and not overloading the
        # provider's API
        with ProgressExecutor(pdisplay, max_workers=2) as executor:
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

            self.log.info(f"Scanning for {mod.name!r} > {modfile.name!r}...")
            try:
                result[modfile] = self.__online_scan_modfile(mod.mod_id, modfile)
            except Exception as ex:
                self.log.error(
                    f"Failed to scan for {mod.name!r} > {modfile.name!r}: {ex}",
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
            self.log.info("Found route entry for mod file in masterlist.")
            return TranslationStatus.TranslationAvailableOnline

        if len(available_translations):
            return TranslationStatus.TranslationAvailableOnline
        else:
            return TranslationStatus.NoTranslationAvailable

    def run_deep_scan(
        self, pdisplay: Optional[ProgressDisplay] = None
    ) -> dict[ModFile, TranslationStatus]:
        """
        Scans each installed translation for missing or untranslated strings.

        Args:
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            dict[ModFile, TranslationStatus]:
                Mod files with installed translations and their status
        """

        translations: list[Translation] = self.database.user_translations

        self.log.info(f"Running deep scan for {len(translations)} translation(s)...")

        scan_result: dict[ModFile, TranslationStatus] = {}
        for t, translation in enumerate(translations):
            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=self.tr("Running deep scan...")
                        + f" ({t}/{len(translations)})",
                        value=t,
                        maximum=len(translations),
                    )
                )

            self.log.info(f"Scanning {translation.name!r}...")
            scan_result.update(self.__deep_scan_translation(translation, pdisplay))

        self.log.info("Deep scan complete.")

        return scan_result

    def __deep_scan_translation(
        self, translation: Translation, pdisplay: Optional[ProgressDisplay] = None
    ) -> dict[ModFile, TranslationStatus]:
        result: dict[ModFile, TranslationStatus] = {}
        for m, (modfile_path, strings) in enumerate(translation.strings.items()):
            if pdisplay is not None:
                pdisplay.updateProgress(
                    1,
                    ProgressUpdate(
                        status_text=f"{translation.name} > {modfile_path} ({m}/{len(translation.strings)})",
                        value=m,
                        maximum=len(translation.strings),
                    ),
                )

            modfile: Optional[ModFile] = self.mod_instance.get_modfile(
                modfile_path, ignore_states=[TranslationStatus.IsTranslated]
            )

            if modfile is None:
                self.log.warning(f"Mod file {modfile_path!r} not found in modlist.")
                continue

            self.log.info(f"Scanning {translation.name!r} > {modfile_path!r}...")
            result[modfile] = self.__deep_scan_modfile_translation(
                strings, modfile, pdisplay
            )
            translation.save()

        return result

    def __deep_scan_modfile_translation(
        self,
        translation_strings: StringList,
        modfile: ModFile,
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> TranslationStatus:
        modfile_strings: StringList = modfile.get_strings()
        translation_map: dict[str, String] = {
            string.id: string for string in translation_strings
        }

        translation_complete = True
        for s, modfile_string in enumerate(modfile_strings):
            if pdisplay is not None:
                pdisplay.updateProgress(
                    2,
                    ProgressUpdate(
                        status_text=self.tr("Scanning strings...")
                        + f" ({s}/{len(modfile_strings)})",
                        value=s,
                        maximum=len(modfile_strings),
                    ),
                )

            matching: Optional[String] = translation_map.get(modfile_string.id)

            if matching is None:
                new_string: String = copy(modfile_string)
                new_string.status = StringStatus.TranslationRequired
                new_string.string = new_string.original
                translation_map[new_string.id] = new_string
                translation_strings.append(new_string)
                translation_complete = False

            elif (
                matching.status == StringStatus.TranslationIncomplete
                or matching.status == StringStatus.TranslationRequired
            ):
                translation_complete = False

        if not translation_complete:
            self.log.info(f"Translation for {modfile.name!r} is incomplete.")
            return TranslationStatus.TranslationIncomplete
        else:
            self.log.info(f"Translation for {modfile.name!r} is complete.")
            return TranslationStatus.TranslationInstalled

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

            self.log.info(f"Searching for strings in {mod.name!r}...")
            mod_result: dict[Path, StringList] = self.__search_mod(
                mod, modfiles, filter, pdisplay
            )
            if mod_result:
                results.update(mod_result)

        self.log.info("Search modlist for strings complete.")

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

            self.log.info(f"Searching for strings in {mod.name!r} > {modfile.name!r}...")
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

            self.log.info(
                f"Importing translation {installed_translation.name!r} "
                f"for original mod {original_mod.name!r}..."
            )

            translation_strings: dict[Path, StringList] = (
                StringExtractor.map_strings_from_mods(
                    installed_translation, original_mod
                )
            )

            if not translation_strings:
                self.log.info(
                    f"No additional strings from {installed_translation.name!r}."
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

                self.log.info(f"Creating database translation for {mod.name!r}...")
                new_translations.append(
                    DatabaseService.create_translation_for_mod(
                        mod,
                        self.database,
                        only_complete_coverage=True,
                        add_and_save=False,
                    )
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

            self.log.info(f"Scanning for installed translations in {mod.name!r}...")

            original_mod: Optional[Mod] = self.__translation_scan_mod(mod, pdisplay)

            if original_mod is not None:
                result[mod] = original_mod

        self.log.info("Scanning for installed translations complete.")

        return result

    def __translation_scan_mod(
        self, mod: Mod, pdisplay: Optional[ProgressDisplay] = None
    ) -> Optional[Mod]:
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
                    f"No original mod found for installed translation {mod.name!r}!"
                )

        return original_mod
