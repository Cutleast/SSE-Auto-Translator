"""
Copyright (c) Cutleast
"""

import logging
from typing import override

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from app_context import AppContext
from core.cache.cache import Cache
from core.config.app_config import AppConfig
from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.downloader.download_manager import DownloadManager
from core.masterlist.masterlist import Masterlist
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.translator_api.translator import Translator
from core.utilities.logger import Logger
from core.utilities.path_limit_fixer import PathLimitFixer
from core.utilities.updater import Updater
from ui.settings.settings_dialog import SettingsDialog
from ui.widgets.about_dialog import AboutDialog

from .main_page.main_page import MainPageWidget
from .menubar import MenuBar
from .statusbar import StatusBar
from .translation_editor.editor_page import EditorPage


class MainWindow(QMainWindow):
    """
    Class for main application window.
    """

    log: logging.Logger = logging.getLogger("App")

    cache: Cache
    database: TranslationDatabase
    app_config: AppConfig
    user_config: UserConfig
    translator_config: TranslatorConfig
    translator: Translator
    masterlist: Masterlist
    mod_instance: ModInstance
    scanner: Scanner
    provider: Provider
    download_manager: DownloadManager
    state_service: StateService
    nxm_listener: NXMHandler
    logger: Logger

    __refresh_shortcut: QShortcut

    __menu_bar: MenuBar
    tab_widget: QTabWidget
    mainpage_widget: MainPageWidget
    translation_editor: EditorPage
    __status_bar: StatusBar

    refresh_signal = Signal()
    """
    This signal is emitted when the refresh shortcut is activated.
    """

    def __init__(
        self,
        cache: Cache,
        database: TranslationDatabase,
        app_config: AppConfig,
        user_config: UserConfig,
        translator_config: TranslatorConfig,
        translator: Translator,
        masterlist: Masterlist,
        mod_instance: ModInstance,
        scanner: Scanner,
        provider: Provider,
        download_manager: DownloadManager,
        state_service: StateService,
        nxm_listener: NXMHandler,
        logger: Logger,
    ) -> None:
        super().__init__()

        self.cache = cache
        self.database = database
        self.app_config = app_config
        self.user_config = user_config
        self.translator_config = translator_config
        self.translator = translator
        self.masterlist = masterlist
        self.mod_instance = mod_instance
        self.scanner = scanner
        self.provider = provider
        self.download_manager = download_manager
        self.state_service = state_service
        self.nxm_listener = nxm_listener
        self.logger = logger

        self.setObjectName("root")

        self.__init_ui()
        self.__init_shortcuts()

    def __init_ui(self) -> None:
        self.__init_menu_bar()
        self.__init_tab_widget()
        self.__init_status_bar()

        self.resize(1500, 800)

    def __init_menu_bar(self) -> None:
        self.__menu_bar = MenuBar()
        self.setMenuBar(self.__menu_bar)

        self.__menu_bar.settings_requested.connect(self.__open_settings)
        self.__menu_bar.exit_requested.connect(self.close)
        self.__menu_bar.update_check_requested.connect(self.__check_for_updates)
        self.__menu_bar.docs_requested.connect(AppContext.get_app().open_documentation)
        self.__menu_bar.path_limit_fix_requested.connect(
            lambda: PathLimitFixer.disable_path_limit(AppContext.get_app().res_path)
        )
        self.__menu_bar.about_requested.connect(self.__show_about)
        self.__menu_bar.about_qt_requested.connect(self.__show_about_qt)

    def __init_tab_widget(self) -> None:
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("root")
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.South)
        self.tab_widget.tabBar().setDocumentMode(True)
        self.setCentralWidget(self.tab_widget)

        self.mainpage_widget = MainPageWidget(
            self.cache,
            self.database,
            self.app_config,
            self.user_config,
            self.masterlist,
            self.mod_instance,
            self.scanner,
            self.provider,
            self.download_manager,
            self.state_service,
            self.nxm_listener,
        )
        self.tab_widget.addTab(self.mainpage_widget, self.tr("Modlist"))

        self.translation_editor = EditorPage(
            self.database,
            self.app_config,
            self.user_config,
            self.translator_config,
            self.translator,
        )
        self.tab_widget.addTab(self.translation_editor, self.tr("Translation Editor"))
        self.tab_widget.setTabEnabled(1, False)

    def __init_shortcuts(self) -> None:
        self.__refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.__refresh_shortcut.activated.connect(self.refresh)

    def __init_status_bar(self) -> None:
        self.__status_bar = StatusBar(self.logger, self.provider)
        self.setStatusBar(self.__status_bar)

    @override
    def update(self) -> None:  # type: ignore
        """
        Updates the displayed tabs for main page and translation editor.
        """

        editor_enabled_before: bool = self.tab_widget.isTabEnabled(1)

        self.tab_widget.setTabEnabled(1, len(self.translation_editor.tabs) > 0)

        if self.tab_widget.isTabEnabled(1) != editor_enabled_before:
            if self.tab_widget.isTabEnabled(1):
                self.tab_widget.setCurrentIndex(1)
            else:
                self.tab_widget.setCurrentIndex(0)

    def refresh(self) -> None:
        self.refresh_signal.emit()

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        confirmation: bool = True

        # TODO: Move this to the translation editor
        if hasattr(self, "translation_editor"):
            if any(tab.changes_pending for tab in self.translation_editor.tabs):
                message_box = QMessageBox(self)
                message_box.setWindowTitle(self.tr("Exit?"))
                message_box.setText(
                    self.tr(
                        "Are you sure you want to exit? There are still unsaved "
                        "translations open in the editor. All unsaved changes will be lost!"
                    )
                )
                message_box.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
                )
                message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
                message_box.button(QMessageBox.StandardButton.Yes).setText(
                    self.tr("Continue")
                )
                message_box.button(QMessageBox.StandardButton.Cancel).setText(
                    self.tr("Cancel")
                )

                if message_box.exec() != QMessageBox.StandardButton.Yes:
                    confirmation = False

        if confirmation:
            super().closeEvent(event)
        else:
            event.ignore()

    def __open_settings(self) -> None:
        SettingsDialog(
            self.cache,
            self.app_config,
            self.user_config,
            self.translator_config,
            self,
        ).show()

    def __check_for_updates(self) -> None:
        upd = Updater(AppContext.get_app().APP_VERSION)
        if upd.update_available():
            upd.run()
        else:
            messagebox = QMessageBox(self)
            messagebox.setWindowTitle(self.tr("No Updates Available"))
            messagebox.setText(self.tr("There are no updates available."))
            messagebox.setTextFormat(Qt.TextFormat.RichText)
            messagebox.setIcon(QMessageBox.Icon.Information)
            messagebox.exec()

    def __show_about(self) -> None:
        AboutDialog(self).exec()

    def __show_about_qt(self) -> None:
        QMessageBox.aboutQt(self, self.tr("About Qt"))
