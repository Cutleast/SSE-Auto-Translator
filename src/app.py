"""
Copyright (c) Cutleast
"""

import logging
import os
import platform
import shutil
import subprocess
import sys
import time
import webbrowser
from argparse import Namespace
from pathlib import Path
from typing import Callable, Optional, override

from PySide6.QtCore import Qt, QTimerEvent, QTranslator, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

import resources_rc  # type: ignore # noqa: F401
from core.cache.cache import Cache
from core.config.app_config import AppConfig
from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.downloader.download_manager import DownloadManager
from core.masterlist.masterlist import Masterlist
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.mod_instance_loader import ModInstanceLoader
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.translation_provider.nm_api.nm_api import NexusModsApi
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.translation_provider.provider_manager import ProviderManager
from core.translator_api.translator import Translator
from core.utilities.container_utils import unique
from core.utilities.exception_handler import ExceptionHandler
from core.utilities.exe_info import get_current_path, get_execution_info
from core.utilities.game_language import GameLanguage
from core.utilities.localisation import LocalisationUtils
from core.utilities.logger import Logger
from core.utilities.path_limit_fixer import PathLimitFixer
from core.utilities.qt_res_provider import read_resource
from core.utilities.updater import Updater
from ui.main_window import MainWindow
from ui.startup_dialog.startup_dialog import StartupDialog
from ui.utilities.icon_provider import IconProvider, ResourceIcon
from ui.widgets.api_setup import ApiSetup
from ui.widgets.loading_dialog import LoadingDialog


