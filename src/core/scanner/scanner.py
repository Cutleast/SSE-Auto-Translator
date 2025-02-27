"""
Copyright (c) Cutleast
"""

import logging
from copy import copy
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject

from app_context import AppContext
from core.cacher.cacher import Cacher
from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.search_filter import SearchFilter, matches_filter
from core.database.string import String
from core.database.translation import Translation
from core.masterlist.masterlist import Masterlist
from core.masterlist.masterlist_entry import MasterlistEntry
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.plugin import Plugin
from core.translation_provider.provider import Provider
from core.translation_provider.source import Source
from core.utilities.container_utils import unique
from core.utilities.detector import LangDetector, Language
from ui.widgets.loading_dialog import LoadingDialog


class Scanner(QObject):
    """
    Class for various scanning actions on the loaded modlist.
    """

    log: logging.Logger = logging.getLogger("Scanner")

    cacher: Cacher
    mod_instance: ModInstance
    database: TranslationDatabase
    app_config: AppConfig
    user_config: UserConfig
    provider: Provider
    masterlist: Masterlist
    detector: LangDetector

    def __init__(self) -> None:
        super().__init__()

        self.cacher = AppContext.get_app().cacher
        self.mod_instance = AppContext.get_app().mod_instance
        self.database = AppContext.get_app().database
        self.app_config = AppContext.get_app().app_config
        self.user_config = AppContext.get_app().user_config
        self.provider = AppContext.get_app().provider
        self.masterlist = AppContext.get_app().masterlist
        self.detector = LangDetector(
            self.app_config.detector_confidence,
            getattr(Language, self.user_config.language.upper()),
        )

    def run_basic_scan(
        self, items: dict[Mod, list[Plugin]], ldialog: Optional[LoadingDialog] = None
    ) -> dict[Mod, dict[Plugin, Plugin.Status]]:
        """
        Scans mods for required and installed translations.
        Automatically imports installed translations if enabled by the user.

        Args:
            items (dict[Mod, list[Plugin]]): The items to scan.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[Mod, dict[Plugin, Plugin.Status]]:
                A dictionary of mods, their plugins and their status.
        """

        self.log.info(f"Scanning {len(items)} mod(s)...")

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Loading database..."))

        database_strings: list[String] = String.unique(
            string
            for string in self.database.strings
            if string.status != String.Status.TranslationRequired
        )
        database_originals: list[str] = unique(
            string.original_string for string in database_strings
        )

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Scanning modlist..."))

        scan_result: dict[Mod, dict[Plugin, Plugin.Status]] = {}
        for m, (mod, plugins) in enumerate(items.items()):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Scanning modlist...") + f" ({m}/{len(items)})",
                    value1=m,
                    max1=len(items),
                )

            self.log.info(f"Scanning {mod.name!r}...")
            scan_result[mod] = self.__basic_scan_mod(
                mod, plugins, database_strings, database_originals, ldialog
            )

        self.log.info("Modlist scan complete.")

        return scan_result

    def __basic_scan_mod(
        self,
        mod: Mod,
        plugins: list[Plugin],
        database_strings: list[String],
        database_originals: list[str],
        ldialog: Optional[LoadingDialog] = None,
    ) -> dict[Plugin, Plugin.Status]:
        result: dict[Plugin, Plugin.Status] = {}

        for p, plugin in enumerate(plugins):
            if ldialog is not None:
                ldialog.updateProgress(
                    show2=True,
                    text2=f"{mod.name} > {plugin.name} ({p}/{len(plugins)})",
                    value2=p,
                    max2=len(plugins),
                )

            self.log.info(f"Scanning {mod.name!r} > {plugin.name!r}...")
            result[plugin] = self.__basic_scan_plugin(
                plugin, database_strings, database_originals, ldialog
            )

        return result

    def __basic_scan_plugin(
        self,
        plugin: Plugin,
        database_strings: list[String],
        database_originals: list[str],
        ldialog: Optional[LoadingDialog] = None,
    ) -> Plugin.Status:
        if ldialog is not None:
            ldialog.updateProgress(show3=True, text3=self.tr("Extracting strings..."))

        self.log.debug("Extracting strings...")
        plugin_strings: list[String] = self.cacher.get_plugin_strings(plugin.path)
        if not len(plugin_strings):
            return Plugin.Status.NoStrings

        if ldialog is not None:
            ldialog.updateProgress(text3=self.tr("Detecting language..."))

        self.log.debug("Detecting language...")

        status: Plugin.Status
        if self.detector.requires_translation(plugin_strings):
            if self.database.get_translation_by_plugin_name(plugin.name) is not None:
                status = Plugin.Status.TranslationInstalled

            elif any(
                string.original_string not in database_originals
                and string not in database_strings
                for string in plugin_strings
            ):
                status = Plugin.Status.RequiresTranslation
            else:
                status = Plugin.Status.TranslationAvailableInDatabase

        else:
            status = Plugin.Status.IsTranslated
            self.log.info("Plugin is already translated.")

        return status

    def run_online_scan(
        self, items: dict[Mod, list[Plugin]], ldialog: Optional[LoadingDialog] = None
    ) -> dict[Mod, dict[Plugin, Plugin.Status]]:
        """
        Scans online for available translations.

        Args:
            items (dict[Mod, list[Plugin]]): The items to scan.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[Mod, dict[Plugin, Plugin.Status]]:
                A dictionary of mods, their plugins and their status.
        """

        relevant_items: dict[Mod, list[Plugin]] = {
            mod: [
                plugin
                for plugin in plugins
                if plugin.status == Plugin.Status.RequiresTranslation
            ]
            for mod, plugins in items.items()
            if any(
                plugin.status == Plugin.Status.RequiresTranslation for plugin in plugins
            )
        }

        self.log.info(
            "Scanning online for available translations "
            f"for {len(relevant_items)} mod(s)..."
        )

        scan_result: dict[Mod, dict[Plugin, Plugin.Status]] = {}
        for m, (mod, plugins) in enumerate(relevant_items.items()):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Scanning online...")
                    + f" ({m}/{len(relevant_items.items())})",
                    value1=m,
                    max1=len(relevant_items.items()),
                )

            self.log.info(f"Scanning for {mod.name!r}...")
            scan_result[mod] = self.__online_scan_mod(mod, plugins, ldialog)

        self.log.info("Online scan complete.")

        return scan_result

    def __online_scan_mod(
        self, mod: Mod, plugins: list[Plugin], ldialog: Optional[LoadingDialog] = None
    ) -> dict[Plugin, Plugin.Status]:
        result: dict[Plugin, Plugin.Status] = {}
        for p, plugin in enumerate(plugins):
            if ldialog is not None:
                ldialog.updateProgress(
                    show2=True,
                    text2=f"{mod.name} > {plugin.name} ({p}/{len(plugins)})",
                    value2=p,
                    max2=len(plugins),
                )

            self.log.info(f"Scanning for {mod.name!r} > {plugin.name!r}...")
            result[plugin] = self.__online_scan_plugin(mod.mod_id, plugin, ldialog)

        return result

    def __online_scan_plugin(
        self, mod_id: int, plugin: Plugin, ldialog: Optional[LoadingDialog] = None
    ) -> Plugin.Status:
        available_translations: list[tuple[int, list[int], Source]] = (
            self.provider.get_translations(
                mod_id,
                plugin.name,
                self.user_config.language,
                self.user_config.author_blacklist,
            )
        )

        masterlist_entry: Optional[MasterlistEntry] = self.masterlist.entries.get(
            plugin.name.lower()
        )

        if (
            masterlist_entry is not None
            and masterlist_entry.type == MasterlistEntry.Type.Route
            and masterlist_entry.targets
        ):
            self.log.info("Found route entry for plugin in masterlist.")
            return Plugin.Status.TranslationAvailableOnline

        if len(available_translations):
            return Plugin.Status.TranslationAvailableOnline
        else:
            return Plugin.Status.NoTranslationAvailable

    def run_deep_scan(
        self, ldialog: Optional[LoadingDialog] = None
    ) -> dict[Plugin, Plugin.Status]:
        """
        Scans each installed translation for missing or untranslated strings.

        Args:
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[Plugin, Plugin.Status]:
                Plugins with installed translations and their status
        """

        translations: list[Translation] = self.database.user_translations

        self.log.info(f"Running deep scan for {len(translations)} translation(s)...")

        scan_result: dict[Plugin, Plugin.Status] = {}
        for t, translation in enumerate(translations):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Running deep scan...")
                    + f" ({t}/{len(translations)})",
                    value1=t,
                    max1=len(translations),
                )

            self.log.info(f"Scanning {translation.name!r}...")
            scan_result.update(self.__deep_scan_translation(translation, ldialog))

        self.log.info("Deep scan complete.")

        return scan_result

    def __deep_scan_translation(
        self, translation: Translation, ldialog: Optional[LoadingDialog] = None
    ) -> dict[Plugin, Plugin.Status]:
        result: dict[Plugin, Plugin.Status] = {}
        for p, (plugin_name, strings) in enumerate(translation.strings.items()):
            if ldialog is not None:
                ldialog.updateProgress(
                    show2=True,
                    text2=f"{translation.name} > {plugin_name} ({p}/{len(translation.strings)})",
                    value2=p,
                    max2=len(translation.strings),
                )

            plugin: Optional[Plugin] = self.mod_instance.get_plugin(
                plugin_name,
                ignore_states=[Plugin.Status.IsTranslated],
                ignore_case=True,
            )

            if plugin is None:
                self.log.warning(f"Plugin {plugin_name!r} not found in modlist.")
                continue

            self.log.info(f"Scanning {translation.name!r} > {plugin_name!r}...")
            result[plugin] = self.__deep_scan_plugin_translation(
                strings, plugin, ldialog
            )
            translation.save_translation()

        return result

    def __deep_scan_plugin_translation(
        self,
        translation_strings: list[String],
        plugin: Plugin,
        ldialog: Optional[LoadingDialog] = None,
    ) -> Plugin.Status:
        plugin_strings: list[String] = self.cacher.get_plugin_strings(plugin.path)
        translation_map: dict[str, String] = {
            string.id: string for string in translation_strings
        }

        translation_complete = True
        for s, plugin_string in enumerate(plugin_strings):
            if ldialog is not None:
                ldialog.updateProgress(
                    show3=True,
                    text3=self.tr("Scanning strings...")
                    + f" ({s}/{len(plugin_strings)})",
                    value3=s,
                    max3=len(plugin_strings),
                )

            matching: Optional[String] = translation_map.get(plugin_string.id)

            if matching is None:
                new_string: String = copy(plugin_string)
                new_string.status = String.Status.TranslationRequired
                new_string.translated_string = new_string.original_string
                translation_map[new_string.id] = new_string
                translation_strings.append(new_string)
                translation_complete = False

            elif (
                matching.status == String.Status.TranslationIncomplete
                or matching.status == String.Status.TranslationRequired
            ):
                translation_complete = False

        if not translation_complete:
            self.log.info(f"Translation for {plugin.name!r} is incomplete.")
            return Plugin.Status.TranslationIncomplete
        else:
            self.log.info(f"Translation for {plugin.name!r} is complete.")
            return Plugin.Status.TranslationInstalled

    def run_string_search(
        self,
        items_to_search: dict[Mod, list[Plugin]],
        filter: SearchFilter,
        ldialog: Optional[LoadingDialog] = None,
    ) -> dict[str, list[String]]:
        """
        Searches the modlist for strings.

        Args:
            items_to_search (dict[Mod, list[Plugin]]): The items to search.
            filter (SearchFilter): The search filter.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[str, list[String]]: A dictionary of plugins and their matching strings.
        """

        relevant_items: dict[Mod, list[Plugin]] = {
            mod: [
                plugin for plugin in plugins if plugin.status != Plugin.Status.NoStrings
            ]
            for mod, plugins in items_to_search.items()
            if any(plugin.status != Plugin.Status.NoStrings for plugin in plugins)
        }

        self.log.info(f"Searching {len(relevant_items)} mod(s) for strings...")

        results: dict[str, list[String]] = {}
        for m, (mod, plugins) in enumerate(relevant_items.items()):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Searching modlist for strings...")
                    + f" ({m}/{len(relevant_items.items())})",
                    value1=m,
                    max1=len(relevant_items.items()),
                )

            self.log.info(f"Searching for strings in {mod.name!r}...")
            mod_result: dict[str, list[String]] = self.__search_mod(
                mod, plugins, filter, ldialog
            )
            if mod_result:
                results.update(mod_result)

        self.log.info("Search modlist for strings complete.")

        return results

    def __search_mod(
        self,
        mod: Mod,
        plugins: list[Plugin],
        filter: SearchFilter,
        ldialog: Optional[LoadingDialog] = None,
    ) -> dict[str, list[String]]:
        result: dict[str, list[String]] = {}

        for p, plugin in enumerate(plugins):
            if ldialog is not None:
                ldialog.updateProgress(
                    show2=True,
                    text2=f"{mod.name} > {plugin.name} ({p}/{len(plugins)})",
                    value2=p,
                    max2=len(plugins),
                )

            self.log.info(f"Searching for strings in {mod.name!r} > {plugin.name!r}...")
            plugin_result: list[String] = self.__search_plugin(plugin, filter)
            if plugin_result:
                result[f"{mod.name} > {plugin.name}"] = plugin_result

        return result

    def __search_plugin(self, plugin: Plugin, filter: SearchFilter) -> list[String]:
        result: list[String] = []

        strings: list[String] = self.cacher.get_plugin_strings(plugin.path)
        for string in strings:
            if matches_filter(filter, string):
                result.append(string)

        return result

    def import_installed_translations(
        self, mods: list[Mod], ldialog: Optional[LoadingDialog] = None
    ) -> None:
        """
        Scans for and imports installed translations. Creates database translations for
        plugins that are entirely covered by installed translations if enabled.

        Args:
            mods (list[Mod]): The mods to scan.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        installed_translations: dict[Mod, Mod] = self.run_translation_scan(
            mods, ldialog
        )
        for m, (installed_translation, original_mod) in enumerate(
            installed_translations.items()
        ):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Importing translations...")
                    + f" ({m}/{len(installed_translations)})",
                    value1=m,
                    max1=len(installed_translations),
                    show2=True,
                    text2=installed_translation.name,
                    value2=0,
                    max2=0,
                )

            self.log.info(
                f"Importing translation {installed_translation.name!r} "
                f"for original mod {original_mod.name!r}..."
            )
            self.database.importer.import_mod_as_translation(
                installed_translation, original_mod
            )

        if self.app_config.auto_create_database_translations:
            self.log.info("Creating database translations...")
            items: dict[Mod, list[Plugin]] = {
                mod: [
                    plugin
                    for plugin in mod.plugins
                    if plugin.status == Plugin.Status.TranslationAvailableInDatabase
                ]
                for mod in mods
                if any(
                    plugin.status == Plugin.Status.TranslationAvailableInDatabase
                    for plugin in mod.plugins
                )
            }

            for m, (mod, plugins) in enumerate(items.items()):
                if ldialog is not None:
                    ldialog.updateProgress(
                        text1=self.tr("Creating database translations...")
                        + f" ({m}/{len(items)})",
                        value1=m,
                        max1=len(items),
                        show2=True,
                        text2=mod.name,
                        value2=0,
                        max2=0,
                    )

                self.log.info(f"Creating database translation for {mod.name!r}...")
                self.database.create_translation((mod, plugins))

    def run_translation_scan(
        self, mods: list[Mod], ldialog: Optional[LoadingDialog] = None
    ) -> dict[Mod, Mod]:
        """
        Scans for installed translations.

        Args:
            mods (list[Mod]): The mods to scan.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[Mod, Mod]: Map of translations to their (approximate) original mod.
        """

        result: dict[Mod, Mod] = {}

        self.log.info(f"Scanning {len(mods)} mod(s) for installed translations...")

        for m, mod in enumerate(mods):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Scanning for installed translations...")
                    + f" ({m}/{len(mods)})",
                    value1=m,
                    max1=len(mods),
                    show2=True,
                    text2=mod.name,
                    value2=0,
                    max2=0,
                )

            self.log.info(f"Scanning for installed translations in {mod.name!r}...")

            original_mod: Optional[Mod] = self.__translation_scan_mod(mod, ldialog)

            if original_mod is not None:
                result[mod] = original_mod

        self.log.info("Scanning for installed translations complete.")

        return result

    def __translation_scan_mod(
        self, mod: Mod, ldialog: Optional[LoadingDialog] = None
    ) -> Optional[Mod]:
        original_mod: Optional[Mod] = None

        plugin_names: list[str] = list(
            filter(
                lambda p: self.database.get_translation_by_plugin_name(p) is None,
                unique(
                    [
                        plugin.name
                        for plugin in mod.plugins
                        if plugin.status == Plugin.Status.IsTranslated
                    ]
                    + [Path(dsd_file).parent.name for dsd_file in mod.dsd_files],
                    key=lambda s: s.lower(),
                ),
            )
        )
        for p, plugin_name in enumerate(plugin_names):
            if ldialog is not None:
                ldialog.updateProgress(
                    show2=True,
                    text2=f"{mod.name} > {plugin_name} ({p}/{len(plugin_names)})",
                    value2=p,
                    max2=len(plugin_names),
                )

            original_mod = self.mod_instance.get_mod_with_plugin(
                plugin_name,
                ignore_mods=[mod],
                ignore_states=[
                    Plugin.Status.IsTranslated,
                    Plugin.Status.TranslationInstalled,
                ],
                ignore_case=True,
            )

            if original_mod is not None:
                break

        else:
            if plugin_names:
                self.log.warning(
                    f"No original mod found for installed translation {mod.name!r}!"
                )

        return original_mod

    def check_for_translation_updates(
        self, ldialog: Optional[LoadingDialog] = None
    ) -> dict[Translation, bool]:
        """
        Checks for available updates for the installed translations.

        Args:
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[Translation, bool]:
                Map of translations and whether an update is available
        """

        result: dict[Translation, bool] = {}

        relevant_translations = [
            translation
            for translation in self.database.user_translations
            if translation.mod_id
            and translation.status != Translation.Status.UpdateIgnored
            and translation.status != Translation.Status.UpdateAvailable
            and translation.source != Source.Local
        ]
        for t, translation in enumerate(relevant_translations):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Checking for translation updates...")
                    + f" ({t}/{len(relevant_translations)})",
                    value1=t,
                    max1=len(relevant_translations),
                    show2=True,
                    text2=translation.name,
                    value2=0,
                    max2=0,
                )

            # TODO: Improve this filter
            if (
                not translation.mod_id
                or not translation.file_id
                or not translation.timestamp
                or not translation.source
            ):
                continue

            result[translation] = self.provider.is_update_available(
                translation.mod_id,
                translation.file_id,
                translation.timestamp,
                translation.source,
            )

        return result
