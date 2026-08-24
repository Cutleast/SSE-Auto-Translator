"""
Copyright (c) Cutleast
"""

import webbrowser
from typing import override

from cutleast_core_lib.core.utilities.path_limit_fixer import PathLimitFixer
from cutleast_core_lib.core.utilities.updater import Updater
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.utilities.window_manager import WindowManager
from cutleast_core_lib.ui.widgets.about_dialog import AboutDialog
from cutleast_core_lib.ui.widgets.tab_widget import TabWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QShortcut
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from core.config.app_config import AppConfig
from core.downloader.download_manager import DownloadManager
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.translation_provider.provider import TranslationProvider
from core.translator.service import TranslatorService
from core.user_data.user_data import UserData
from core.utilities.constants import DOCS_URL
from core.utilities.licenses import LICENSES
from ui.settings.settings_dialog import SettingsDialog

from .main_page.main_page import MainPageWidget
from .menubar import MenuBar
from .statusbar import StatusBar
from .toast_notifier import ToastNotifier
from .translation_editor.editor_page import EditorPage


class MainWindow(QMainWindow):
    """
    Class for main application window.
    """

    __app_config: AppConfig
    __user_data: UserData
    __translator_service: TranslatorService
    __scanner: Scanner
    __provider: TranslationProvider
    __download_manager: DownloadManager
    __state_service: StateService

    __refresh_shortcut: QShortcut

    __menu_bar: MenuBar
    __tab_widget: TabWidget
    __mainpage_widget: MainPageWidget
    __translation_editor: EditorPage
    __toast_notifier: ToastNotifier
    __status_bar: StatusBar

    def initialize(
        self,
        app_config: AppConfig,
        user_data: UserData,
        translator_service: TranslatorService,
        scanner: Scanner,
        provider: TranslationProvider,
        download_manager: DownloadManager,
        state_service: StateService,
    ) -> None:
        """
        Args:
            app_config (AppConfig): App configuration.
            user_data (UserData): User data.
            translator_service (TranslatorService): API translator service.
            scanner (Scanner): Scanner.
            provider (TranslationProvider): Translation provider.
            download_manager (DownloadManager): Download manager.
            state_service (StateService): State service.
        """

        self.__app_config = app_config
        self.__user_data = user_data
        self.__translator_service = translator_service
        self.__scanner = scanner
        self.__provider = provider
        self.__download_manager = download_manager
        self.__state_service = state_service

        self.__init_ui()
        self.__init_toast_notifier()

        self.__translation_editor.tab_count_updated.connect(
            self.__on_editor_tab_count_change
        )
        self.__mainpage_widget.edit_translation_requested.connect(
            self.__translation_editor.open_translation
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
        self.__tab_widget = TabWidget()
        self.__tab_widget.setTabPosition(QTabWidget.TabPosition.South)
        self.__tab_widget.setSpacing(0)
        self.setCentralWidget(self.__tab_widget)

        self.__mainpage_widget = MainPageWidget(
            app_config=self.__app_config,
            user_data=self.__user_data,
            scanner=self.__scanner,
            provider=self.__provider,
            download_manager=self.__download_manager,
            state_service=self.__state_service,
        )
        self.__tab_widget.addTab(self.__mainpage_widget, self.tr("Modlist"))

        self.__translation_editor = EditorPage(
            self.__app_config, self.__user_data, self.__translator_service
        )
        self.__tab_widget.addTab(
            self.__translation_editor, self.tr("Translation Editor")
        )
        self.__tab_widget.setTabEnabled(1, False)

        WidgetStateManager.get().register_state("editor_page", self.__translation_editor)

    def __init_status_bar(self) -> None:
        self.__status_bar = StatusBar(self.__provider)
        self.setStatusBar(self.__status_bar)

    def __init_toast_notifier(self) -> None:
        self.__toast_notifier = ToastNotifier(self)
        self.__toast_notifier.set_download_manager(self.__download_manager)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        confirmation: bool = True

        # TODO: Move this to the translation editor
        if hasattr(self, "translation_editor") and any(
            tab.changes_pending for tab in self.__translation_editor.tabs
        ):
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
            ThemeManager.update_widget_styles(message_box)

            if message_box.exec() != QMessageBox.StandardButton.Yes:
                confirmation = False

        if confirmation:
            super().closeEvent(event)
            self.__mainpage_widget.save_state()

            WindowManager.get().close_all()
        else:
            event.ignore()

    def __open_settings(self) -> None:
        SettingsDialog(
            app_config=self.__app_config,
            user_config=self.__user_data.user_config,
            translator_config=self.__user_data.translator_config,
            parent=self,
        ).show()

    def __check_for_updates(self) -> None:
        upd: Updater = Updater.get()
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
            app_name=App.APP_NAME,
            app_version=App.APP_VERSION,
            app_icon=App.windowIcon(),
            app_license="Attribution-NonCommercial-NoDerivatives 4.0 International",
            licenses=LICENSES,
            text=text,
        ).exec()

    def __show_about_qt(self) -> None:
        QMessageBox.aboutQt(self, self.tr("About Qt"))

    def __on_editor_tab_count_change(self, new_tab_count: int) -> None:
        if new_tab_count > 0:
            self.__tab_widget.setCurrentWidget(self.__translation_editor)
        else:
            self.__tab_widget.setCurrentWidget(self.__mainpage_widget)

        self.__tab_widget.setTabEnabled(1, new_tab_count > 0)
