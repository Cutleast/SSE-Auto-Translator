"""
Copyright (c) Cutleast
"""

from typing import Optional

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.config.exceptions import ConfigValidationError
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.widgets.divider import Divider
from cutleast_core_lib.ui.widgets.tab_widget import TabWidget
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.config.app_config import AppConfig
from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from ui.utilities.icon_provider import IconProvider

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

    _changes_pending: bool = False
    """Whether there are unsaved changes."""

    _restart_required: bool = False
    """Whether a restart is required for changes to take effect."""

    _theme_update_required: bool = False
    """Whether a theme update is required for changes to take effect."""

    __cache: Cache
    __app_config: AppConfig
    __user_config: UserConfig
    __translator_config: TranslatorConfig

    __vlayout: QVBoxLayout
    __tab_widget: TabWidget

    __app_settings: AppSettings
    __user_settings: UserSettings
    __translator_settings: TranslatorSettings

    __status_label: QLabel
    __save_button: QPushButton

    def __init__(
        self,
        cache: Cache,
        app_config: AppConfig,
        user_config: UserConfig,
        translator_config: TranslatorConfig,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            cache (Cache): The application cache.
            app_config (AppConfig): The application configuration.
            user_config (UserConfig): The user configuration.
            translator_config (TranslatorConfig): The translator configuration.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__cache = cache
        self.__app_config = app_config
        self.__user_config = user_config
        self.__translator_config = translator_config

        self.__init_ui()

        self.__save_button.clicked.connect(self._save)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_settings()

        divider = Divider()
        self.__vlayout.addWidget(divider)

        self.__init_footer()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.__vlayout.addLayout(hlayout)

        icon_label = QLabel()
        IconProvider.bind_qta_icon(
            icon_label,
            lambda icon: icon_label.setPixmap(
                icon.pixmap(
                    ThemeManager.get().theme.metrics.icon_l,
                    ThemeManager.get().theme.metrics.icon_l,
                )
            ),
            "mdi6.cog",
        )
        hlayout.addWidget(icon_label)

        title_label = QLabel(self.tr("Settings"))
        title_label.setProperty("title", True)
        hlayout.addWidget(title_label)

        hlayout.addStretch()

        restart_hint_label = QLabel(
            self.tr("Settings marked with * require a restart to take effect.")
        )
        restart_hint_label.setProperty("secondary", True)
        self.__vlayout.addWidget(restart_hint_label)

    def __init_settings(self) -> None:
        self.__tab_widget = TabWidget()
        self.__vlayout.addWidget(self.__tab_widget)

        self.__app_settings = AppSettings(self.__app_config, self.__cache)
        self.__app_settings.changed_signal.connect(self._on_change)
        self.__app_settings.restart_required_signal.connect(self._on_restart_required)
        self.__app_settings.theme_update_required_signal.connect(
            self._on_theme_update_required
        )
        self.__tab_widget.addTab(self.__app_settings, self.tr("App Settings"))

        self.__user_settings = UserSettings(self.__user_config)
        self.__user_settings.changed_signal.connect(self._on_change)
        self.__user_settings.restart_required_signal.connect(self._on_restart_required)
        self.__tab_widget.addTab(self.__user_settings, self.tr("User Settings"))

        self.__translator_settings = TranslatorSettings(self.__translator_config)
        self.__translator_settings.changed_signal.connect(self._on_change)
        self.__translator_settings.restart_required_signal.connect(
            self._on_restart_required
        )
        self.__tab_widget.addTab(
            self.__translator_settings, self.tr("Translator Settings")
        )

    def _on_change(self) -> None:
        self._changes_pending = True

        try:
            self.__app_settings.validate()
            self.__user_settings.validate()
            self.__translator_settings.validate()
        except ConfigValidationError as ex:
            self.__status_label.setText(str(ex))
            self.__save_button.setEnabled(False)
        else:
            self.__status_label.clear()
            self.__save_button.setEnabled(True)

    def _on_restart_required(self) -> None:
        self._restart_required = True

    def _on_theme_update_required(self) -> None:
        self._theme_update_required = True

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        hlayout.addStretch()

        self.__status_label = QLabel()
        self.__status_label.setProperty("state", "error")
        hlayout.addWidget(self.__status_label)

        self.__save_button = QPushButton(self.tr("Save"))
        self.__save_button.setDefault(True)
        self.__save_button.setDisabled(True)
        hlayout.addWidget(self.__save_button)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.cancel_signal.emit)
        hlayout.addWidget(cancel_button)

    def _save(self) -> None:
        self.__app_settings.apply(self.__app_config)
        self.__user_settings.apply(self.__user_config)
        self.__translator_settings.apply(self.__translator_config)

        self.__app_config.save()
        self.__user_config.save()
        self.__translator_config.save()

        if self._theme_update_required:
            ThemeManager.get().set_primary_color(
                self.__app_config.accent_color, apply=False
            )
            ThemeManager.get().set_ui_mode(self.__app_config.ui_mode)

        self._changes_pending = False
        self.save_signal.emit()

        if self._restart_required:
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
            choice: int = messagebox.exec()

            if choice == QMessageBox.StandardButton.Yes:
                from app import App

                App.get().restart_application()
