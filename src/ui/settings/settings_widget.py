"""
Copyright (c) Cutleast
"""

from typing import Optional

from cutleast_core_lib.core.cache.cache import Cache
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.config.app_config import AppConfig
from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig

from .app_settings import AppSettings
from .translator_settings import TranslatorSettings
from .user_settings import UserSettings


class SettingsWidget(QWidget):
    """
    Widget for configuring application settings.
    """

    cancel_signal = Signal()
    """This signal is emitted when the cancel button is clicked."""

    save_signal = Signal()
    """This signal is emitted when the save button is clicked."""

    changes_pending: bool = False
    """Whether there are unsaved changes."""

    restart_required: bool = False
    """Whether a restart is required for changes to take effect."""

    cache: Cache
    app_config: AppConfig
    user_config: UserConfig
    translator_config: TranslatorConfig

    __vlayout: QVBoxLayout
    __tab_widget: QTabWidget

    __app_settings: AppSettings
    __user_settings: UserSettings
    __translator_settings: TranslatorSettings

    __save_button: QPushButton

    def __init__(
        self,
        cache: Cache,
        app_config: AppConfig,
        user_config: UserConfig,
        translator_config: TranslatorConfig,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.cache = cache
        self.app_config = app_config
        self.user_config = user_config
        self.translator_config = translator_config

        self.__init_ui()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_settings()
        self.__init_footer()

    def __init_header(self) -> None:
        title_label = QLabel(self.tr("Settings"))
        title_label.setObjectName("h1")
        self.__vlayout.addWidget(title_label)
        self.__vlayout.addSpacing(15)

        restart_hint_label = QLabel(
            self.tr("Settings marked with * require a restart to take effect.")
        )
        self.__vlayout.addWidget(restart_hint_label)
        self.__vlayout.addSpacing(15)

    def __init_settings(self) -> None:
        self.__tab_widget = QTabWidget()
        self.__tab_widget.tabBar().setExpanding(True)
        self.__tab_widget.tabBar().setDocumentMode(True)
        self.__vlayout.addWidget(self.__tab_widget)

        self.__app_settings = AppSettings(self.app_config, self.cache)
        self.__app_settings.changed_signal.connect(self._on_change)
        self.__app_settings.restart_required_signal.connect(self._on_restart_required)
        self.__tab_widget.addTab(self.__app_settings, self.tr("App Settings"))

        self.__user_settings = UserSettings(self.user_config)
        self.__user_settings.changed_signal.connect(self._on_change)
        self.__user_settings.restart_required_signal.connect(self._on_restart_required)
        self.__tab_widget.addTab(self.__user_settings, self.tr("User Settings"))

        self.__translator_settings = TranslatorSettings(self.translator_config)
        self.__translator_settings.changed_signal.connect(self._on_change)
        self.__translator_settings.restart_required_signal.connect(
            self._on_restart_required
        )
        self.__tab_widget.addTab(
            self.__translator_settings, self.tr("Translator Settings")
        )

    def _on_change(self) -> None:
        self.changes_pending = True
        self.__save_button.setEnabled(True)

    def _on_restart_required(self) -> None:
        self.restart_required = True

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.cancel_signal.emit)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        self.__save_button = QPushButton(self.tr("Save"))
        self.__save_button.setDefault(True)
        self.__save_button.setDisabled(True)
        self.__save_button.clicked.connect(self.__save)
        hlayout.addWidget(self.__save_button)

    def __save(self) -> None:
        self.__app_settings.apply(self.app_config)
        self.__user_settings.apply(self.user_config)
        self.__translator_settings.apply(self.translator_config)

        self.app_config.save()
        self.user_config.save()
        self.translator_config.save()

        self.save_signal.emit()

        if self.restart_required:
            messagebox = QMessageBox()
            messagebox.setWindowTitle(self.tr("Restart required"))
            messagebox.setText(
                self.tr(
                    "SSE-AT must be restarted for the changes to take effect! Restart now?"
                )
            )
            messagebox.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            messagebox.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            messagebox.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
            choice = messagebox.exec()

            if choice == QMessageBox.StandardButton.Yes:
                from app import App

                App.get().restart_application()
