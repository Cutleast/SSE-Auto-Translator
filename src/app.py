"""
Copyright (c) Cutleast
"""

import logging
import os
import platform
import shutil
import sys
import tempfile
import time
from argparse import Namespace
from pathlib import Path
from typing import Any, Callable, Optional

import jstyleson as json
from PySide6.QtCore import Qt, QTimerEvent, QTranslator, Signal
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from core.cacher.cacher import Cacher
from core.config.app_config import AppConfig
from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.downloader.download_manager import DownloadManager
from core.masterlist.masterlist import Masterlist
from core.mod_instance.mod_instance import ModInstance
from core.mod_managers.mod_manager import ModManager
from core.scanner.scanner import Scanner
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.translator_api.translator import Translator
from core.utilities.container_utils import unique
from core.utilities.exception_handler import ExceptionHandler
from core.utilities.localisation import detect_system_locale
from core.utilities.logger import Logger
from core.utilities.masterlist import get_masterlist
from core.utilities.qt_res_provider import read_resource
from core.utilities.updater import Updater
from ui.main_window import MainWindow
from ui.startup_dialog.startup_dialog import StartupDialog
from ui.widgets.api_setup import ApiSetup
from ui.widgets.loading_dialog import LoadingDialog


class App(QApplication):
    """
    Main Application Class.
    """

    APP_NAME: str = "SSE Auto Translator"
    APP_VERSION: str = "3.0.0-alpha-1"

    args: Namespace
    app_config: AppConfig
    user_config: UserConfig
    translator_config: TranslatorConfig

    cur_path: Path = Path.cwd()
    res_path: Path = cur_path / "res"
    data_path: Path = cur_path / "data"
    loc_path: Path = res_path / "locales"
    cache_path: Path = data_path / "cache"
    style_path: str = ":/style.qss"
    tmp_path: Optional[Path] = None

    executable = str(cur_path / "SSE-AT.exe")
    """
    Stores command to execute this app.
    """

    log: logging.Logger = logging.getLogger("App")
    logger: Logger
    log_path: Path = data_path / "logs"

    timer_signal = Signal()
    """
    This signal gets emitted every 1000ms.
    """

    ready_signal = Signal()
    """
    This signal gets emitted when the application is ready.
    """

    exit_chain: list[Callable[[], None]] = []
    """
    List of functions to call before the application exits.
    """

    first_start: bool = not (data_path / "user" / "config.json").is_file()
    setup_complete: bool = True

    main_window: MainWindow
    provider: Provider
    database: TranslationDatabase
    nxm_listener: NXMHandler
    translator: Translator
    cacher: Cacher
    exception_handler: ExceptionHandler
    mod_instance: ModInstance
    scanner: Scanner
    download_manager: DownloadManager
    masterlist: Masterlist

    def __init__(self, args: Namespace):
        super().__init__()

        self.args = args

    def init(self) -> None:
        """
        Initializes the application.
        """

        self.app_config = AppConfig(self.data_path / "app")

        log_file: Path = self.log_path / time.strftime(self.app_config.log_file_name)
        self.logger = Logger(
            log_file, self.app_config.log_format, self.app_config.log_date_format
        )
        self.logger.setLevel(self.app_config.log_level)

        self.load_localisation()
        self.load_theme()

        self.cacher = Cacher(self.cache_path)
        self.cacher.load_caches()

        self.exception_handler = ExceptionHandler(self)
        self.main_window = MainWindow()

        self.setApplicationName(self.APP_NAME)
        self.setApplicationDisplayName(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.setApplicationVersion(self.APP_VERSION)
        self.setWindowIcon(QIcon(":/icons/icon.png"))

        self.log_basic_info()

    def exec(self) -> int:
        self.log.info("Application started.")

        Updater(self.APP_VERSION).run()

        if self.first_start:
            self.setup_complete = (
                StartupDialog(QApplication.activeModalWidget()).exec()
                == QDialog.DialogCode.Accepted
            )

        retcode: int = 0
        if self.setup_complete:
            self.__start_main_app()
            retcode = super().exec()

        self.log.info("Exiting application...")

        for function in unique(self.exit_chain):
            function()

        self.cacher.save_caches()
        self.clean()

        return retcode

    def __start_main_app(self) -> None:
        self.load_user_data()
        self.load_masterlist()

        self.nxm_listener = NXMHandler()
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
        self.scanner = Scanner()
        self.download_manager = DownloadManager()

        self.ready_signal.emit()

        self.main_window.showMaximized()
        self.startTimer(1000, Qt.TimerType.PreciseTimer)

    def load_masterlist(self) -> None:
        """
        Loads masterlist from repository.

        TODO: Move this to the masterlist module
        """

        if not self.user_config.use_masterlist:
            self.log.info("Masterlist disabled by user.")
            self.masterlist = Masterlist(entries={})
            return

        self.log.info("Loading Masterlist from Repository...")

        try:
            masterlist_data: dict[str, dict[str, Any]] = get_masterlist(
                self.user_config.language
            )
            self.masterlist = Masterlist.from_data(masterlist_data)
            self.log.info("Masterlist loaded.")
        except Exception as ex:
            if str(ex).endswith("404"):
                self.log.error(
                    f"No Masterlist available for {self.user_config.language!r}."
                )
            else:
                self.log.error(f"Failed to load masterlist: {ex}")
            self.masterlist = Masterlist(entries={})

    def load_user_data(self) -> None:
        """
        Loads user config and translation database.

        TODO: Refactor this
        """

        self.log.info("Loading user data...")

        self.user_config = UserConfig(self.data_path / "user")
        self.translator_config = TranslatorConfig(self.data_path / "translator")
        self.translator = self.translator_config.translator()

        # Backwards-compatibility with portable.txt
        portable_txt_path: Path = self.data_path / "user" / "portable.txt"
        if self.user_config.modinstance == "Portable" and portable_txt_path.is_file():
            self.user_config.instance_path = Path(
                portable_txt_path.read_text("utf-8").strip()
            )
            os.remove(portable_txt_path)
            self.user_config.save()

        self.provider = Provider(
            self.user_config.api_key,
            self.cacher,
            self.user_config.provider_preference,
        )
        nm_api_valid = self.provider.check_api_key()

        if not nm_api_valid:
            self.log.error("Nexus Mods API Key is invalid!")

            dialog = QDialog(self.main_window)
            dialog.setWindowTitle(self.tr("API Key is invalid!"))
            dialog.setMinimumSize(800, 400)

            vlayout = QVBoxLayout()
            dialog.setLayout(vlayout)

            api_setup = ApiSetup()
            vlayout.addWidget(api_setup)

            hlayout = QHBoxLayout()
            vlayout.addLayout(hlayout)

            hlayout.addStretch()

            save_button = QPushButton(self.tr("Save"))
            save_button.setObjectName("accent_button")
            save_button.setDisabled(True)
            api_setup.valid_signal.connect(lambda valid: save_button.setEnabled(valid))

            def save() -> None:
                if api_setup.api_key is None:
                    raise ValueError("API Key is required")
                self.user_config.api_key = api_setup.api_key
                self.provider.api_key = self.user_config.api_key

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

        language = self.user_config.language.lower()
        userdb_path: Path = self.data_path / "user" / "database" / language
        appdb_path: Path = self.res_path / "app" / "database"

        if not userdb_path.is_dir():
            os.makedirs(userdb_path, exist_ok=True)

            index_path = userdb_path / "index.json"
            with open(index_path, "w", encoding="utf8") as index_file:
                json.dump([], index_file, indent=4)

        self.log.info("Loading translation database...")

        def process(ldialog: LoadingDialog) -> None:
            ldialog.updateProgress(
                text1=self.tr("Loading translation database..."),
            )

            self.database = TranslationDatabase(
                userdb_path.parent, appdb_path, language
            )

        LoadingDialog.run_callable(QApplication.activeModalWidget(), process)
        LoadingDialog.run_callable(
            QApplication.activeModalWidget(), self.__load_modinstance
        )

        self.log.info("Loaded user data.")

    def __load_modinstance(self, ldialog: Optional[LoadingDialog] = None) -> None:
        self.log.info("Loading modinstance...")

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Loading modinstance..."))

        mod_manager: ModManager = self.user_config.mod_manager()
        self.mod_instance = mod_manager.load_mod_instance(
            self.user_config.modinstance,
            self.user_config.instance_profile,
            self.user_config.instance_path,
        )

        self.log.info(
            f"Loaded {self.mod_instance.display_name!r} with "
            f"{len(self.mod_instance.mods)} mod(s) and "
            f"{len(self.mod_instance.plugins)} plugin(s)."
        )

    def log_basic_info(self) -> None:
        """
        Logs basic information.
        """

        width = 100
        log_title = f" {self.APP_NAME} ".center(width, "=")
        self.log.info(f"\n{'=' * width}\n{log_title}\n{'=' * width}")
        self.log.info(f"Program Version: {self.APP_VERSION}")
        self.log.info(f"Executable: {self.executable}")
        self.log.info(f"Commandline Arguments: {sys.argv}")
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
        self.log.info(f"First start: {self.first_start}")

        self.app_config.print_settings_to_log()

    def load_localisation(self) -> None:
        translator = QTranslator(self)

        language: str
        if self.app_config.language == "System":
            language = detect_system_locale() or "en_US"
        else:
            language = self.app_config.language

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

        highlighted_accent: str = QColor(accent_color).darker(120).name()

        stylesheet = stylesheet.replace("<accent_color>", accent_color)
        stylesheet = stylesheet.replace("<highlighted_accent>", highlighted_accent)

        self.setStyleSheet(stylesheet)

        palette: QPalette = self.palette()
        palette.setColor(palette.ColorRole.Link, QColor(accent_color))
        palette.setColor(palette.ColorRole.Highlight, QColor(highlighted_accent))
        palette.setColor(palette.ColorRole.Text, QColor("#ffffff"))
        palette.setColor(palette.ColorRole.Accent, QColor(accent_color))
        self.setPalette(palette)

    def get_tmp_dir(self) -> Path:
        """
        Returns path to a temporary directory.
        Creates one if needed.
        """

        if self.tmp_path is None:
            self.tmp_path = Path(
                tempfile.mkdtemp(prefix="SSE-AT_temp-", dir=self.app_config.temp_path)
            )

        return self.tmp_path

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

        if self.tmp_path is not None:
            shutil.rmtree(self.tmp_path)

        self.logger.clean_log_folder(
            self.log_path,
            self.app_config.log_file_name,
            self.app_config.log_num_of_files,
        )
