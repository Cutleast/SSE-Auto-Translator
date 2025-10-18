"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.utilities.exception_handler import ExceptionHandler
from cutleast_core_lib.core.utilities.singleton import SingletonQObject
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog

from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.masterlist.masterlist import Masterlist
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.mod_instance_loader import ModInstanceLoader
from core.utilities.game_language import GameLanguage

from .user_data import UserData


class UserDataService(SingletonQObject):
    """
    Service class that manages the user data (config, database, modinstance, etc.).
    """

    __res_path: Path
    __data_path: Path

    __user_data: Optional[UserData] = None

    log: logging.Logger = logging.getLogger("UserDataService")

    def __init__(self, res_path: Path, data_path: Path) -> None:
        """
        Args:
            res_path (Path): Path to the folder with the application resources.
            data_path (Path): Path to the folder with the user data.
        """

        super().__init__()

        self.__res_path = res_path
        self.__data_path = data_path

    def load(self, ldialog: Optional[LoadingDialog[UserData]] = None) -> UserData:
        """
        Loads the user data from the configured folder.

        Args:
            ldialog (Optional[LoadingDialog[UserData]], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            UserData: The loaded user data.
        """

        self.log.info(f"Loading user data from '{self.__data_path}'...")

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Loading user configuration..."))

        user_config = self.__load_user_config()

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Loading translator configuration..."))

        translator_config = self.__load_translator_config()

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Loading translation database..."))

        database = self.__load_database(user_config.language, ldialog)

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Loading modlist..."))

        modinstance = self.__load_modinstance(user_config, ldialog)

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Loading masterlist..."))

        masterlist = self.__load_masterlist(user_config)

        self.__user_data = UserData(
            user_config=user_config,
            translator_config=translator_config,
            database=database,
            modinstance=modinstance,
            masterlist=masterlist,
        )

        self.log.info("Loaded user data.")

        return self.__user_data

    def __load_user_config(self) -> UserConfig:
        self.log.info("Loading user configuration...")

        return UserConfig.load(self.__data_path)

    def __load_translator_config(self) -> TranslatorConfig:
        self.log.info("Loading translator configuration...")

        return TranslatorConfig.load(self.__data_path)

    def __load_database(
        self, language: GameLanguage, ldialog: Optional[LoadingDialog[UserData]] = None
    ) -> TranslationDatabase:
        self.log.info(f"Loading translation database for language '{language}'...")

        appdb_path: Path = self.__res_path / "app" / "database"
        userdb_path: Path = self.__data_path / "user" / "database"

        return DatabaseService.load_database(appdb_path, userdb_path, language)

    def __load_modinstance(
        self, user_config: UserConfig, ldialog: Optional[LoadingDialog[UserData]] = None
    ) -> ModInstance:
        if user_config.modinstance is not None:
            self.log.info("Loading modinstance...")

            return ModInstanceLoader().load_instance(
                instance_info=user_config.modinstance,
                language=user_config.language,
                include_bsas=user_config.parse_bsa_archives,
                ldialog=ldialog,
            )

        self.log.info("No modinstance configured. Creating empty modinstance...")
        return ModInstance(self.tr("<No modinstance selected>"), [])

    def __load_masterlist(self, user_config: UserConfig) -> Masterlist:
        self.log.info("Loading masterlist...")

        if user_config.use_masterlist:
            try:
                return Masterlist.load_from_repo(user_config.language)
            except Exception as ex:
                self.log.error(
                    f"Failed to load masterlist from repository: {ex}", exc_info=ex
                )
        else:
            self.log.info("Masterlist disabled by user.")

        return Masterlist(entries={})

    def is_setup_required(self) -> bool:
        """
        Checks if the user data is not yet setup.

        Returns:
            bool: True if the user data is not yet setup, False otherwise.
        """

        return (
            not (self.__data_path / "user" / "config.json").is_file()
        ) or ExceptionHandler.raises_exception(
            lambda: UserConfig.load(self.__data_path, log_settings=False)
        )

    def get_user_data(self) -> UserData:
        """
        Returns:
            UserData: Loaded user data.

        Raises:
            ValueError: When the user data is not yet loaded or setup.
        """

        if self.__user_data is None:
            raise ValueError("User data is not yet loaded or setup.")

        return self.__user_data

    def get_data_path(self) -> Path:
        """
        Returns:
            Path: The path to the user data folder.
        """

        return self.__data_path
