"""
Copyright (c) Cutleast
"""

import os
import shutil
import subprocess
import webbrowser
from argparse import Namespace
from pathlib import Path
from typing import Callable, Optional, cast, override

from cutleast_core_lib.base_app import BaseApp
from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.config.app_config import AppConfig as BaseAppConfig
from cutleast_core_lib.core.utilities.exe_info import (
    get_current_path,
    get_execution_info,
)
from cutleast_core_lib.core.utilities.localisation import detect_system_locale
from cutleast_core_lib.core.utilities.path_limit_fixer import PathLimitFixer
from cutleast_core_lib.core.utilities.singleton import Singleton
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
)

from core.component_provider import ComponentProvider
from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.translation_provider.nm_api.nm_api import NexusModsApi
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider_manager import ProviderManager
from core.user_data.user_data import UserData
from core.user_data.user_data_service import UserDataService
from core.utilities.container_utils import unique
from core.utilities.localisation import Language
from resources_rc import qt_resource_data as qt_resource_data
from ui.main_window import MainWindow
from ui.startup_dialog.startup_dialog import StartupDialog
from ui.utilities.icon_provider import IconProvider, ResourceIcon
from ui.utilities.theme_manager import ThemeManager
from ui.widgets.api_setup_dialog import ApiSetupDialog


