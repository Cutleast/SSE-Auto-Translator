"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, TypeVar

from cutleast_core_lib.core.config.base_config import BaseConfig
from cutleast_core_lib.core.config.manager import ConfigManager
from mod_manager_lib.core.instance.metadata import Metadata

from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.database.translation_service import TranslationService
from core.file_types.plugin.file import PluginFile
from core.file_types.plugin.string import PluginString
from core.masterlist.masterlist import Masterlist
from core.mod_file.mod_file import ModFile
from core.mod_file.mod_file_service import ModFileService
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.string.string_status import StringStatus
from core.string.types import StringList
from core.user_data.user_data import UserData
from core.utilities.game_language import GameLanguage

from .paths import DATA_PATH

_C = TypeVar("_C", bound=BaseConfig)


class DataFactory:
    """
    Creates small, in-memory domain objects for tests, so that tests only set up
    the data they actually need instead of loading the complete test user data.
    """

    TEST_MODS_PATH: Path = DATA_PATH / "mod_instance" / "mods"
    """The (read-only) mods folder of the MO2 test instance."""

    TEST_USER_DATABASE_PATH: Path = DATA_PATH / "data" / "user" / "database" / "german"
    """The (read-only) German user database of the test user data."""

    @staticmethod
    def plugin_string(
        original: str,
        string: Optional[str] = None,
        status: StringStatus = StringStatus.TranslationComplete,
        form_id: str = "00000800|Test.esp",
        record_type: str = "WEAP FULL",
        editor_id: Optional[str] = None,
    ) -> PluginString:
        """
        Creates a plugin string.

        Args:
            original (str): The original text.
            string (Optional[str], optional): The translated text. Defaults to None.
            status (StringStatus, optional):
                The string status. Defaults to StringStatus.TranslationComplete.
            form_id (str, optional): The form id. Defaults to "00000800|Test.esp".
            record_type (str, optional): The record type. Defaults to "WEAP FULL".
            editor_id (Optional[str], optional): The editor id. Defaults to None.

        Returns:
            PluginString: The created string.
        """

        return PluginString(
            form_id=form_id,
            type=record_type,
            editor_id=editor_id,
            original=original,
            string=string,
            status=status,
        )

    @staticmethod
    def translation(
        name: str, folder: Path, strings: Optional[dict[Path, StringList]] = None
    ) -> Translation:
        """
        Creates a translation that is stored in the specified folder.

        Args:
            name (str): The name of the translation.
            folder (Path): The folder that contains the translation folder.
            strings (Optional[dict[Path, StringList]], optional):
                The strings of the translation. Defaults to None (no strings).

        Returns:
            Translation: The created translation.
        """

        return Translation.create(name=name, path=folder / name, strings=strings or {})

    @staticmethod
    def stored_translation(name: str, folder: Path) -> Translation:
        """
        Creates a translation with the strings of the equally named translation in the
        (read-only) test user database. The created translation is stored in the
        specified folder.

        Args:
            name (str): The name of the translation in the test user database.
            folder (Path): The folder that contains the translation folder.

        Returns:
            Translation: The created translation.
        """

        strings: dict[Path, StringList] = TranslationService.load_translation_strings(
            DataFactory.TEST_USER_DATABASE_PATH / name
        )

        return DataFactory.translation(name, folder, strings)

    @staticmethod
    def database(
        root: Path,
        user_translations: Optional[list[Translation]] = None,
        vanilla_strings: Optional[dict[Path, StringList]] = None,
        language: GameLanguage = GameLanguage.German,
    ) -> TranslationDatabase:
        """
        Creates an in-memory translation database that stores its files in the
        specified folder.

        Args:
            root (Path): The folder for the database files.
            user_translations (Optional[list[Translation]], optional):
                The user translations. Defaults to None (no translations).
            vanilla_strings (Optional[dict[Path, StringList]], optional):
                The strings of the vanilla translation. Defaults to None (no strings).
            language (GameLanguage, optional):
                The database language. Defaults to GameLanguage.German.

        Returns:
            TranslationDatabase: The created database.
        """

        appdb_path: Path = root / "appdb"

        return TranslationDatabase(
            userdb_path=root / "userdb",
            appdb_path=appdb_path,
            language=language,
            vanilla_translation=DataFactory.translation(
                "Base Game", appdb_path / language.id, vanilla_strings
            ),
            user_translations=user_translations or [],
        )

    @staticmethod
    def plugin_file(
        full_path: Path, status: TranslationStatus = TranslationStatus.NoneStatus
    ) -> PluginFile:
        """
        Creates a plugin file.

        Args:
            full_path (Path): The full path of the plugin.
            status (TranslationStatus, optional):
                The translation status. Defaults to TranslationStatus.NoneStatus.

        Returns:
            PluginFile: The created plugin file.
        """

        return PluginFile(name=full_path.name, full_path=full_path, status=status)

    @staticmethod
    def mod(
        name: str,
        modfiles: Optional[list[ModFile]] = None,
        path: Optional[Path] = None,
        mod_id: Optional[int] = None,
        mod_type: Mod.Type = Mod.Type.Regular,
    ) -> Mod:
        """
        Creates a mod.

        Args:
            name (str): The display name of the mod.
            modfiles (Optional[list[ModFile]], optional):
                The mod files of the mod. Defaults to None (no mod files).
            path (Optional[Path], optional):
                The folder of the mod. Defaults to a relative path with the mod name.
            mod_id (Optional[int], optional):
                The Nexus Mods id of the mod. Defaults to None.
            mod_type (Mod.Type, optional): The mod type. Defaults to Mod.Type.Regular.

        Returns:
            Mod: The created mod.
        """

        return Mod(
            display_name=name,
            path=path or Path(name),
            deploy_path=None,
            metadata=Metadata(
                mod_id=mod_id,
                file_id=None,
                version="1.0",
                file_name=None,
                game_id="skyrimspecialedition",
            ),
            installed=True,
            enabled=True,
            mod_type=mod_type,
            modfiles=modfiles or [],
        )

    @staticmethod
    def instance_mod(
        name: str,
        mod_id: Optional[int] = None,
        language: GameLanguage = GameLanguage.German,
    ) -> Mod:
        """
        Creates a mod with the mod files of the equally named mod in the (read-only)
        MO2 test instance, for tests that need to parse real files.

        Args:
            name (str): The name of the mod in the test instance.
            mod_id (Optional[int], optional):
                The Nexus Mods id of the mod. Defaults to None.
            language (GameLanguage, optional):
                The language to scan mod files for. Defaults to GameLanguage.German.

        Returns:
            Mod: The created mod.
        """

        mod: Mod = DataFactory.mod(
            name, path=DataFactory.TEST_MODS_PATH / name, mod_id=mod_id
        )
        mod.modfiles = ModFileService().get_modfiles_from_mod(
            mod, language, include_bsas=False
        )

        return mod

    @staticmethod
    def mod_instance(mods: list[Mod]) -> ModInstance:
        """
        Creates a mod instance.

        Args:
            mods (list[Mod]): The mods of the instance.

        Returns:
            ModInstance: The created mod instance.
        """

        return ModInstance("Test Instance", mods)

    @staticmethod
    def masterlist() -> Masterlist:
        """
        Creates an empty masterlist.

        Returns:
            Masterlist: The created masterlist.
        """

        return Masterlist(entries={})

    @staticmethod
    def user_config(language: GameLanguage = GameLanguage.German) -> UserConfig:
        """
        Creates a user configuration.

        Args:
            language (GameLanguage, optional):
                The game language. Defaults to GameLanguage.German.

        Returns:
            UserConfig: The created user configuration.
        """

        return UserConfig(language=language, api_key="")

    @staticmethod
    def config_manager(config: _C, folder: Path) -> ConfigManager[_C]:
        """
        Saves the specified configuration to a folder and creates its manager.

        Args:
            config (_C): The configuration.
            folder (Path): The configuration folder.

        Returns:
            ConfigManager[_C]: The manager of the configuration.
        """

        config_file: Path = folder / type(config).get_config_name()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            config.model_dump_json(indent=4, by_alias=True), encoding="utf-8"
        )

        return ConfigManager(type(config), folder)

    @staticmethod
    def user_data(
        folder: Path,
        database: TranslationDatabase,
        mod_instance: Optional[ModInstance] = None,
    ) -> UserData:
        """
        Creates user data from the specified components with default configurations
        stored in the specified folder.

        Args:
            folder (Path): The folder for the configuration files.
            database (TranslationDatabase): The translation database.
            mod_instance (Optional[ModInstance], optional):
                The mod instance. Defaults to an empty mod instance.

        Returns:
            UserData: The created user data.
        """

        return UserData(
            user_config_manager=DataFactory.config_manager(
                DataFactory.user_config(), folder
            ),
            translator_config_manager=DataFactory.config_manager(
                TranslatorConfig(), folder
            ),
            database=database,
            mod_instance=mod_instance or DataFactory.mod_instance([]),
            masterlist=DataFactory.masterlist(),
        )
