"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from cutleast_core_lib.core.cache.cache import Cache
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMessageBox, QWidget

from core.config.app_config import AppConfig
from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from ui.utilities.theme_manager import ThemeManager

from .settings_widget import SettingsWidget


class SettingsDialog(SettingsWidget):
    """
    Class for settings dialog.
    """

    def __init__(
        self,
        app_config: AppConfig,
        user_config: UserConfig,
        translator_config: TranslatorConfig,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(
            Cache.get(), app_config, user_config, translator_config, parent
        )

        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowTitle(self.tr("Settings"))
        self.setObjectName("root")
        self.setMinimumSize(1000, 650)
        self.resize(1000, 650)

        self.cancel_signal.connect(self.close)

    @override
    def _on_change(self) -> None:
        super()._on_change()

        self.setWindowTitle(self.tr("Settings") + "*")

    @override
    def _save(self) -> None:
        super()._save()

        self.close()

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Cancels dialog and asks for confirmation if changes are pending.
        """

        if self.changes_pending:
            message_box = QMessageBox(self)
            message_box.setWindowTitle(self.tr("Cancel"))
            message_box.setText(
                self.tr("Are you sure you want to cancel? All changes will be lost.")
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.No)
            message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))

            # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
            message_box.setStyleSheet(ThemeManager.get_stylesheet() or "")

            if message_box.exec() == QMessageBox.StandardButton.Yes:
                event.accept()
            elif event:
                event.ignore()
        else:
            event.accept()
