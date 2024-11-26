"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import pyperclip as clipboard
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QWidget

from app import MainApp
from core.utilities import apply_dark_title_bar


class ErrorDialog(QMessageBox):
    """
    Custom error messagebox with short text
    and detailed text functionality.

    Parameters:
        parent: QWidget (parent window)
        app: MainApp (for localisation of buttons)
        title: str (window title)
        text: str (short message)
        details: str (will be displayed when details are shown)
        yesno: bool (determines if 'continue' and 'cancel' buttons are shown
        or only an 'ok' button)
    """

    def __init__(
        self,
        parent: QWidget,
        app: MainApp,
        title: str,
        text: str,
        details: str = "",
        yesno: bool = True,
    ):
        super().__init__(parent)
        self.app = app

        # Basic configuration
        self.setWindowTitle(title)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setText(text)
        apply_dark_title_bar(self)

        # Show 'continue' and 'cancel' button
        if yesno:
            self.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            self.button(QMessageBox.StandardButton.Yes).setText(
                self.app.loc.main._continue
            )
            self.button(QMessageBox.StandardButton.No).setText(
                self.app.loc.main.exit
            )

        # Only show 'ok' button
        else:
            self.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Add details button if details are given
        if details:
            self.details_button: QPushButton = self.addButton(
                self.app.loc.main.show_details, QMessageBox.ButtonRole.AcceptRole
            )
            self.details_button.setIcon(qta.icon("fa5s.chevron-down", color="#ffffff"))

            self.copy_button: QPushButton = self.addButton(
                "", QMessageBox.ButtonRole.YesRole
            )
            self.copy_button.setText("")
            self.copy_button.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
            self.copy_button.clicked.disconnect()
            self.copy_button.clicked.connect(lambda: clipboard.copy(details))

            self._details = False
            label: QLabel = self.findChild(QLabel)

            def toggle_details():
                # toggle details
                if not self._details:
                    self._details = True
                    self.details_button.setText(self.app.loc.main.hide_details)
                    self.details_button.setIcon(
                        qta.icon("fa5s.chevron-up", color="#ffffff")
                    )
                    self.setInformativeText(
                        f"<font><p style='font-family: Consolas;font-size: 12px'>{details}</p>"
                    )
                    label.setTextInteractionFlags(
                        Qt.TextInteractionFlag.TextSelectableByMouse
                    )
                    label.setCursor(Qt.CursorShape.IBeamCursor)
                else:
                    self._details = False
                    self.details_button.setText(self.app.loc.main.show_details)
                    self.details_button.setIcon(
                        qta.icon("fa5s.chevron-down", color="#ffffff")
                    )
                    self.setInformativeText("")
                    label.setTextInteractionFlags(
                        Qt.TextInteractionFlag.NoTextInteraction
                    )
                    label.setCursor(Qt.CursorShape.ArrowCursor)

                # update messagebox size
                self.adjustSize()

            self.details_button.clicked.disconnect()
            self.details_button.clicked.connect(toggle_details)
