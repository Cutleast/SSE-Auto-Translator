"""
Copyright (c) Cutleast
"""

import logging
import webbrowser
from typing import override

from cutleast_core_lib.core.utilities.path_limit_fixer import PathLimitFixer
from cutleast_core_lib.core.utilities.updater import Updater
from cutleast_core_lib.ui.widgets.about_dialog import AboutDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from core.config.app_config import AppConfig
from core.downloader.download_manager import DownloadManager
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.translation_provider.provider import Provider
from core.translator_api.translator import Translator
from core.user_data.user_data import UserData
from core.utilities.constants import DOCS_URL
from core.utilities.licenses import LICENSES
from ui.settings.settings_dialog import SettingsDialog
from ui.utilities.theme_manager import ThemeManager

from .main_page.main_page import MainPageWidget
from .menubar import MenuBar
from .statusbar import StatusBar
from .toast_notifier import ToastNotifier
from .translation_editor.editor_page import EditorPage


class MainWindow(QMainWindow):
    """
    Class for main application window.
    """

    log: logging.Logger = logging.getLogger("App")

    app_config: AppConfig
    user_data: UserData
    translator: Translator
    scanner: Scanner
    provider: Provider
    download_manager: DownloadManager
    state_service: StateService

    __refresh_shortcut: QShortcut

    __menu_bar: MenuBar
    tab_widget: QTabWidget
    mainpage_widget: MainPageWidget
    translation_editor: EditorPage
    toast_notifier: ToastNotifier
    __status_bar: StatusBar

    refresh_signal = Signal()
    """
    This signal is emitted when the refresh shortcut is activated.
    """

    def initialize(
        self,
        app_config: AppConfig,
        user_data: UserData,
        translator: Translator,
        scanner: Scanner,
        provider: Provider,
        download_manager: DownloadManager,
        state_service: StateService,
    ) -> None:
        """
        Initializes the main window.

        Args:
            app_config (AppConfig): App configuration.
            user_data (UserData): User data.
            translator (Translator): API translator.
            scanner (Scanner): Scanner.
            provider (Provider): Translation provider.
            download_manager (DownloadManager): Download manager.
            state_service (StateService): State service.
        """

        self.app_config = app_config
        self.user_data = user_data
        self.translator = translator
        self.scanner = scanner
        self.provider = provider
        self.download_manager = download_manager
        self.state_service = state_service

        self.__init_ui()
        self.__init_shortcuts()
        self.__init_toast_notifier()

        self.translation_editor.tab_count_updated.connect(
            self.__on_editor_tab_count_change
        )
        self.mainpage_widget.edit_translation_requested.connect(
            self.translation_editor.open_translation
        )

    def __init_ui(self) -> None:
        self.__init_menu_bar()
        self.__init_tab_widget()
        self.__init_status_bar()

        self.resize(1500, 800)

    def __init_menu_bar(self) -> None:
        from app import App

        self.__menu_bar = MenuBar()
        self.setMenuBar(self.__menu_bar)

        self.__menu_bar.settings_requested.connect(self.__open_settings)
        self.__menu_bar.exit_requested.connect(self.close)
        self.__menu_bar.update_check_requested.connect(self.__check_for_updates)
        self.__menu_bar.docs_requested.connect(lambda: webbrowser.open(DOCS_URL))
        self.__menu_bar.path_limit_fix_requested.connect(
            lambda: PathLimitFixer.disable_path_limit(App.get().res_path)
        )
        self.__menu_bar.about_requested.connect(self.__show_about)
        self.__menu_bar.about_qt_requested.connect(self.__show_about_qt)

    def __init_tab_widget(self) -> None:
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("main_tab_widget")
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.South)
        self.tab_widget.tabBar().setDocumentMode(True)
        self.setCentralWidget(self.tab_widget)

        self.mainpage_widget = MainPageWidget(
            self.app_config,
            self.user_data,
            self.scanner,
            self.provider,
            self.download_manager,
            self.state_service,
        )
        self.tab_widget.addTab(self.mainpage_widget, self.tr("Modlist"))

        self.translation_editor = EditorPage(
            self.app_config, self.user_data, self.translator
        )
        self.tab_widget.addTab(self.translation_editor, self.tr("Translation Editor"))
        self.tab_widget.setTabEnabled(1, False)

    def __init_shortcuts(self) -> None:
        self.__refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.__refresh_shortcut.activated.connect(self.refresh)

    def __init_status_bar(self) -> None:
        self.__status_bar = StatusBar(self.provider)
        self.setStatusBar(self.__status_bar)

    def __init_toast_notifier(self) -> None:
        self.toast_notifier = ToastNotifier(self)
        self.toast_notifier.set_download_manager(self.download_manager)

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

                # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
                message_box.setStyleSheet(ThemeManager.get_stylesheet() or "")

                if message_box.exec() != QMessageBox.StandardButton.Yes:
                    confirmation = False

        if confirmation:
            super().closeEvent(event)
            self.mainpage_widget.save_state()
            self.__status_bar.close_log_window()
        else:
            event.ignore()

    def __open_settings(self) -> None:
        SettingsDialog(
            self.app_config,
            self.user_data.user_config,
            self.user_data.translator_config,
            self,
        ).show()

    def __check_for_updates(self) -> None:
        upd = Updater.get()
        if upd.is_update_available():
            upd.run()
        else:
            messagebox = QMessageBox(self)
            messagebox.setWindowTitle(self.tr("No Updates Available"))
            messagebox.setText(self.tr("There are no updates available."))
            messagebox.setTextFormat(Qt.TextFormat.RichText)
            messagebox.setIcon(QMessageBox.Icon.Information)
            messagebox.exec()

    def __show_about(self) -> None:
        from app import App

        text: str = self.tr(
            "Created by Cutleast (<a href='https://www.nexusmods.com/users/65733731'>"
            "NexusMods</a> | <a href='https://github.com/cutleast'>GitHub</a> "
            "| <a href='https://ko-fi.com/cutleast'>Ko-Fi</a>)<br><br>Icon by "
            "Wuerfelhusten (<a href='https://www.nexusmods.com/users/122160268'>"
            "NexusMods</a>)<br><br>Licensed under "
            "Attribution-NonCommercial-NoDerivatives 4.0 International"
        )

        # Add translator credit if available
        translator_info: str = self.tr("<<Put your translator information here.>>")
        if translator_info != "<<Put your translator information here.>>":
            text += translator_info

        AboutDialog(
            App.APP_NAME,
            App.APP_VERSION,
            App.windowIcon(),
            "Attribution-NonCommercial-NoDerivatives 4.0 International",
            licenses=LICENSES,
            text=text,
        ).exec()

    def __show_about_qt(self) -> None:
        QMessageBox.aboutQt(self, self.tr("About Qt"))

    def __on_editor_tab_count_change(self, new_tab_count: int) -> None:
        if new_tab_count > 0:
            self.tab_widget.setCurrentWidget(self.translation_editor)
        else:
            self.tab_widget.setCurrentWidget(self.mainpage_widget)

        self.tab_widget.setTabEnabled(1, new_tab_count > 0)