class App(BaseApp, Singleton):
    """
    Main Application Class.
    """

    APP_NAME: str = "SSE Auto Translator"
    APP_VERSION: str = "development"

    __user_data: Optional[UserData] = None
    __user_data_service: UserDataService

    compiled: bool
    executable: list[str]
    """
    Stores command to execute this app.
    """

    executable, compiled = get_execution_info()

    exit_chain: list[Callable[[], None]] = []
    """
    List of functions to call before the application exits.
    """

    setup_complete: bool = True

    __component_provider: Optional[ComponentProvider] = None

    def __init__(self, args: Namespace) -> None:
        Singleton.__init__(self)

        self.data_path = (
            (self.cur_path / "data") if not args.data_path else Path(args.data_path)
        )
        self.cache_path = self.data_path / "cache"
        self.log_path = self.data_path / "logs"

        Cache(self.cache_path, App.APP_VERSION)
        self.__user_data_service = UserDataService(self.res_path, self.data_path)

        super().__init__(args)

    @override
    def _init(self) -> None:
        """
        Initializes the application.
        """

        self.setApplicationName(App.APP_NAME)
        self.setApplicationDisplayName(f"{App.APP_NAME} v{App.APP_VERSION}")
        self.setApplicationVersion(App.APP_VERSION)
        self.setWindowIcon(IconProvider.get_res_icon(ResourceIcon.SSEAT))

        super()._init()

    @override
    def _load_app_config(self) -> BaseAppConfig:
        app_config = AppConfig.load(self.data_path)
        app_config.debug_mode = getattr(self.args, "debug_mode", False)

        return app_config

    @override
    def _get_theme_manager(self) -> Optional[ThemeManager]:
        return ThemeManager(self.app_config.accent_color, self.app_config.ui_mode)

    @override
    def _init_main_window(self) -> MainWindow:
        self.__load_translation()

        return MainWindow()

    def __load_translation(self) -> None:
        """
        Loads translation for the configured language and installs the translator into
        the app.
        """

        translator = QTranslator(self)

        app_config: AppConfig = cast(AppConfig, self.app_config)

        language: str
        if app_config.language == Language.System:
            language = detect_system_locale() or "en_US"
        else:
            language = app_config.language.value

        if language != "en_US":
            res_file: str = f":/loc/{language}.qm"
            if not translator.load(res_file):
                self.log.error(
                    f"Failed to load localisation for {language} from '{res_file}'."
                )
            else:
                self.installTranslator(translator)
                self.log.info(f"Loaded localisation for {language}.")

    @override
    def exec(self) -> int:
        self.log.info("Application started.")

        if self.__user_data_service.is_setup_required():
            self.setup_complete = (
                StartupDialog(self.data_path, QApplication.activeModalWidget()).exec()
                == QDialog.DialogCode.Accepted
            )

        retcode: int = 0
        if self.setup_complete:
            self.__start_main_app()
            retcode = super().exec()

        return retcode

    def __start_main_app(self) -> None:
        self.__user_data = LoadingDialog.run_callable(
            QApplication.activeModalWidget(), self.__user_data_service.load
        )

        app_config: AppConfig = cast(AppConfig, self.app_config)

        if app_config.auto_bind_nxm and NXMHandler.has_instance():
            NXMHandler.get().bind()
            self.log.info("Bound Nexus Mods Links.")
        # TODO: Reimplement this
        # self.nxm_listener.request_signal.connect(
        #     self.download_manager.add_download_item
        # )
        # self.nxm_listener.download_signal.connect(
        #     lambda url: self.log.info(f"Handled NXM link: {url}")
        # )
        self.__component_provider = ComponentProvider(app_config, self.__user_data)

        LoadingDialog.run_callable(
            QApplication.activeModalWidget(),
            self.__component_provider.initialize_components,
        )

        main_window: MainWindow = cast(MainWindow, self.main_window)
        main_window.initialize(
            cast(AppConfig, self.app_config),
            self.__user_data,
            self.__component_provider.get_translator(),
            self.__component_provider.get_scanner(),
            self.__component_provider.get_provider(),
            self.__component_provider.get_download_manager(),
            self.__component_provider.get_state_service(),
        )
        main_window.showMaximized()

        self.__check_nm_api_key(self.__user_data.user_config)
        self.detect_path_limit()

    def __check_nm_api_key(self, user_config: UserConfig) -> None:
        try:
            nm_api: NexusModsApi = ProviderManager.get_provider(NexusModsApi)
        except ValueError:
            self.log.warning("No Nexus Mods API available.")
        else:
            nm_api_valid = nm_api.is_api_key_valid(user_config.api_key)

            if not nm_api_valid:
                self.__run_nm_api_key_setup(nm_api, user_config)

    def __run_nm_api_key_setup(
        self, nm_api: NexusModsApi, user_config: UserConfig
    ) -> None:
        self.log.error("Nexus Mods API Key is invalid!")

        dialog = ApiSetupDialog()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_config.api_key = dialog.get_api_key()
            user_config.save()

            nm_api.set_api_key(user_config.api_key)

        else:
            self.exit()

    def detect_path_limit(self) -> None:
        """
        Detects if the NTFS path length limit is enabled
        and asks if the user wants to disable it.
        """

        path_limit_enabled: bool = PathLimitFixer.is_path_limit_enabled()
        self.log.info(f"Path length limit enabled: {path_limit_enabled}")

        if path_limit_enabled:
            reply = QMessageBox.question(
                self.main_window,
                self.tr("Path Limit Enabled"),
                self.tr(
                    "The NTFS path length limit is enabled and paths longer than 255 "
                    "characters will cause issues. Would you like to disable it now "
                    "(admin rights may be required)? "
                    "A reboot is required for this to take effect.\n\n"
                    "You can always disable it later under "
                    "Help > Fix Windows Path Limit."
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                PathLimitFixer.disable_path_limit(self.res_path)

    @override
    def clean(self) -> None:
        """
        Cleans up temporary files, running downloads and log folder.
        """

        super().clean()

        for function in unique(self.exit_chain):
            function()

        if self.__component_provider is not None:
            self.__component_provider.get_download_manager().stop()

        if NXMHandler.has_instance() and NXMHandler.get().is_bound():
            NXMHandler.get().unbind()
            self.log.info("Unbound Nexus Mods Links.")

        shutil.rmtree(cast(AppConfig, self.app_config).get_tmp_dir())

    def get_execution_command(self) -> str:
        """
        Returns the joined command this application was started with.
        """

        return subprocess.list2cmdline(self.executable)

    @staticmethod
    def open_documentation() -> None:
        """
        Opens the documentation in the default browser.
        """

        webbrowser.open(
            "file://" + str(get_current_path() / "doc" / "Instructions_en_US.html")
        )

    def restart_application(self) -> None:
        """
        Restarts the application.
        """

        exe_path: str = self.get_execution_command()
        if os.path.isfile(exe_path):
            os.startfile(exe_path)
        self.exit()

    @override
    @classmethod
    def get_repo_owner(cls) -> Optional[str]:
        return "Cutleast"

    @override
    @classmethod
    def get_repo_name(cls) -> Optional[str]:
        return "SSE-Auto-Translator"

    @override
    @classmethod
    def get_repo_branch(cls) -> Optional[str]:
        return "master"
