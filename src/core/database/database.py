"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.mod_instance.mod import Mod
from core.string.search_filter import SearchFilter, matches_filter
from core.string.string_status import StringStatus
from core.string.types import StringList
from core.translation_provider.mod_id import ModId
from core.utilities.game_language import GameLanguage

from .translation import Translation


class TranslationDatabase(QObject):
    """
    Class for translation database manager.
    """

    update_signal = Signal()
    """
    This signal gets emitted everytime, a translation is added, removed or renamed.
    """

    add_signal = Signal(list)
    """
    This signal gets emitted when at least one translation is added.

    Args:
        list[Translation]: The added translations.
    """

    remove_signal = Signal(list)
    """
    This signal gets emitted when at least translation is removed.

    Args:
        list[Translation]: The removed translations.
    """

    userdb_path: Path
    """The path to the user database directory (language not included)."""

    appdb_path: Path
    """The path to the app database directory (language not included)."""

    language: GameLanguage
    """The language of the database."""

    __vanilla_translation: Translation
    __user_translations: list[Translation]

    log: logging.Logger = logging.getLogger("TranslationDatabase")

    def __init__(
        self,
        userdb_path: Path,
        appdb_path: Path,
        language: GameLanguage,
        vanilla_translation: Translation,
        user_translations: list[Translation],
    ) -> None:
        """
        Args:
            userdb_path (Path): Path to the user database directory.
            appdb_path (Path): Path to the application database directory.
            language (GameLanguage): Language of the database.
            vanilla_translation (Translation): Translation for base game + AE CC Content.
            user_translations (list[Translation]): List of user installed translations.
        """

        super().__init__()

        self.userdb_path = userdb_path
        self.appdb_path = appdb_path
        self.language = language

        self.__vanilla_translation = vanilla_translation
        self.__user_translations = user_translations

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
        """

        return self.__user_translations

    @property
    def strings(self) -> StringList:
        """
        A list of all strings in the database.
        """

        result: StringList = []

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
            if string.status != StringStatus.TranslationRequired
        ]

        return result

    def get_translation_by_modfile_path(
        self, modfile_path: Path
    ) -> Optional[Translation]:
        """
        Gets a translation that covers a specified mod file.
        This method is case-insensitive.

        Args:
            modfile_path (Path):
                Path of the mod file, relative to the game's "Data" folder.

        Returns:
            Optional[Translation]: Translation that covers the mod file or None.
        """

        translations = {
            _modfile: translation
            for translation in self.user_translations
            for _modfile in translation.strings
        }

        return translations.get(Path(modfile_path))

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
            for translation in self.user_translations
            if translation.mod_id
        }

        translation: Optional[Translation] = None
        if (
            mod.mod_id is not None
            and f"{mod.mod_id.mod_id}###{mod.mod_id.file_id}" in installed_translations
        ):
            translation = installed_translations[
                f"{mod.mod_id.mod_id}###{mod.mod_id.file_id}"
            ]

        elif mod.modfiles:
            translation = self.get_translation_by_modfile_path(mod.modfiles[0].path)

        return translation

    def get_translation_by_mod_id(self, mod_id: ModId) -> Optional[Translation]:
        """
        Gets a translation for a specified mod and file id if installed.

        Args:
            mod_id (ModId): Mod id.

        Returns:
            Optional[Translation]: Translation or None.
        """

        translations: dict[ModId, Translation] = {
            translation.mod_id: translation
            for translation in self.user_translations
            if translation.mod_id is not None
        }

        return translations.get(mod_id)

    def get_translation_for_id(self, id: str) -> Translation:
        """
        Gets a translation for the specified ID.

        Args:
            id (str): ID of the translation to get.

        Raises:
            KeyError:
                If the translation with the specified ID is not found in the database.

        Returns:
            Translation: The translation with the specified ID.
        """

        for translation in self.user_translations:
            if translation.id == id:
                return translation

        else:
            raise KeyError(f"Translation with ID '{id}' not found in database.")

    def is_translation_in_database(self, translation: Translation) -> bool:
        """
        Checks if a translation is already installed in the database.

        Args:
            translation (Translation): Translation to check.

        Returns:
            bool: `True` if the translation is in the database, `False` otherwise.
        """

        return any(t.id == translation.id for t in self.user_translations)

    def search_database(self, filter: SearchFilter) -> dict[Path, StringList]:
        """
        Returns strings from database that match a specified filter.

        Args:
            filter (SearchFilter): Filter options.

        Returns:
            dict[Path, StringList]: Strings that match the filter.
        """

        self.log.info("Searching database...")
        self.log.debug(f"Filter: {filter}")

        result: dict[Path, StringList] = {}
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
