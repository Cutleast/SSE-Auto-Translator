"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional

import jstyleson as json
from cutleast_core_lib.core.alerts.alert import Alert
from cutleast_core_lib.core.alerts.manager import AlertManager
from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.exceptions import format_exception
from cutleast_core_lib.core.utilities.unique import unique
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from pydantic import ValidationError
from PySide6.QtWidgets import QApplication

from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.string.string_utils import StringUtils
from core.string.types import StringList
from core.translation_provider.source import Source
from core.utilities.game_language import GameLanguage

from .database import TranslationDatabase
from .database_reload_result import DatabaseReloadResult


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

        translation = Translation(name="Base Game", path=appdb_path / language.id)
        translation.strings  # build cache of strings by "calling" the strings property  # noqa: B018

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
        translations: list[Translation] = []
        for translation_data in cls.__load_index_data(db_path):
            name: str = translation_data["name"]
            try:
                translation = Translation.from_index_data(translation_data, db_path)
                translation.strings  # build cache of strings by "calling" the strings property  # noqa: B018
                translations.append(translation)
            except Exception as ex:
                cls.log.error(f"Failed to load translation '{name}': {ex}", exc_info=ex)

        cls.log.info(f"Loaded {len(translations)} user translation(s).")

        return translations

    @classmethod
    def __load_index_data(cls, db_path: Path) -> list[dict[str, Any]]:
        """
        Loads the raw index data of the user database at the specified path. Creates an
        empty index file if there is none.

        Args:
            db_path (Path): Path to the user database directory of a language.

        Returns:
            list[dict[str, Any]]: List of raw translation entries from the index file.
        """

        index_path: Path = db_path / "index.json"

        if not index_path.is_file():
            with index_path.open("w", encoding="utf8") as index_file:
                json.dump([], index_file)

        with index_path.open(encoding="utf8") as index_file:
            translation_list: list[dict[str, Any]] = json.load(index_file)

        return translation_list

    @classmethod
    def reload_database(
        cls, database: TranslationDatabase, pdisplay: Optional[ProgressDisplay] = None
    ) -> DatabaseReloadResult:
        """
        Reloads the user translations of the specified database from disk to apply
        changes that were made outside of the application. Existing translation objects
        are updated in-place, translations that were added to the index file are added
        and translations that were removed from the index file are removed from the
        database (without deleting their files). Translations that fail to load are
        left unchanged and reported as alerts to the `AlertManager`.

        Args:
            database (TranslationDatabase): The database to reload.
            pdisplay (Optional[ProgressDisplay], optional):
                Progress display to report the progress to. Defaults to None.

        Returns:
            DatabaseReloadResult: Summary of the reload.

        ## Emitted Signals:
            `TranslationDatabase.add_signal(translations)`:
                With the translations that were added to the index file.
            `TranslationDatabase.remove_signal(translations)`:
                With the translations that were removed from the index file.
            `TranslationDatabase.changed_signal(translation)`:
                For every successfully reloaded translation that was already in the
                database.
            `TranslationDatabase.reload_signal(translations, removed_modfiles)`:
                With the successfully reloaded translations that were already in the
                database.
            `TranslationDatabase.update_signal()`: Always.
        """

        cls.log.info(f"Reloading translation database for '{database.language}'...")

        db_path: Path = database.userdb_path / database.language.id
        index_data: list[dict[str, Any]] = cls.__load_index_data(db_path)
        existing_translations: dict[str, Translation] = {
            translation.id: translation for translation in database.user_translations
        }

        # The path of a user translation is derived from its name, so the name is
        # sufficient to identify it. This also keeps translations whose index entry
        # is present but fails to load.
        indexed_names: set[str] = {
            str(entry["name"]).lower() for entry in index_data if "name" in entry
        }

        added_translations: list[Translation] = []
        reloaded_translations: list[Translation] = []
        removed_modfiles: list[Path] = []
        failed_count: int = 0
        for i, translation_data in enumerate(index_data):
            name: str = str(translation_data.get("name", ""))

            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=f"{name} ({i + 1}/{len(index_data)})",
                        value=i,
                        maximum=len(index_data),
                    )
                )

            try:
                loaded_translation = Translation.from_index_data(
                    translation_data, db_path
                )
                existing_translation: Optional[Translation] = existing_translations.get(
                    loaded_translation.id
                )
                if existing_translation is None:
                    loaded_translation.reload_strings()
                    added_translations.append(loaded_translation)
                else:
                    removed_modfiles.extend(
                        cls.__reload_translation(
                            existing_translation, loaded_translation
                        )
                    )
                    reloaded_translations.append(existing_translation)
            except (KeyError, OSError, ValidationError) as ex:
                failed_count += 1
                cls.__report_reload_failure(name, db_path / name, ex)

        removed_translations: list[Translation] = [
            translation
            for translation in existing_translations.values()
            if translation.name.lower() not in indexed_names
        ]

        cls.__apply_reload(
            database,
            added_translations,
            reloaded_translations,
            removed_translations,
            removed_modfiles,
        )

        result = DatabaseReloadResult(
            reloaded=len(reloaded_translations),
            added=len(added_translations),
            removed=len(removed_translations),
            failed=failed_count,
        )
        cls.log.info(f"Reloaded database: {result}")

        return result

    @classmethod
    def __reload_translation(
        cls, existing_translation: Translation, loaded_translation: Translation
    ) -> list[Path]:
        """
        Reloads the strings of an existing translation from disk and updates it
        in-place with the metadata of a freshly loaded translation. The translation is
        left unchanged if its strings fail to load.

        Args:
            existing_translation (Translation): Translation that is in the database.
            loaded_translation (Translation):
                Translation with the same ID that was freshly loaded from the index file.

        Raises:
            OSError: If a file of the translation could not be read.
            ValidationError: If a file of the translation contains invalid data.

        Returns:
            list[Path]: Paths of mod files that are no longer covered by the translation.
        """

        old_modfiles: set[Path] = set(existing_translation.strings)
        existing_translation.reload_strings()

        existing_translation.mod_id = loaded_translation.mod_id
        existing_translation.version = loaded_translation.version
        existing_translation.source = loaded_translation.source
        existing_translation.timestamp = loaded_translation.timestamp

        return list(old_modfiles - set(existing_translation.strings))

    @classmethod
    def __report_reload_failure(
        cls, name: str, path: Path, ex: KeyError | OSError | ValidationError
    ) -> None:
        """
        Logs a translation that failed to reload and reports it as an alert.

        Args:
            name (str): The name of the translation.
            path (Path): The path to the translation's folder.
            ex (KeyError | OSError | ValidationError):
                The exception that caused the failure.
        """

        cls.log.error(f"Failed to reload translation '{name}': {ex}", exc_info=ex)

        AlertManager.get().add_alert(
            Alert(
                severity=Alert.Severity.Error,
                title=QApplication.translate(
                    "DatabaseService", "Failed to reload translation '{name}'"
                ).format(name=name),
                summary=QApplication.translate(
                    "DatabaseService",
                    "The translation '{name}' could not be reloaded from disk and was "
                    "left unchanged.",
                ).format(name=name),
                details=format_exception(ex),
                context={
                    QApplication.translate("DatabaseService", "Translation"): name,
                    QApplication.translate("DatabaseService", "Path"): str(path),
                },
            )
        )

    @classmethod
    def __apply_reload(
        cls,
        database: TranslationDatabase,
        added_translations: list[Translation],
        reloaded_translations: list[Translation],
        removed_translations: list[Translation],
        removed_modfiles: list[Path],
    ) -> None:
        """
        Applies the result of a database reload to the specified database and emits the
        respective signals.

        Args:
            database (TranslationDatabase): The reloaded database.
            added_translations (list[Translation]): Translations to add.
            reloaded_translations (list[Translation]):
                Translations that were already in the database and got reloaded.
            removed_translations (list[Translation]): Translations to remove.
            removed_modfiles (list[Path]):
                Paths of mod files that are no longer covered by the reloaded
                translations.
        """

        for translation in removed_translations:
            database.user_translations.remove(translation)
            cls.log.info(f"Removed translation '{translation.name}' from database.")

        for translation in added_translations:
            database.user_translations.append(translation)
            cls.log.info(f"Added translation '{translation.name}' to database.")

        if removed_translations:
            database.remove_signal.emit(removed_translations)

        if added_translations:
            database.add_signal.emit(added_translations)

        for translation in reloaded_translations:
            database.changed_signal.emit(translation)

        if reloaded_translations:
            database.reload_signal.emit(reloaded_translations, removed_modfiles)

        database.update_signal.emit()

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

        cls.delete_translations(translations=[translation], database=database, save=save)

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

            if apply_db:
                StringUtils.match_strings(
                    strings_to_update=modfile_strings, database_strings=database.strings
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

        if apply_db:
            StringUtils.match_strings(
                strings_to_update=modfile_strings, database_strings=database.strings
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
                strings_={},
                source=mod.mod_id.source if mod.mod_id is not None else Source.Local,
            )

        translation.strings = cls.merge_translation_strings(translation.strings, strings)

        if add_and_save:
            translation.save()
            cls.add_translation(translation, database)

        return translation
