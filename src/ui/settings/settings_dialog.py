"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMessageBox, QWidget

from .settings_widget import SettingsWidget


class SettingsDialog(SettingsWidget):
    """
    Class for settings dialog.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowTitle(self.tr("Settings"))
        self.setObjectName("root")
        self.setMinimumSize(1000, 650)
        self.resize(1000, 650)

        self.cancel_signal.connect(self.close)
        self.save_signal.connect(self.__save)

    @override
    def _on_change(self) -> None:
        super()._on_change()

        self.setWindowTitle(self.tr("Settings") + "*")

    def __save(self) -> None:
        self.changes_pending = False
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
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            message_box.button(QMessageBox.StandardButton.No).setObjectName(
                "accent_button"
            )
            message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
            choice = message_box.exec()

            if choice == QMessageBox.StandardButton.Yes:
                event.accept()
            elif event:
                event.ignore()
        else:
            event.accept()
