"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional, override

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTabWidget

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

    tab_widget: QTabWidget
    mainpage_widget: MainPageWidget
    translation_editor: EditorPage

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

        self.close_event = self.closeEvent
        self.closeEvent = lambda event: self.exit(event)

        self.__init_ui()
        self.__init_shortcuts()

    def __init_ui(self) -> None:
        self.setMenuBar(MenuBar())
        self.setStatusBar(StatusBar(self.logger, self.provider))

        self.resize(1500, 800)
        self.setStyleSheet(AppContext.get_app().styleSheet())

        self.__init_tab_widget()

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

    def exit(self, event: Optional[QCloseEvent] = None) -> None:
        confirmation = True

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

                choice = message_box.exec()

                if choice != QMessageBox.StandardButton.Yes:
                    confirmation = False

        if confirmation:
            if event:
                self.close_event(event)
            else:
                self.destroy()

            QApplication.exit()

        elif event:
            event.ignore()
