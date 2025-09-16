"""
Copyright (c) Cutleast
"""

import logging
import subprocess
from typing import Optional

from cutleast_core_lib.core.utilities.exe_info import get_execution_info
from cutleast_core_lib.core.utilities.singleton import Singleton

from core.config.app_config import AppConfig
from core.downloader.download_manager import DownloadManager
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.translator_api.translator import Translator
from core.user_data.user_data import UserData


class ComponentProvider(Singleton):
    """
    Provider class for initializing and providing the app components.
    """

    __app_config: AppConfig
    __user_data: UserData

    __provider: Optional[Provider] = None
    __translator: Optional[Translator] = None
    __state_service: Optional[StateService] = None
    __scanner: Optional[Scanner] = None
    __download_manager: Optional[DownloadManager] = None

    log: logging.Logger = logging.getLogger("ComponentProvider")

    def __init__(self, app_config: AppConfig, user_data: UserData) -> None:
        super().__init__()

        self.__app_config = app_config
        self.__user_data = user_data

    def initialize_components(self) -> None:
        """
        Initializes the app components.
        """

        self.log.info("Initializing app components...")

        NXMHandler(subprocess.list2cmdline(get_execution_info()[0]))

        self.__provider = Provider(self.__user_data.user_config)

        self.__translator = (
            self.__user_data.translator_config.translator.get_api_class()(
                self.__user_data.translator_config
            )
        )

        self.__state_service = StateService(
            self.__user_data.modinstance, self.__user_data.database
        )

        self.__scanner = Scanner(
            self.__user_data.modinstance,
            self.__user_data.database,
            self.__app_config,
            self.__user_data.user_config,
            self.__provider,
            self.__user_data.masterlist,
        )

        self.__download_manager = DownloadManager(
            self.__user_data.database,
            self.__user_data.modinstance,
            self.__provider,
            self.__app_config,
            self.__user_data.user_config,
            self.__user_data.masterlist,
        )

        self.log.info("Initialization complete.")

    def get_provider(self) -> Provider:
        """
        Returns:
            Provider: Translation provider.

        Raises:
            ValueError: When the provider is not yet initialized.
        """

        if self.__provider is None:
            raise ValueError("Provider is not yet initialized.")

        return self.__provider

    def get_translator(self) -> Translator:
        """
        Returns:
            Translator: Translator.

        Raises:
            ValueError: When the translator is not yet initialized.
        """

        if self.__translator is None:
            raise ValueError("Translator is not yet initialized.")

        return self.__translator

    def get_state_service(self) -> StateService:
        """
        Returns:
            StateService: State service.

        Raises:
            ValueError: When the state service is not yet initialized.
        """

        if self.__state_service is None:
            raise ValueError("State service is not yet initialized.")

        return self.__state_service

    def get_scanner(self) -> Scanner:
        """
        Returns:
            Scanner: Scanner.

        Raises:
            ValueError: When the scanner is not yet initialized.
        """

        if self.__scanner is None:
            raise ValueError("Scanner is not yet initialized.")

        return self.__scanner

    def get_download_manager(self) -> DownloadManager:
        """
        Returns:
            DownloadManager: Download manager.

        Raises:
            ValueError: When the download manager is not yet initialized.
        """

        if self.__download_manager is None:
            raise ValueError("Download manager is not yet initialized.")

        return self.__download_manager
