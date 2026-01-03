"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional

import jstyleson as json

from core.database.translation import Translation
from core.database.translation_service import TranslationService
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.string.string_status import StringStatus
from core.string.string_utils import StringUtils
from core.string.types import StringList
from core.translation_provider.source import Source
from core.utilities.container_utils import unique
from core.utilities.game_language import GameLanguage

from .database import TranslationDatabase


class DatabaseService:
    """
    Service class for managing the translation database.
    """

    log: logging.Logger = logging.getLogger("DatabaseService")

    @classmethod
    def load_database(
        cls, appdb_path: Path, userdb_path: Path, language: GameLanguage
    ) -> TranslationDatabase:
        """
        Loads the translation database for the specified language from the specified
        paths. Creates a new user database if there is none for the specified language.

        Args:
            appdb_path (Path): Path to the application database directory.
            userdb_path (Path): Path to the user database directory.
            language (GameLanguage): Language to load the database for.

        Returns:
            TranslationDatabase: The loaded translation database.
        """

        cls.log.info(f"Loading translation database for '{language}'...")
        cls.log.debug(f"App database path: {appdb_path}")
        cls.log.debug(f"User database path: {userdb_path}")

        if not (userdb_path / language.id).is_dir():
            (userdb_path / language.id).mkdir(parents=True, exist_ok=True)

            index_path = userdb_path / language.id / "index.json"
            with open(index_path, "w", encoding="utf8") as index_file:
                json.dump([], index_file, indent=4)

            cls.log.info(f"Created new database for '{language}'.")

        database = TranslationDatabase(
            userdb_path=userdb_path,
            appdb_path=appdb_path,
            language=language,
            vanilla_translation=cls.__load_vanilla_translation(appdb_path, language),
            user_translations=cls.__load_user_database(userdb_path, language),
        )

        cls.log.info(
            f"Loaded database with {len(database.strings)} strings(s) from "
            f"{len(database.user_translations) + 1} translation(s)."
        )

        return database

    @classmethod
    def __load_vanilla_translation(
        cls, appdb_path: Path, language: GameLanguage
    ) -> Translation:
        """
        Loads vanilla translation.

        Args:
            appdb_path (Path): Path to the application database directory.
            language (GameLanguage): Language to load the database for.
        """

        cls.log.info("Loading vanilla database...")

        translation = Translation(name="", path=appdb_path / language.id)
        translation.strings  # build cache of strings by "calling" the strings property

        cls.log.info(
            f"Loaded vanilla database for {len(translation.strings)} base game "
            "plugin(s)."
        )

        return translation

    @classmethod
    def __load_user_database(
        cls, userdb_path: Path, language: GameLanguage
    ) -> list[Translation]:
        """
        Loads user installed translation database.

        Args:
            userdb_path (Path): Path to the user database directory.
            language (GameLanguage): Language to load the database for.

        Returns:
            list[Translation]: List of loaded user translations.
        """

        cls.log.info("Loading user database...")

        db_path: Path = userdb_path / language.id
        index_path: Path = db_path / "index.json"

        if not index_path.is_file():
            with index_path.open("w", encoding="utf8") as index_file:
                json.dump([], index_file)

        with index_path.open(encoding="utf8") as index_file:
            translation_list: list[dict[str, Any]] = json.load(index_file)

        translations: list[Translation] = []
        for translation_data in translation_list:
            name: str = translation_data["name"]
            try:
                translation = Translation.from_index_data(translation_data, db_path)
                translation.strings  # build cache of strings by "calling" the strings property
                translations.append(translation)
            except Exception as ex:
                cls.log.error(f"Failed to load translation {name!r}: {ex}", exc_info=ex)

        cls.log.info(f"Loaded {len(translations)} user translation(s).")

        return translations

    @classmethod
    def save_database(cls, database: TranslationDatabase) -> None:
        """
        Saves the translation database index (not the translations themselves).

        Args:
            database (TranslationDatabase): The database to save.
        """

        cls.log.info(f"Saving database index for '{database.language}'...")

        index_path: Path = database.userdb_path / database.language.id / "index.json"
        index_data: list[dict[str, Any]] = [
            translation.to_index_data()
            for translation in unique(database.user_translations, key=lambda t: t.id)
        ]

        with index_path.open("w", encoding="utf8") as index_file:
            json.dump(index_data, index_file, indent=4, ensure_ascii=False)

        cls.log.info("Database index saved.")

    @classmethod
    def add_translation(
        cls, translation: Translation, database: TranslationDatabase, save: bool = True
    ) -> None:
        """
        Adds the specified translation to the specified translation database.
        Optionally saves the database.

        If a translation with the same ID (same name and path) is already in the database,
        the existing translation will be updated and their strings are merged.

        Args:
            translation (Translation): Translation to add.
            database (TranslationDatabase): Database to add the translation to.
            save (bool, optional): Whether to save the database. Defaults to True.

        ## Emitted Signals:
            `TranslationDatabase.add_signal([translation])`:
                If the translation wasn't in the database before.
            `TranslationDatabase.update_signal()`: Always.
        """

        cls.add_translations(translations=[translation], database=database, save=save)

    @classmethod
    def add_translations(
        cls,
        translations: list[Translation],
        database: TranslationDatabase,
        save: bool = True,
    ) -> None:
        """
        Adds the specified translations to the specified translation database.
        Optionally saves the database.

        If a translation with the same ID (same name and path) is already in the database,
        the existing translation will be updated and their strings are merged.

        Args:
            translations (list[Translation]): Translations to add.
            database (TranslationDatabase): Database to add the translations to.
            save (bool, optional): Whether to save the database. Defaults to True.

        ## Emitted Signals:
            `TranslationDatabase.add_signal(translations)`:
                With the translation that weren't in the database before.
            `TranslationDatabase.update_signal()`: Always.
        """

        added_translations: list[Translation] = []
        for translation in translations:
            if not database.is_translation_in_database(translation):
                database.user_translations.append(translation)
                cls.log.info(f"Added translation '{translation.name}' to database.")
                added_translations.append(translation)
            else:
                existing_translation: Translation = database.get_translation_for_id(
                    translation.id
                )
                cls.merge_translations(existing_translation, translation)
                cls.log.info(f"Updated translation '{translation.name}' in database.")

        if added_translations:
            database.add_signal.emit(added_translations)

        database.update_signal.emit()

        if save:
            cls.save_database(database)

    @classmethod
    def merge_translations(
        cls, existing_translation: Translation, new_translation: Translation
    ) -> Translation:
        """
        Merges the new translation into the existing translation by updating the metadata
        and merging the strings.

        Args:
            existing_translation (Translation):
                Translation that already exists in the database.
            new_translation (Translation):
                Translation to merge into the existing translation.

        Returns:
            Translation: The merged translation.
        """

        cls.merge_translation_strings(
            existing_translation.strings, new_translation.strings
        )

        # Merge metadata
        existing_translation.mod_id = new_translation.mod_id
        existing_translation.version = new_translation.version
        existing_translation.original_mod_id = new_translation.original_mod_id
        existing_translation.original_version = new_translation.original_version

        return existing_translation

    @classmethod
    def merge_translation_strings(
        cls,
        existing_strings: dict[Path, StringList],
        new_strings: dict[Path, StringList],
    ) -> dict[Path, StringList]:
        """
        Merges the strings of two translations and removes duplicate strings.

        Args:
            existing_strings (dict[Path, StringList]): Strings that are merged into.
            new_strings (dict[Path, StringList]): New strings to merge.

        Returns:
            dict[Path, StringList]: The merged strings.
        """

        for modfile_name, modfile_strings in new_strings.items():
            existing_strings.setdefault(modfile_name, []).extend(modfile_strings)

            # Remove duplicates
            existing_strings[modfile_name] = StringUtils.unique(
                existing_strings[modfile_name]
            )

        return existing_strings

    @classmethod
    def delete_translation(
        cls, translation: Translation, database: TranslationDatabase, save: bool = True
    ) -> None:
        """
        Deletes the specified translation from the translation database.

        Args:
            translation (Translation): Translation to delete.
            database (TranslationDatabase): Database to delete from.
            save (bool, optional): Whether to save the database. Defaults to True.

        ## Emitted Signals:
            `TranslationDatabase.remove_signal([translation])`:
                If the translation was in the database.
            `TranslationDatabase.update_signal()`: Always.
        """

        cls.delete_translations(
            translations=[translation], database=database, save=save
        )

    @classmethod
    def delete_translations(
        cls,
        translations: list[Translation],
        database: TranslationDatabase,
        save: bool = True,
    ) -> None:
        """
        Deletes the specified translations from the translation database.

        Args:
            translations (list[Translation]): Translations to delete.
            database (TranslationDatabase): Database to delete from.
            save (bool, optional): Whether to save the database. Defaults to True.

        ## Emitted Signals:
            `TranslationDatabase.remove_signal(translations)`:
                With every translation that was in the database.
            `TranslationDatabase.update_signal()`: Always.
        """

        deleted_translations: list[Translation] = []
        for translation in translations:
            shutil.rmtree(translation.path, ignore_errors=True)

            if database.is_translation_in_database(translation):
                database.user_translations.remove(translation)
                deleted_translations.append(translation)
                cls.log.info(f"Deleted translation '{translation.name}' from database.")

        if deleted_translations:
            database.remove_signal.emit(deleted_translations)

        database.update_signal.emit()

        if save:
            cls.save_database(database)

    @classmethod
    def rename_translation(
        cls,
        translation: Translation,
        new_name: str,
        database: TranslationDatabase,
        save: bool = True,
    ) -> None:
        """
        Renames a translation and its folder.

        Args:
            translation (Translation): Translation to rename.
            new_name (str): New name for the translation.
            database (TranslationDatabase): Database to rename in.
            save (bool, optional):
                Whether to save the database if the translation is in the database.
                Defaults to True.

        ## Emitted Signals:
            `TranslationDatabase.rename_signal(translation)`: If the translation is in the database.
            `TranslationDatabase.update_signal()`: If the translation is in the database.
        """

        old_name: str = translation.name
        new_path: Path = database.userdb_path / database.language.id / new_name
        os.rename(translation.path, new_path)
        translation.name = new_name
        translation.path = new_path

        cls.log.info(f"Renamed translation '{old_name}' to '{new_name}'.")

        if database.is_translation_in_database(translation):
            if save:
                cls.save_database(database)

            database.rename_signal.emit(translation)
            database.update_signal.emit()

    @classmethod
    def create_blank_translation(
        cls,
        name: str,
        strings: dict[Path, StringList],
        database: TranslationDatabase,
    ) -> Translation:
        """
        Creates a blank translation with the specified name and strings.

        Args:
            name (str): The name of the translation.
            strings (dict[Path, StringList]): Strings to add to the translation.
            database (TranslationDatabase):
                Database to determine the translation's path but the translation doesn't
                get added to it by this method.

        Returns:
            Translation: The created translation.
        """

        path: Path = database.userdb_path / database.language.id / name
        return Translation.create(name=name, path=path, strings=strings)

    @classmethod
    def create_translation_for_mod(
        cls,
        mod: Mod,
        database: TranslationDatabase,
        only_complete_coverage: bool = False,
        apply_db: bool = True,
        add_and_save: bool = True,
    ) -> Translation:
        """
        Creates a translation for the specified mod.

        Args:
            mod (Mod): Mod to create translation for.
            database (TranslationDatabase): Database to add the translation to.
            only_complete_coverage (bool, optional):
                Whether to only create translations for mod files that are completely
                covered by the database. Defaults to False.
            apply_db (bool, optional): Whether to apply database. Defaults to True.
            add_and_save (bool, optional):
                Whether to add the translation to the database and save them. Defaults to
                True.

        Returns:
            Translation: The created translation.
        """

        cls.log.info(f"Creating translation for mod '{mod.name}'...")

        translation: Optional[Translation] = database.get_translation_by_mod(mod)
        if translation is None:
            translation = cls.create_blank_translation(
                name=mod.name + " - " + database.language.name,
                strings={},
                database=database,
            )

        relevant_modfiles: list[ModFile] = list(
            filter(
                lambda modfile: (
                    modfile.status
                    not in [
                        TranslationStatus.NoStrings,
                        TranslationStatus.TranslationInstalled,
                        TranslationStatus.IsTranslated,
                    ]
                    and (modfile.path not in translation.strings)
                    and (
                        not only_complete_coverage
                        or modfile.status
                        == TranslationStatus.TranslationAvailableInDatabase
                    )
                ),
                mod.modfiles,
            )
        )

        if not relevant_modfiles:
            return translation

        translation_strings: dict[Path, StringList] = translation.strings
        for modfile in relevant_modfiles:
            modfile_strings: StringList = modfile.get_strings()

            for string in modfile_strings:
                string.string = string.original
                string.status = StringStatus.TranslationRequired

            if apply_db:
                TranslationService.update_strings(
                    strings_to_update=modfile_strings,
                    existing_strings=database.strings,
                )

            translation_strings.setdefault(modfile.path, []).extend(modfile_strings)

        translation.strings = translation_strings
        translation.remove_duplicates(save=False)

        if add_and_save:
            translation.save()
            cls.add_translation(translation, database)

        cls.log.info(
            f"Created translation with strings for {len(translation.strings)} "
            "modfile(s)."
        )

        return translation

    @classmethod
    def create_translation_for_modfile(
        cls,
        modfile: ModFile,
        database: TranslationDatabase,
        apply_db: bool = True,
        add_and_save: bool = True,
    ) -> Translation:
        """
        Creates a translation for the specified mod file.

        Args:
            modfile (ModFile): Mod file to create translation for.
            database (TranslationDatabase): Database to add the translation to.
            apply_db (bool, optional): Whether to apply database. Defaults to True.
            add_and_save (bool, optional):
                Whether to add the translation to the database and save them. Defaults to
                True.

        Returns:
            Translation: The created translation.
        """

        cls.log.info(f"Creating translation for mod file '{modfile.full_path}'...")

        translation: Optional[Translation] = database.get_translation_by_modfile_path(
            modfile.path
        )
        if translation is None:
            translation = cls.create_blank_translation(
                name=modfile.name + " - " + database.language.name,
                strings={},
                database=database,
            )

        modfile_strings: StringList = modfile.get_strings()
        for string in modfile_strings:
            string.string = string.original
            string.status = StringStatus.TranslationRequired

        if apply_db:
            TranslationService.update_strings(
                strings_to_update=modfile_strings,
                existing_strings=database.strings,
            )

        translation.strings.setdefault(modfile.path, []).extend(modfile_strings)
        translation.remove_duplicates(save=False)

        if add_and_save:
            translation.save()
            cls.add_translation(translation, database)

        cls.log.info(f"Created translation with {len(modfile_strings)} string(s).")

        return translation

    @classmethod
    def create_translation_from_mod(
        cls,
        mod: Mod,
        original_mod: Optional[Mod],
        strings: dict[Path, StringList],
        database: TranslationDatabase,
        add_and_save: bool = True,
    ) -> Translation:
        """
        Creates a translation from the metadata of the specified mod and the specified
        merged (!) strings.

        Args:
            mod (Mod): Mod to create translation from.
            original_mod (Optional[Mod]): Original mod that is translated.
            strings (dict[Path, StringList]): **Merged** strings to add to the translation.
            database (TranslationDatabase): Database to add the translation to.
            add_and_save (bool, optional):
                Whether to add the translation to the database and save them. Defaults
                to True.

        Returns:
            Translation: The created translation.
        """

        translation: Optional[Translation] = database.get_translation_by_mod(mod)
        if translation is None:
            translation = Translation(
                name=mod.name,
                path=database.userdb_path / database.language.id / mod.name,
                mod_id=mod.mod_id,
                version=mod.version,
                original_mod_id=original_mod.mod_id if original_mod else None,
                original_version=original_mod.version if original_mod else None,
                _strings={},
                source=(
                    mod.mod_id.estimate_source(
                        is_french=database.language == GameLanguage.French
                    )
                    if mod.mod_id is not None
                    else Source.Local
                ),
            )

        translation.strings = cls.merge_translation_strings(
            translation.strings, strings
        )

        if add_and_save:
            translation.save()
            cls.add_translation(translation, database)

        return translation
