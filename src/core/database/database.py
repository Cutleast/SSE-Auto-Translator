"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import time
from pathlib import Path
from shutil import rmtree

import jstyleson as json

from core.cacher.cacher import Cacher
from core.utilities.mod import Mod
from core.utilities.source import Source
from core.utilities.string import String

from .translation import Translation


class TranslationDatabase:
    """
    Class for translation database manager.
    """

    userdb_path: Path = None
    appdb_path: Path = None

    language: str = None

    vanilla_translation: Translation = None
    user_translations: list[Translation] = None

    log = logging.getLogger("TranslationDatabase")

    def __init__(
        self,
        userdb_path: Path,
        appdb_path: Path,
        language: str,
    ):
        self.userdb_path = userdb_path
        self.appdb_path = appdb_path
        self.language = language

        self.load_database()

    def load_vanilla_translation(self):
        """
        Loads vanilla translation.
        """

        self.log.info("Loading vanilla database...")

        translation_path = self.appdb_path / self.language.lower()

        translation = Translation(
            name="",
            mod_id=0,
            file_id=0,
            version="",
            original_mod_id=0,
            original_file_id=0,
            original_version="",
            path=translation_path,
            source=Source.Local,
        )
        translation.load_translation()
        self.vanilla_translation = translation

        self.log.info(
            f"Loaded vanilla database for {len(translation.strings)} base game plugin(s)."
        )

    def load_user_database(self):
        """
        Loads user installed translation database.
        """

        self.log.info("Loading user database...")

        index_path = self.userdb_path / self.language / "index.json"

        if not index_path.is_file():
            with index_path.open("w", encoding="utf8") as index_file:
                json.dump([], index_file)

        with index_path.open(encoding="utf8") as index_file:
            translation_list: list[dict] = json.load(index_file)

        translations: list[Translation] = []

        for translation_data in translation_list:
            name: str = translation_data["name"]
            mod_id: int = int(translation_data["mod_id"])
            file_id: int | None = translation_data["file_id"]
            version: str = translation_data["version"]
            original_mod_id: int = int(translation_data["original_mod_id"])
            original_file_id: int = int(translation_data["original_file_id"])
            original_version: str = translation_data["original_version"]
            translation_path: Path = self.userdb_path / self.language / name
            source = translation_data.get("source")
            source = Source.get(source)

            if source is None:
                if mod_id and file_id:
                    source = Source.NexusMods
                elif mod_id:
                    source = Source.Confrerie
                else:
                    source = Source.Local

            timestamp: int | None = translation_data.get("timestamp")

            translation = Translation(
                name=name,
                mod_id=mod_id,
                file_id=file_id,
                version=version,
                original_mod_id=original_mod_id,
                original_file_id=original_file_id,
                original_version=original_version,
                path=translation_path,
                source=source,
                timestamp=timestamp,
            )
            translation.load_translation()
            translations.append(translation)

        self.user_translations = translations

        self.log.info(f"Loaded {len(self.user_translations)} user translation(s).")

    def load_database(self):
        """
        Loads translation database.
        """

        self.load_vanilla_translation()
        self.load_user_database()

    def save_database(self):
        """
        Saves translation database.
        """

        self.log.info("Saving database...")

        index_path = self.userdb_path / self.language / "index.json"
        index_data = [
            {
                "name": translation.name,
                "mod_id": translation.mod_id,
                "file_id": translation.file_id,
                "version": translation.version,
                "original_mod_id": translation.original_mod_id,
                "original_file_id": translation.original_file_id,
                "original_version": translation.original_version,
                "source": translation.source.name,
                "timestamp": translation.timestamp,
            }
            for translation in self.user_translations
        ]

        with index_path.open("w", encoding="utf8") as index_file:
            json.dump(index_data, index_file, indent=4, ensure_ascii=False)

        self.log.info("Database saved.")

    def add_translation(self, translation: Translation):
        """
        Adds `translation` to database.
        """

        if translation not in self.user_translations:
            self.user_translations.append(translation)

        # Merge new translation with existing one
        else:
            installed_translation = self.user_translations[
                self.user_translations.index(translation)
            ]

            for plugin_name, plugin_strings in translation.strings.items():
                _strings = (
                    installed_translation.strings.get(plugin_name, []) + plugin_strings
                )

                # Remove duplicates
                installed_translation.strings[plugin_name] = list(set(_strings))

            # Merge metadata
            installed_translation.mod_id = translation.mod_id
            installed_translation.file_id = translation.file_id
            installed_translation.version = translation.version
            installed_translation.original_mod_id = translation.original_mod_id
            installed_translation.original_file_id = translation.original_file_id
            installed_translation.original_version = translation.original_version

        self.save_database()

    def delete_translation(self, translation: Translation):
        """
        Deletes `translation` from database.
        """

        if translation.path.is_dir():
            rmtree(translation.path)
        if translation in self.user_translations:
            self.user_translations.remove(translation)

        self.save_database()

    def get_translation_by_plugin_name(self, plugin_name: str):
        """
        Gets a translation that covers the `plugin_name`.

        Returns None if there is no translation installed for that plugin.

        This method is case-insensitive.
        """

        translations = {
            _plugin_name.lower(): translation
            for translation in self.user_translations
            for _plugin_name in translation.strings
        }

        return translations.get(plugin_name.lower())

    def get_translation_by_mod(self, mod: Mod):
        """
        Gets a translation that covers the `mod`.

        Returns None if there is no translation installed for that mod.
        """

        installed_translations = {
            f"{translation.mod_id}###{translation.file_id}": translation
            for translation in self.user_translations
            if translation.mod_id and translation.file_id
        }

        if f"{mod.mod_id}###{mod.file_id}" in installed_translations:
            return installed_translations[f"{mod.mod_id}###{mod.file_id}"]

        elif mod.plugins:
            return self.get_translation_by_plugin_name(mod.plugins[0].name)

    def get_translation_by_id(self, mod_id: int, file_id: int = None):
        """
        Gets translation with `mod_id` and `file_id` if installed.
        """

        if mod_id == 0 or file_id == 0:
            return

        if file_id is not None:
            installed_translations = {
                f"{translation.mod_id}###{translation.file_id}": translation
                for translation in self.user_translations
            }

            return installed_translations.get(f"{mod_id}###{file_id}")

        else:
            installed_translations = {
                translation.mod_id: translation
                for translation in self.user_translations
            }

            return installed_translations.get(mod_id)

    def apply_db_to_translation(
        self, translation: Translation, plugin_name: str = None
    ):
        """
        Applies database to untranslated strings in `translation`.
        """

        installed_translations = [self.vanilla_translation] + self.user_translations

        database_originals = {
            string.original_string: string
            for _translation in installed_translations
            for _plugin_name, plugin_strings in _translation.strings.items()
            if _translation != translation or _plugin_name != plugin_name
            for string in plugin_strings
            if string.status != String.Status.TranslationRequired
        }
        database_strings = {
            f"{string.form_id.lower()[2:]}###{string.editor_id}###{string.type}###{string.index}": string
            for translation in installed_translations
            for plugin_strings in translation.strings.values()
            for string in plugin_strings
            if string.status != String.Status.TranslationRequired
        }

        if plugin_name is not None:
            strings = [
                string
                for string in translation.strings[plugin_name]
                if string.status == string.Status.TranslationRequired
            ]
        else:
            strings = [
                string
                for plugin_strings in translation.strings.values()
                for string in plugin_strings
                if string.status == string.Status.TranslationRequired
            ]

        if not len(strings):
            return

        self.log.info(f"Translating {len(strings)} string(s) from database...")
        self.log.debug(
            f"Database size: {len(database_strings)} string(s) ({len(database_originals)} original(s))"
        )

        translated = 0
        for string in strings:
            matching = database_strings.get(
                f"{string.form_id.lower()[2:]}###{string.editor_id}###{string.type}###{string.index}"
            )

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

    def create_translation(self, plugin_path: Path, cache: Cacher):
        """
        Creates translation for plugin at `plugin_path` by extracting its strings
        and applying translations from database to them.
        """

        translation = self.get_translation_by_plugin_name(plugin_path.name)
        if translation:
            return translation

        plugin_strings = cache.get_plugin_strings(plugin_path)

        for string in plugin_strings:
            string.translated_string = string.original_string
            string.status = string.Status.TranslationRequired

        translation_name = f"{plugin_path.name} - {self.language.capitalize()}"
        translation = Translation(
            name=translation_name,
            mod_id=0,
            file_id=0,
            version="",
            original_mod_id=0,
            original_file_id=0,
            original_version="",
            path=self.userdb_path / self.language / translation_name,
            strings={plugin_path.name.lower(): plugin_strings},
            source=Source.Local,
            timestamp=int(time.time()),
        )
        self.apply_db_to_translation(translation, plugin_path.name.lower())

        return translation

    def get_strings(self):
        """
        Returns list of all strings that are in the database.
        """

        result: list[String] = []

        result += [
            string
            for plugin_strings in self.vanilla_translation.strings.values()
            for string in plugin_strings
        ]

        result += [
            string
            for translation in self.user_translations
            for plugin_strings in translation.strings.values()
            for string in plugin_strings
            if string.status != String.Status.TranslationRequired
        ]

        return result

    def search_database(self, filter: dict[str, str]):
        """
        Returns strings from database that match `filter`.

        Example for `filter`:
        ```
        {
            "editor_id": "SomeEditorID123",
            "form_id": "00123456|Skyrim.esm",
            "original": "Some untranslated string",
        }
        ```

        Keys that are not in `filter` are ignored.
        """

        self.log.info("Searching database...")
        self.log.debug(f"Filter: {filter}")

        type_filter = filter.get("type")
        form_id_filter = filter.get("form_id")
        editor_id_filter = filter.get("editor_id")
        original_filter = filter.get("original")
        string_filter = filter.get("string")

        result: dict[str, list[String]] = {}

        translations = self.user_translations + [self.vanilla_translation]

        for translation in translations:
            self.log.debug(f"Searching translation {translation.name!r}...")

            for plugin, strings in translation.strings.items():
                self.log.debug(f"Searching plugin translation {plugin!r}...")

                for string in strings:
                    matching = True

                    if type_filter:
                        matching = type_filter.lower() in string.type.lower()

                    if form_id_filter and matching:
                        matching = form_id_filter.lower() in string.form_id.lower()

                    if editor_id_filter and matching and string.editor_id is not None:
                        matching = editor_id_filter.lower() in string.editor_id.lower()
                    elif editor_id_filter:
                        matching = False

                    if original_filter and matching:
                        matching = (
                            original_filter.lower() in string.original_string.lower()
                        )

                    if (
                        string_filter
                        and matching
                        and string.translated_string is not None
                    ):
                        matching = (
                            string_filter.lower() in string.translated_string.lower()
                        )
                    elif string_filter:
                        matching = False

                    if matching:
                        if plugin in result:
                            result[plugin].append(string)
                        else:
                            result[plugin] = [string]

        self.log.info(
            f"Found {sum(len(strings) for strings in result.values())} matching string(s) in {len(result)} plugin(s)."
        )

        return result
