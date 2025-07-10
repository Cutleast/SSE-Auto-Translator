"""
Copyright (c) Cutleast
"""

import logging
import os
from copy import copy
from pathlib import Path
from shutil import rmtree
from typing import Any, Optional, overload

import jstyleson as json
from PySide6.QtCore import QObject, Signal

from core.cache.cache import Cache
from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.exporter import Exporter
from core.database.string import String
from core.database.utilities import Utilities
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.translation_provider.mod_id import ModId
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

    TODO: Remove this signal from this class
    """

    update_signal = Signal()
    """
    This signal gets emitted everytime, a translation is added, removed or renamed.
    """

    add_signal = Signal(Translation)
    """
    This signal gets emitted for every translation that is added.

    Args:
        Translation: The added translation.
    """

    edit_signal = Signal(Translation)
    """
    This signal gets emitted when a translation is to be edited.

    TODO: Remove this signal from this class
    """

    remove_signal = Signal(Translation)
    """
    This signal gets emitted for every translation that is removed.

    Args:
        Translation: The removed translation.
    """

    userdb_path: Path
    appdb_path: Path
    language: str

    cache: Cache
    importer: Importer
    exporter: Exporter
    utils: Utilities

    __vanilla_translation: Translation
    __user_translations: list[Translation]

    log: logging.Logger = logging.getLogger("TranslationDatabase")

    def __init__(
        self,
        userdb_path: Path,
        appdb_path: Path,
        language: str,
        cache: Cache,
        app_config: AppConfig,
        user_config: UserConfig,
    ) -> None:
        super().__init__()

        self.userdb_path = userdb_path
        self.appdb_path = appdb_path
        self.language = language
        self.cache = cache

        self.importer = Importer(cache, self, app_config, user_config)
        self.exporter = Exporter(self, user_config)
        self.utils = Utilities(user_config)

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

        result += [
            string
            for modfile_strings in self.__vanilla_translation.strings.values()
            for string in modfile_strings
        ]

        result += [
            string
            for translation in self.__user_translations
            for modfile_strings in (translation.strings or {}).values()
            for string in modfile_strings
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
        translation.load_strings()
        self.__vanilla_translation = translation

        self.log.info(
            f"Loaded vanilla database for {len(translation.strings)} base game plugin(s)."
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
                mod_id: int = int(translation_data.pop("mod_id"))
                file_id: Optional[int] = translation_data.pop("file_id", None)
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
                    mod_id=ModId(mod_id=mod_id, file_id=file_id),
                    original_mod_id=ModId(
                        mod_id=translation_data.pop("original_mod_id", 0),
                        file_id=translation_data.pop("original_file_id", None),
                    ),
                    **translation_data,
                    source=source,
                )
                translation.load_strings()
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

        # Add new translation
        if translation.id not in [t.id for t in self.__user_translations]:
            self.__user_translations.append(translation)
            self.log.info(f"Added translation {translation.name!r} to database.")

        # Merge with existing translation
        else:
            # Merge new translation with existing one
            translations: dict[str, Translation] = {
                t.id: t for t in self.user_translations
            }
            installed_translation = translations[translation.id]

            for modfile_name, modfile_strings in translation.strings.items():
                installed_translation.strings.setdefault(modfile_name, []).extend(
                    modfile_strings
                )

                # Remove duplicates
                installed_translation.strings[modfile_name] = String.unique(
                    installed_translation.strings[modfile_name]
                )

            # Merge metadata
            installed_translation.mod_id = translation.mod_id
            installed_translation.version = translation.version
            installed_translation.original_mod_id = translation.original_mod_id
            installed_translation.original_version = translation.original_version
            translation = installed_translation

        if save:
            self.save_database()

        self.add_signal.emit(translation)
        self.update_signal.emit()

    def delete_translation(self, translation: Translation, save: bool = True) -> None:
        """
        Deletes a translation from the database.

        Args:
            translation (Translation): Translation to delete from the database.
            save (bool, optional): Whether to save the database. Defaults to True.
        """

        if translation.path.is_dir():
            rmtree(translation.path)
        if translation in self.__user_translations:
            self.__user_translations.remove(translation)

        self.log.info(f"Deleted translation {translation.name!r} from database.")

        if save:
            self.save_database()

        self.remove_signal.emit(translation)
        self.update_signal.emit()

    def get_translation_by_modfile_name(
        self, modfile_name: str
    ) -> Optional[Translation]:
        """
        Gets a translation that covers a specified mod file.
        This method is case-insensitive.

        Args:
            modfile_name (str): Name of the mod file.

        Returns:
            Optional[Translation]: Translation that covers the mod file or None.
        """

        translations = {
            _modfile_name.lower(): translation
            for translation in self.__user_translations
            for _modfile_name in translation.strings
        }

        return translations.get(modfile_name.lower())

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
            if translation.mod_id
        }

        translation: Optional[Translation] = None
        if f"{mod.mod_id.mod_id}###{mod.mod_id.file_id}" in installed_translations:
            translation = installed_translations[
                f"{mod.mod_id.mod_id}###{mod.mod_id.file_id}"
            ]

        elif mod.modfiles:
            translation = self.get_translation_by_modfile_name(mod.modfiles[0].name)

        return translation

    def get_translation_by_id(self, mod_id: ModId) -> Optional[Translation]:
        """
        Gets a translation for a specified mod and file id if installed.

        Args:
            mod_id (int): Mod id.
            file_id (Optional[int], optional): File id. Defaults to None.

        Returns:
            Optional[Translation]: Translation or None.
        """

        translation: Optional[Translation] = {
            translation.mod_id: translation for translation in self.__user_translations
        }.get(mod_id)

        return translation

    def apply_db_to_translation(
        self, translation: Translation, modfile_name: Optional[str] = None
    ) -> None:
        """
        Applies database to untranslated strings in a translation.

        Args:
            translation (Translation): Translation to apply database to.
            modfile_name (Optional[str], optional):
                Name of the mod file to apply database to. Defaults to None.
        """

        translation_strings: Optional[dict[str, list[String]]] = translation.strings

        self.log.debug("Indexing database strings...")
        installed_translations: list[Translation] = [
            self.__vanilla_translation
        ] + self.__user_translations

        database_originals: dict[str, String] = {
            string.original_string: string
            for t in installed_translations
            for _modfile_name, modfile_strings in t.strings.items()
            if t != translation or _modfile_name != modfile_name
            for string in modfile_strings
            if string.status != String.Status.TranslationRequired
        }
        database_strings: dict[str, String] = {
            string.id: string
            for t in installed_translations
            for modfile_strings in t.strings.values()
            for string in modfile_strings
            if string.status != String.Status.TranslationRequired
        }

        strings: list[String]
        if modfile_name is not None:
            strings = [
                string
                for string in translation_strings[modfile_name]
                if string.status == String.Status.TranslationRequired
            ]
        else:
            strings = [
                string
                for modfile_strings in translation_strings.values()
                for string in modfile_strings
                if string.status == String.Status.TranslationRequired
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

            full_matching = string.id == matching.id
            string.translated_string = matching.translated_string

            if full_matching or matching.status == String.Status.NoTranslationRequired:
                string.status = matching.status
            else:
                string.status = String.Status.TranslationIncomplete

            translated += 1

        self.log.info(f"Translated {translated} string(s) from database.")

    @overload
    def create_translation(
        self,
        item: tuple[Mod, list[ModFile]],
        apply_db: bool = True,
        add_and_save: bool = True,
    ) -> Translation:
        """
        Creates translation for a mod by extracting the strings from the specified
        mod files and applying translations from database to them if enabled.

        Args:
            item (tuple[Mod, list[ModFile]]):
                Mod and mod files to create translation for.
            apply_db (bool, optional): Whether to apply database. Defaults to True.
            add_and_save (bool, optional):
                Whether to save the translation. Defaults to True.

        Returns:
            Translation: Created translation.
        """

    @overload
    def create_translation(
        self, item: ModFile, apply_db: bool = True, add_and_save: bool = True
    ) -> Translation:
        """
        Creates translation for a mod file by extracting its strings
        and applying translations from database to them if enabled.

        Args:
            item (ModFile): Mod file to create translation for.
            apply_db (bool, optional): Whether to apply database. Defaults to True.
            add_and_save (bool, optional):
                Whether to save the translation and database. Defaults to True.

        Returns:
            Translation: Created translation.
        """

    def create_translation(
        self,
        item: ModFile | tuple[Mod, list[ModFile]],
        apply_db: bool = True,
        add_and_save: bool = True,
    ) -> Optional[Translation]:
        mod: Optional[Mod] = None
        modfiles: list[ModFile] = []
        translation: Optional[Translation] = None
        translation_name: str

        if isinstance(item, ModFile):
            modfiles = [item]
            translation = self.get_translation_by_modfile_name(item.path.name)

            if translation is not None:
                return translation

            translation_name = f"{item.name} - {self.language.capitalize()}"

        else:
            mod, modfiles = item
            translation = self.get_translation_by_mod(mod)
            translation_name = f"{mod.name} - {self.language.capitalize()}"

        modfiles = list(
            filter(
                lambda p: p.status
                in [
                    TranslationStatus.RequiresTranslation,
                    TranslationStatus.TranslationAvailableInDatabase,
                ],
                modfiles,
            )
        )

        if not len(modfiles):
            return translation

        self.log.info(f"Creating translation for {len(modfiles)} mod file(s)...")

        if translation is None:
            translation_path: Path = self.userdb_path / self.language / translation_name
            translation = Translation(name=translation_name, path=translation_path)

        translation_strings: dict[str, list[String]] = translation.strings or {}
        for modfile in modfiles:
            modfile_strings: list[String] = modfile.get_strings(self.cache)

            for string in modfile_strings:
                string.translated_string = string.original_string
                string.status = String.Status.TranslationRequired

            translation_strings.setdefault(modfile.name.lower(), []).extend(
                modfile_strings
            )

        translation.strings = translation_strings
        translation.remove_duplicates(save=False)

        if apply_db:
            self.apply_db_to_translation(translation)

        if add_and_save:
            translation.save_strings()
            self.add_translation(translation)

        self.log.info(f"Created translation {translation.name!r}.")

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

            for modfile, strings in translation.strings.items():
                self.log.debug(f"Searching mod file translation {modfile!r}...")

                for string in strings:
                    if matches_filter(filter, string):
                        if modfile in result:
                            result[modfile].append(string)
                        else:
                            result[modfile] = [string]

        self.log.info(
            f"Found {sum(len(strings) for strings in result.values())} "
            f"matching string(s) in {len(result)} mod file(s)."
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

        if not translation.path.is_dir():
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
