"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtWidgets as qtw
import qtawesome as qta


class KeyEntry(qtw.QLineEdit):
    """
    LineEdit for passwords or keys, has a toggle visibility button.
    """

    __is_visible = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setEchoMode(qtw.QLineEdit.EchoMode.Password)

        self.toggle_visibility_action = self.addAction(
            qta.icon("mdi6.eye", color="#ffffff"),
            qtw.QLineEdit.ActionPosition.TrailingPosition
        )
        self.toggle_visibility_action.triggered.connect(self.toggle_visibility)
    
    def toggle_visibility(self):
        self.__is_visible = not self.__is_visible

        if self.__is_visible:
            self.setEchoMode(qtw.QLineEdit.EchoMode.Normal)
            self.toggle_visibility_action.setIcon(
                qta.icon("mdi6.eye-off", color="#ffffff")
            )
        else:
            self.setEchoMode(qtw.QLineEdit.EchoMode.Password)
            self.toggle_visibility_action.setIcon(
                qta.icon("mdi6.eye", color="#ffffff")
            )


if __name__ == "__main__":
    app = qtw.QApplication()

    lineedit = KeyEntry()
    lineedit.show()

    app.exec()
