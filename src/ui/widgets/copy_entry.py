"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import pyperclip
import qtawesome as qta
from PySide6.QtWidgets import QApplication, QLineEdit


class CopyLineEdit(QLineEdit):
    """
    LineEdit with copy button.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.copy_action = self.addAction(
            qta.icon("fa5s.copy", color="#ffffff"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.copy_action.triggered.connect(
            lambda: (pyperclip.copy(self.text()) if self.text().strip() else None)
        )


if __name__ == "__main__":
    app = QApplication()

    lineedit = CopyLineEdit()
    lineedit.show()

    app.exec()
