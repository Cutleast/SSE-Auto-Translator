"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import pyperclip
import qtawesome as qta
import qtpy.QtWidgets as qtw


class PasteLineEdit(qtw.QLineEdit):
    """
    LineEdit with paste button.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.paste_action = self.addAction(
            qta.icon("fa5s.paste", color="#ffffff"),
            qtw.QLineEdit.ActionPosition.TrailingPosition,
        )
        self.paste_action.triggered.connect(
            lambda: (
                self.setText(pyperclip.paste()) if pyperclip.paste().strip() else None
            )
        )


if __name__ == "__main__":
    app = qtw.QApplication()

    lineedit = PasteLineEdit()
    lineedit.show()

    app.exec()
