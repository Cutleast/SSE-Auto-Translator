"""
Copyright (c) Cutleast
"""

import logging
import os
from copy import copy
from pathlib import Path
from shutil import rmtree
from typing import Any, Optional

import jstyleson as json
from PySide6.QtCore import QObject, Signal

from app_context import AppContext
from core.cacher.cacher import Cacher
from core.database.string import String
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.plugin import Plugin
from core.translation_provider.source import Source
from core.utilities.container_utils import unique

from .importer import Importer
from .search_filter import SearchFilter, matches_filter
from .translation import Translation


class TranslationDatabase(QObject):
    """
    Class for translation database manager.
    """

    highlight_signal = Signal(Translation)
    """
    This signal gets emitted when a translation is to be highlighted.
    """

    update_signal = Signal()
    """
    This signal gets emitted everytime, a translation is added, removed or renamed.
    """

    edit_signal = Signal(Translation)
    """
    This signal gets emitted when a translation is to be edited.
    """

    userdb_path: Path
    appdb_path: Path
    language: str

    importer: Importer

    __vanilla_translation: Translation
    __user_translations: list[Translation]

    log: logging.Logger = logging.getLogger("TranslationDatabase")

    def __init__(self, userdb_path: Path, appdb_path: Path, language: str) -> None:
        super().__init__()

        self.userdb_path = userdb_path
        self.appdb_path = appdb_path
        self.language = language

        self.importer = Importer(self)

        self.load_database()

    @property
    def vanilla_translation(self) -> Translation:
        """
        Translation for base game + AE CC Content.
        """

        return self.__vanilla_translation

    @property
    def user_translations(self) -> list[Translation]:
        """
        List of user installed translations.

        **Modifying this list won't affect the database.**
        """

        return copy(self.__user_translations)

    @property
    def strings(self) -> list[String]:
        """
        A list of all strings in the database.
        """

        result: list[String] = []

        if self.__vanilla_translation._strings is not None:
            result += [
                string
                for plugin_strings in self.__vanilla_translation._strings.values()
                for string in plugin_strings
            ]

        result += [
            string
            for translation in self.__user_translations
            for plugin_strings in (translation._strings or {}).values()
            for string in plugin_strings
            if string.status != String.Status.TranslationRequired
        ]

        return result

    def __load_vanilla_translation(self) -> None:
        """
        Loads vanilla translation.
        """

        self.log.info("Loading vanilla database...")

        translation_path: Path = self.appdb_path / self.language.lower()
        translation = Translation(name="", path=translation_path, source=Source.Local)
        translation.load_translation()
        self.__vanilla_translation = translation

        self.log.info(
            f"Loaded vanilla database for {len(translation._strings or {})} base game plugin(s)."
        )

    def __load_user_database(self) -> None:
        """
        Loads user installed translation database.
        """

        self.log.info("Loading user database...")

        index_path: Path = self.userdb_path / self.language / "index.json"

        if not index_path.is_file():
            with index_path.open("w", encoding="utf8") as index_file:
                json.dump([], index_file)

        with index_path.open(encoding="utf8") as index_file:
            translation_list: list[dict[str, Any]] = json.load(index_file)

        translations: list[Translation] = []

        for translation_data in translation_list:
            name: str = translation_data["name"]
            try:
                mod_id: int = int(translation_data["mod_id"])
                file_id: Optional[int] = translation_data.get("file_id", None)
                translation_path: Path = self.userdb_path / self.language / name
                source_name: str = translation_data.pop("source", "")
                source: Optional[Source] = Source.get(source_name)

                if source is None:
                    if mod_id and file_id:
                        source = Source.NexusMods
                    elif mod_id:
                        source = Source.Confrerie
                    else:
                        source = Source.Local

                translation = Translation(
                    path=translation_path,
                    **translation_data,
                    source=source,
                )
                translation.load_translation()
                translations.append(translation)
            except Exception as ex:
                self.log.error(
                    f"Failed to load translation {name!r}: {ex}", exc_info=ex
                )

        self.__user_translations = translations
        self.log.info(f"Loaded {len(self.__user_translations)} user translation(s).")

    def load_database(self) -> None:
        """
        Loads translation database.
        """

        self.__load_vanilla_translation()
        self.__load_user_database()

    def save_database(self) -> None:
        """
        Saves translation database.
        """

        self.log.info("Saving database...")

        index_path: Path = self.userdb_path / self.language / "index.json"
        index_data: list[dict[str, Any]] = [
            translation.to_index_data()
            for translation in unique(self.__user_translations, key=lambda t: t.id)
        ]

        with index_path.open("w", encoding="utf8") as index_file:
            json.dump(index_data, index_file, indent=4, ensure_ascii=False)

        self.log.info("Database saved.")

    def add_translation(self, translation: Translation, save: bool = True) -> None:
        """
        Adds a translation to the database.

        Args:
            translation (Translation): Translation to add to the database.
            save (bool, optional): Whether to save the database. Defaults to True.
        """

        if translation not in self.__user_translations:
            self.__user_translations.append(translation)
            self.log.info(f"Added translation {translation.name!r} to database.")

        mod_instance: ModInstance = AppContext.get_app().mod_instance

        # Merge new translation with existing one
        installed_translation = self.__user_translations[
            self.__user_translations.index(translation)
        ]

        plugin_states: dict[Plugin, Plugin.Status] = {}
        for plugin_name, plugin_strings in translation.strings.items():
            installed_translation.strings.setdefault(plugin_name, []).extend(
                plugin_strings
            )

            # Remove duplicates
            installed_translation.strings[plugin_name] = String.unique(
                installed_translation.strings[plugin_name]
            )

            # Set original plugin status to TranslationInstalled
            original_plugin: Optional[Plugin] = mod_instance.get_plugin(
                plugin_name,
                ignore_states=[
                    Plugin.Status.TranslationInstalled,
                    Plugin.Status.IsTranslated,
                ],
                ignore_case=True,
            )

            if original_plugin is not None:
                plugin_states[original_plugin] = Plugin.Status.TranslationInstalled

        # Merge metadata
        installed_translation.mod_id = translation.mod_id
        installed_translation.file_id = translation.file_id
        installed_translation.version = translation.version
        installed_translation.original_mod_id = translation.original_mod_id
        installed_translation.original_file_id = translation.original_file_id
        installed_translation.original_version = translation.original_version

        if save:
            self.save_database()

        mod_instance.set_plugin_states(plugin_states)
        self.update_signal.emit()

    def delete_translation(self, translation: Translation, save: bool = True) -> None:
        """
        Deletes a translation from the database.

        Args:
            translation (Translation): Translation to delete from the database.
            save (bool, optional): Whether to save the database. Defaults to True.
        """

        if translation.path is not None and translation.path.is_dir():
            rmtree(translation.path)
        if translation in self.__user_translations:
            self.__user_translations.remove(translation)

        self.log.info(f"Deleted translation {translation.name!r} from database.")

        mod_instance: ModInstance = AppContext.get_app().mod_instance
        plugin_states: dict[Plugin, Plugin.Status] = {}
        for plugin_name in translation.strings.keys():
            plugin: Optional[Plugin] = mod_instance.get_plugin(
                plugin_name,
                ignore_states=[Plugin.Status.IsTranslated],
                ignore_case=True,
            )
            if plugin is not None:
                plugin_states[plugin] = Plugin.Status.RequiresTranslation

        if save:
            self.save_database()

        mod_instance.set_plugin_states(plugin_states)
        self.update_signal.emit()

    def get_translation_by_plugin_name(self, plugin_name: str) -> Optional[Translation]:
        """
        Gets a translation that covers a specified plugin.
        This method is case-insensitive.

        Args:
            plugin_name (str): Name of the plugin.

        Returns:
            Optional[Translation]: Translation that covers the plugin or None.
        """

        translations = {
            _plugin_name.lower(): translation
            for translation in self.__user_translations
            for _plugin_name in translation.strings
        }

        return translations.get(plugin_name.lower())

    def get_translation_by_mod(self, mod: Mod) -> Optional[Translation]:
        """
        Gets a translation that covers a specified mod.

        Args:
            mod (Mod): Mod to get translation for.

        Returns:
            Optional[Translation]: Translation that covers the mod or None.
        """

        installed_translations = {
            translation.id: translation
            for translation in self.__user_translations
            if translation.mod_id and translation.file_id
        }

        translation: Optional[Translation] = None
        if f"{mod.mod_id}###{mod.file_id}" in installed_translations:
            translation = installed_translations[f"{mod.mod_id}###{mod.file_id}"]

        elif mod.plugins:
            translation = self.get_translation_by_plugin_name(mod.plugins[0].name)

        return translation

    def get_translation_by_id(
        self, mod_id: int, file_id: Optional[int] = None
    ) -> Optional[Translation]:
        """
        Gets a translation for a specified mod and file id if installed.

        Args:
            mod_id (int): Mod id.
            file_id (Optional[int], optional): File id. Defaults to None.

        Returns:
            Optional[Translation]: Translation or None.
        """

        translation: Optional[Translation] = None
        if mod_id and file_id:
            translation = {
                translation.id: translation for translation in self.__user_translations
            }.get(f"{mod_id}###{file_id}")

        elif mod_id:
            translation = {
                translation.mod_id: translation
                for translation in self.__user_translations
            }.get(mod_id)

        return translation

    def apply_db_to_translation(
        self, translation: Translation, plugin_name: Optional[str] = None
    ) -> None:
        """
        Applies database to untranslated strings in a translation.

        Args:
            translation (Translation): Translation to apply database to.
            plugin_name (Optional[str], optional):
                Name of the plugin to apply database to. Defaults to None.
        """

        if translation._strings is None:
            return

        installed_translations: list[Translation] = [
            self.__vanilla_translation
        ] + self.__user_translations

        database_originals: dict[str, String] = {
            string.original_string: string
            for _translation in installed_translations
            for _plugin_name, plugin_strings in (_translation._strings or {}).items()
            if _translation != translation or _plugin_name != plugin_name
            for string in plugin_strings
            if string.status != String.Status.TranslationRequired
        }
        database_strings: dict[str, String] = {
            string.id: string
            for translation in installed_translations
            for plugin_strings in (translation._strings or {}).values()
            for string in plugin_strings
            if string.status != String.Status.TranslationRequired
        }

        if plugin_name is not None:
            strings = [
                string
                for string in translation._strings[plugin_name]
                if string.status == string.Status.TranslationRequired
            ]
        else:
            strings = [
                string
                for plugin_strings in translation._strings.values()
                for string in plugin_strings
                if string.status == string.Status.TranslationRequired
            ]

        if not len(strings):
            return

        self.log.info(f"Translating {len(strings)} string(s) from database...")
        self.log.debug(
            f"Database size: {len(database_strings)} string(s) "
            f"({len(database_originals)} original(s))"
        )

        translated = 0
        for string in strings:
            matching = database_strings.get(string.id)

            if matching is None:
                matching = database_originals.get(string.original_string)

            if matching is None:
                continue

            full_matching = string == matching
            string.translated_string = matching.translated_string

            if full_matching or matching.status == String.Status.NoTranslationRequired:
                string.status = matching.status
            else:
                string.status = String.Status.TranslationIncomplete

            translated += 1

        self.log.info(f"Translated {translated} string(s) from database.")

    def create_translation(
        self, plugin_path: Path, apply_db: bool = True, add_and_save: bool = True
    ) -> Translation:
        """
        Creates translation for a plugin by extracting its strings
        and applying translations from database to them if enabled.

        Args:
            plugin_path (Path): Path to the plugin.
            apply_db (bool, optional): Whether to apply database. Defaults to True.
            add_and_save (bool, optional):
                Whether to save the translation and database. Defaults to True.

        Returns:
            Translation: Created translation.
        """

        translation: Optional[Translation] = self.get_translation_by_plugin_name(
            plugin_path.name
        )
        if translation:
            return translation

        cacher: Cacher = AppContext.get_app().cacher
        plugin_strings: list[String] = cacher.get_plugin_strings(plugin_path)

        for string in plugin_strings:
            string.translated_string = string.original_string
            string.status = string.Status.TranslationRequired

        translation_name: str = f"{plugin_path.name} - {self.language.capitalize()}"
        translation = Translation(
            name=translation_name,
            path=self.userdb_path / self.language / translation_name,
            _strings={plugin_path.name.lower(): plugin_strings},
        )

        if apply_db:
            self.apply_db_to_translation(translation, plugin_path.name.lower())

        if add_and_save:
            translation.save_translation()
            self.add_translation(translation)

        self.log.info(f"Created translation for plugin {plugin_path.name}.")

        return translation

    def search_database(self, filter: SearchFilter) -> dict[str, list[String]]:
        """
        Returns strings from database that match a specified filter.

        Args:
            filter (SearchFilter): Filter options.

        Returns:
            dict[str, list[String]]: Strings that match the filter.
        """

        self.log.info("Searching database...")
        self.log.debug(f"Filter: {filter}")

        result: dict[str, list[String]] = {}
        translations: list[Translation] = self.__user_translations + [
            self.__vanilla_translation
        ]

        for translation in translations:
            self.log.debug(f"Searching translation {translation.name!r}...")

            if translation._strings is None:
                continue

            for plugin, strings in translation._strings.items():
                self.log.debug(f"Searching plugin translation {plugin!r}...")

                for string in strings:
                    if matches_filter(filter, string):
                        if plugin in result:
                            result[plugin].append(string)
                        else:
                            result[plugin] = [string]

        self.log.info(
            f"Found {sum(len(strings) for strings in result.values())} "
            f"matching string(s) in {len(result)} plugin(s)."
        )

        return result

    def create_blank_translation(
        self, name: str, strings: dict[str, list[String]]
    ) -> Translation:
        """
        Creates a blank translation with the specified name and strings.

        Args:
            name (str): The name of the translation.
            strings (dict[str, list[String]]): Strings to add to the translation.

        Returns:
            Translation: The created translation.
        """

        return Translation(
            name=name, path=self.userdb_path / self.language / name, _strings=strings
        )

    def rename_translation(
        self, translation: Translation, new_name: str, save: bool = True
    ) -> None:
        """
        Renames a translation.

        Args:
            translation (Translation): The translation to rename.
            new_name (str): The new name of the translation.
            save (bool, optional):
                Whether to save the changes to the database. Defaults to True.
        """

        if translation.path is None or not translation.path.is_dir():
            raise FileNotFoundError(f"{translation.name!r} is not in database!")

        old_name: str = translation.name
        new_path = self.userdb_path / self.language / new_name
        os.rename(translation.path, new_path)
        translation.name = new_name
        translation.path = new_path

        if save:
            self.save_database()

        self.update_signal.emit()
        self.log.info(f"Renamed translation {old_name!r} to {new_name!r}.")