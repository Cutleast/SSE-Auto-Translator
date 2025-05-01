"""
Copyright (c) Cutleast
"""

import logging
import shutil
from argparse import Namespace
from typing import Generator

import pytest

from app import App
from app_context import AppContext
from core.cache.cache import Cache
from core.config.app_config import AppConfig
from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.downloader.download_manager import DownloadManager
from core.masterlist.masterlist import Masterlist
from core.mod_instance.mod_instance import ModInstance
from core.mod_managers.modorganizer import ModOrganizer
from core.scanner.scanner import Scanner
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.utilities.path import Path

from .base_test import BaseTest


class AppTest(BaseTest):
    """
    Base class for tests using the `App` instance and its components.
    """

    log: logging.Logger = logging.getLogger("AppTest")

    @pytest.fixture
    def app_context(self) -> Generator[App, None, None]:
        """
        Initalizes and sets a test `App` instance.

        If there is already an `App` instance, this will return it.

        This fixture is required to test classes that use the `AppContext` singleton.
        """

        if not AppContext.has_app():
            self.log.info("Initializing app...")

            app = App(self.args_namespace())

            self.log.info("Setting app context...")
            AppContext.set_app(app)

            self.log.info("Initializing app components...")
            self.mock_app_components(app)

            self.log.info("App initialization complete.")

        yield AppContext.get_app()

        self.reset_app_components(AppContext.get_app())

    def args_namespace(self) -> Namespace:
        """
        Mocks the command line arguments for the `App` instance.
        """

        namespace = Namespace()
        namespace.data_path = str(self.tmp_folder() / "data")
        return namespace

    def mock_app_components(self, app: App) -> None:
        """
        Initializes and mocks the app components for a
        partially initialized `App` instance.

        Args:
            app (App): The partially initialized `App` instance
        """

        app.app_config = self.app_config(init=True)
        app.user_config = self.user_config(init=True)
        app.translator_config = self.translator_config(init=True)
        app.cache = self.cache(init=True)
        app.database = self.database(init=True)
        app.mod_instance = self.modinstance(init=True)
        app.provider = self.provider(init=True)
        app.masterlist = self.masterlist(init=True)
        app.scanner = self.scanner(init=True)
        app.download_manager = self.download_manager(init=True)
        app.nxm_listener = self.nxm_listener(init=True)

        app.tmp_path = self.tmp_folder() / "SSE-AT_temp"
        app.tmp_path.mkdir()

        # TODO: Inialize mocked versions of missing app components

    def app_config(self, init: bool = False) -> AppConfig:
        """
        Loads the test app config from `tests/test_data/data/app`.

        Returns the loaded `AppConfig` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `AppConfig`

        Returns:
            AppConfig: The loaded `AppConfig` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().app_config

        return AppConfig(self.data_path() / "data" / "app")

    def user_config(self, init: bool = False) -> UserConfig:
        """
        Loads the test user config from `tests/test_data/data/user`.

        Returns the loaded `UserConfig` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `UserConfig`

        Returns:
            UserConfig: The loaded `UserConfig` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().user_config

        return UserConfig(self.data_path() / "data" / "user")

    def translator_config(self, init: bool = False) -> TranslatorConfig:
        """
        Loads the test translator config from `tests/test_data/data/translator`.

        Returns the loaded `TranslatorConfig` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `TranslatorConfig`

        Returns:
            TranslatorConfig: The loaded `TranslatorConfig` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().translator_config

        return TranslatorConfig(self.data_path() / "data" / "translator")

    def cache(self, init: bool = False) -> Cache:
        """
        Creates a cache instance in the temporary test folder.

        Returns the created `Cache` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `Cache`

        Returns:
            Cache: The created `Cache` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().cache

        return Cache(self.tmp_folder() / "cache", App.APP_VERSION)

    def scanner(self, init: bool = False) -> Scanner:
        """
        Creates a scanner instance.

        Returns the created `Scanner` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `Scanner`

        Returns:
            Scanner: The created `Scanner` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().scanner

        return Scanner()

    def download_manager(self, init: bool = False) -> DownloadManager:
        """
        Creates a download manager instance.

        Returns the created `DownloadManager` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `DownloadManager`

        Returns:
            DownloadManager: The created `DownloadManager` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().download_manager

        return DownloadManager()

    def masterlist(self, init: bool = False) -> Masterlist:
        """
        Creates a masterlist instance.

        Returns the created `Masterlist` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `Masterlist`

        Returns:
            Masterlist: The created `Masterlist` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().masterlist

        return Masterlist(entries={})

    def database(self, init: bool = False) -> TranslationDatabase:
        """
        Creates a translation database instance.

        Returns the created `TranslationDatabase` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`

        Args:
            init (bool, optional): Toggles whether to initialize a new `TranslationDatabase`

        Returns:
            TranslationDatabase: The created `TranslationDatabase` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().database

        user_config: UserConfig = self.user_config()
        language: str = user_config.language
        userdb_path: Path = self.tmp_folder() / "user" / "database"
        appdb_path: Path = self.res_path() / "app" / "database"

        index_path: Path = userdb_path / language / "index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("[]", encoding="utf8")

        return TranslationDatabase(userdb_path, appdb_path, language, user_config)

    def provider(self, init: bool = False) -> Provider:
        """
        Creates a provider instance.

        Returns the created `Provider` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `Provider`

        Returns:
            Provider: The created `Provider` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().provider

        user_config: UserConfig = self.user_config()
        cache: Cache = self.cache()

        return Provider(user_config, cache)

    def modinstance(self, init: bool = False) -> ModInstance:
        """
        Loads the test mod instance from `tests/test_data/mod_instance`.

        Returns the loaded `ModInstance` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `ModInstance`

        Returns:
            ModInstance: The loaded `ModInstance` instance.
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().mod_instance

        self.log.info("Loading test mod instance...")
        mod_instance: ModInstance = ModOrganizer().load_mod_instance(
            instance_name="Portable", instance_path=self.data_path() / "mod_instance"
        )
        self.log.info("Loaded test mod instance.")

        return mod_instance

    def nxm_listener(self, init: bool = False) -> NXMHandler:
        """
        Creates a NXMHandler instance.

        Returns the created `NXMHandler` instance from the `AppContext` singleton
        or initializes a new one if `init` is `True`.

        Args:
            init (bool, optional): Toggles whether to initialize a new `NXMHandler`.

        Returns:
            NXMHandler: The created `NXMHandler` instance
        """

        if AppContext.has_app() and not init:
            return AppContext.get_app().nxm_listener

        return NXMHandler("")

    def reset_app_components(self, app: App) -> None:
        """
        Resets app components to initial state and wipes out the temporary test folder.

        Args:
            app (App): The `App` instance to reset
        """

        self.log.info("Resetting app components...")

        self.log.debug("Clearing temp folder...")
        tmp_folder: Path = self.tmp_folder()
        shutil.rmtree(tmp_folder, ignore_errors=True)
        tmp_folder.mkdir()

        self.log.debug("Reinitializing app components...")
        self.mock_app_components(app)
