"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import pyperclip
import qtpy.QtWidgets as qtw
import qtawesome as qta


class CopyLineEdit(qtw.QLineEdit):
    """
    LineEdit with copy button.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.copy_action = self.addAction(
            qta.icon("fa5s.copy", color="#ffffff"),
            qtw.QLineEdit.ActionPosition.TrailingPosition
        )
        # self.paste_action.setIconVisibleInMenu(True)
        self.copy_action.triggered.connect(
            lambda: (
                pyperclip.copy(self.text()) if self.text().strip() else None
            )
        )


if __name__ == "__main__":
    app = qtw.QApplication()

    lineedit = CopyLineEdit()
    lineedit.show()

    app.exec()