class App(QApplication):
    """
    Main Application Class.
    """

    APP_NAME: str = "SSE Auto Translator"
    APP_VERSION: str = "development"

    args: Namespace
    app_config: AppConfig
    user_config: UserConfig
    translator_config: TranslatorConfig

    compiled: bool
    executable: list[str]
    """
    Stores command to execute this app.
    """

    executable, compiled = get_execution_info()

    cur_path: Path = get_current_path()
    res_path: Path = cur_path / "res"
    loc_path: Path = res_path / "locales"
    data_path: Path
    cache_path: Path
    style_path: str = ":/style.qss"

    log: logging.Logger = logging.getLogger("App")
    logger: Logger
    log_path: Path

    timer_signal = Signal()
    """
    This signal gets emitted every 1000ms.
    """

    exit_chain: list[Callable[[], None]] = []
    """
    List of functions to call before the application exits.
    """

    setup_required: bool
    setup_complete: bool = True

    # App components
    provider: Provider
    database: TranslationDatabase
    nxm_listener: NXMHandler
    translator: Translator
    cache: Cache
    exception_handler: ExceptionHandler
    mod_instance: ModInstance
    state_service: StateService
    scanner: Scanner
    download_manager: DownloadManager
    masterlist: Masterlist

    main_window: MainWindow

    def __init__(self, args: Namespace):
        super().__init__()

        self.args = args

        self.data_path = (
            (self.cur_path / "data") if not args.data_path else Path(args.data_path)
        )
        self.cache_path = self.data_path / "cache"
        self.log_path = self.data_path / "logs"

        # Check if there is a loadable user config and show setup if required
        self.setup_required: bool = (
            not (self.data_path / "user" / "config.json").is_file()
        ) or ExceptionHandler.raises_exception(lambda: UserConfig.load(self.data_path))

    def init(self) -> None:
        """
        Initializes the application.
        """

        self.app_config = AppConfig.load(self.data_path)

        log_file: Path = self.log_path / time.strftime(self.app_config.log_file_name)
        self.logger = Logger(
            log_file, self.app_config.log_format, self.app_config.log_date_format
        )
        self.logger.setLevel(self.app_config.log_level)

        self.load_localisation()
        self.load_theme()

        self.cache = Cache(self.cache_path, App.APP_VERSION)
        self.cache.load_caches()

        self.exception_handler = ExceptionHandler(self, self.logger)

        self.setApplicationName(App.APP_NAME)
        self.setApplicationDisplayName(f"{App.APP_NAME} v{App.APP_VERSION}")
        self.setApplicationVersion(App.APP_VERSION)
        self.setWindowIcon(IconProvider.get_res_icon(ResourceIcon.SSEAT))

        self.log_basic_info()

    @override
    def exec(self) -> int:  # type: ignore
        self.log.info("Application started.")

        try:
            Updater(self.APP_VERSION).run()
        except Exception as ex:
            self.log.warning(f"Failed to check for updates: {ex}", exc_info=ex)

        if self.setup_required:
            self.setup_complete = (
                StartupDialog(self.cache, QApplication.activeModalWidget()).exec()
                == QDialog.DialogCode.Accepted
            )

        retcode: int = 0
        if self.setup_complete:
            self.__start_main_app()
            retcode = super().exec()

        self.log.info("Exiting application...")

        for function in unique(self.exit_chain):
            function()

        self.cache.save_caches()
        self.clean()

        return retcode

    def __start_main_app(self) -> None:
        self.__load_user_data()
        self.__load_masterlist()

        self.nxm_listener = NexusModsApi.NXM_HANDLER
        if self.app_config.auto_bind_nxm:
            self.nxm_listener.bind()
            self.log.info("Bound Nexus Mods Links.")
        # TODO: Reimplement this
        # self.nxm_listener.request_signal.connect(
        #     self.download_manager.add_download_item
        # )
        # self.nxm_listener.download_signal.connect(
        #     lambda url: self.log.info(f"Handled NXM link: {url}")
        # )
        self.download_manager = DownloadManager(
            self.database,
            self.mod_instance,
            self.provider,
            self.app_config,
            self.user_config,
            self.masterlist,
        )
        self.scanner = Scanner(
            self.mod_instance,
            self.database,
            self.app_config,
            self.user_config,
            self.provider,
            self.masterlist,
        )

        self.main_window = MainWindow(
            self.cache,
            self.database,
            self.app_config,
            self.user_config,
            self.translator_config,
            self.translator,
            self.masterlist,
            self.mod_instance,
            self.scanner,
            self.provider,
            self.download_manager,
            self.state_service,
            self.nxm_listener,
            self.logger,
        )
        self.main_window.showMaximized()
        self.detect_path_limit()
        self.startTimer(1000, Qt.TimerType.PreciseTimer)

    def __load_masterlist(self) -> None:
        masterlist = Masterlist(entries={})
        if self.user_config.use_masterlist:
            try:
                masterlist = Masterlist.load_from_repo(self.user_config.language)
            except Exception as ex:
                self.log.error(
                    f"Failed to load masterlist from repository: {ex}", exc_info=ex
                )
        else:
            self.log.info("Masterlist disabled by user.")

        self.masterlist = masterlist

    def __load_user_data(self) -> None:
        """
        Loads user config and translation database.
        """

        self.log.info("Loading user data...")

        self.user_config = UserConfig.load(self.data_path)
        self.translator_config = TranslatorConfig.load(self.data_path)
        self.translator = self.translator_config.translator.get_api_class()(
            self.translator_config
        )

        self.provider = Provider(self.user_config, self.cache)
        self.__check_nm_api_key()

        self.__load_database()

        LoadingDialog.run_callable(
            QApplication.activeModalWidget(), self.__load_modinstance
        )

        self.state_service = StateService(self.cache, self.mod_instance, self.database)

        self.log.info("Loaded user data.")

    def __check_nm_api_key(self) -> None:
        try:
            nm_api: NexusModsApi = ProviderManager.get_provider(NexusModsApi)
        except ValueError:
            self.log.warning("No Nexus Mods API available.")
        else:
            nm_api_valid = nm_api.is_api_key_valid(self.user_config.api_key)

            if not nm_api_valid:
                self.__run_nm_api_key_setup(nm_api)

    def __run_nm_api_key_setup(self, nm_api: NexusModsApi) -> None:
        self.log.error("Nexus Mods API Key is invalid!")

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle(self.tr("API Key is invalid!"))
        dialog.setMinimumSize(800, 400)

        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        api_setup = ApiSetup(self.cache)
        vlayout.addWidget(api_setup)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        save_button = QPushButton(self.tr("Save"))
        save_button.setDefault(True)
        save_button.setDisabled(True)
        api_setup.valid_signal.connect(save_button.setEnabled)

        def save() -> None:
            if api_setup.api_key is None:
                raise ValueError("API Key is required")
            self.user_config.api_key = api_setup.api_key
            nm_api.set_api_key(self.user_config.api_key)

            self.user_config.save()
            dialog.accept()

        save_button.clicked.connect(save)
        hlayout.addWidget(save_button)

        exit_button = QPushButton(self.tr("Cancel"))
        exit_button.clicked.connect(dialog.reject)
        hlayout.addWidget(exit_button)

        if dialog.exec() == dialog.DialogCode.Rejected:
            self.clean()
            sys.exit()

    def __load_database(self) -> None:
        language: GameLanguage = self.user_config.language
        userdb_path: Path = self.data_path / "user" / "database"
        appdb_path: Path = self.res_path / "app" / "database"

        self.log.info("Loading translation database...")

        def process(ldialog: LoadingDialog) -> None:
            ldialog.updateProgress(
                text1=self.tr("Loading translation database..."),
            )

            self.database = DatabaseService.load_database(
                appdb_path, userdb_path, language
            )

        LoadingDialog.run_callable(QApplication.activeModalWidget(), process)

    def __load_modinstance(self, ldialog: Optional[LoadingDialog] = None) -> None:
        self.log.info("Loading modinstance...")

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Loading modinstance..."))

        if self.user_config.modinstance is not None:
            self.mod_instance = ModInstanceLoader().load_instance(
                self.user_config.modinstance,
                self.user_config.language,
                any(
                    (
                        self.user_config.enable_interface_files,
                        self.user_config.enable_scripts,
                        self.user_config.enable_textures,
                        self.user_config.enable_sound_files,
                    )
                ),
            )
        else:
            self.mod_instance = ModInstance(self.tr("<No modinstance selected>"), [])

        self.log.info(
            f"Loaded {self.mod_instance.display_name!r} with "
            f"{len(self.mod_instance.mods)} mod(s) and "
            f"{len(self.mod_instance.modfiles)} mod file(s)."
        )

    def log_basic_info(self) -> None:
        """
        Logs basic information.
        """

        width = 100
        log_title = f" {self.APP_NAME} ".center(width, "=")
        self.log.info(f"\n{'=' * width}\n{log_title}\n{'=' * width}")
        self.log.info(f"Program Version: {self.APP_VERSION}")
        self.log.info(f"Executed command: {self.executable}")
        self.log.info(f"Compiled: {self.compiled}")
        self.log.info(f"Current Path: {self.cur_path}")
        self.log.info(f"Resource Path: {self.res_path}")
        self.log.info(f"Data Path: {self.data_path}")
        self.log.info(f"Cache Path: {self.cache_path}")
        self.log.info(f"Log Path: {self.log_path}")
        self.log.debug(
            f"Detected Platform: \
{platform.system()} \
{platform.version()} \
{platform.architecture()[0]}"
        )
        self.log.info(f"Setup required: {self.setup_required}")

        self.app_config.print_settings_to_log()

    def load_localisation(self) -> None:
        translator = QTranslator(self)

        language: str
        if self.app_config.language.name == "System":
            language = LocalisationUtils.detect_system_locale() or "en_US"
        else:
            language = self.app_config.language.value

        if language != "en_US":
            translator.load(f":/loc/{language}.qm")
            self.installTranslator(translator)

            self.log.info(f"Loaded localisation for {language}.")

    def load_theme(self) -> None:
        """
        Loads stylesheet and applies user set accent color.
        """

        stylesheet: str = read_resource(self.style_path)
        accent_color: str = self.app_config.accent_color

        highlighted_accent: str = QColor(accent_color).lighter(110).name()

        stylesheet = stylesheet.replace("<accent_color>", accent_color)
        stylesheet = stylesheet.replace("<highlighted_accent>", highlighted_accent)

        self.setStyleSheet(stylesheet)

        palette: QPalette = self.palette()
        palette.setColor(QPalette.ColorRole.Link, QColor(accent_color))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(highlighted_accent))
        palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Accent, QColor(accent_color))
        self.setPalette(palette)

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
    def timerEvent(self, event: QTimerEvent) -> None:
        super().timerEvent(event)

        self.timer_signal.emit()

    def clean(self) -> None:
        """
        Cleans up temporary files, running downloads and log folder.
        """

        if self.setup_complete:
            self.download_manager.stop()

            if self.nxm_listener.is_bound():
                self.nxm_listener.unbind()
                self.log.info("Unbound Nexus Mods Links.")

        shutil.rmtree(self.app_config.get_tmp_dir())

        self.logger.clean_log_folder(
            self.log_path,
            self.app_config.log_file_name,
            self.app_config.log_num_of_files,
        )

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
