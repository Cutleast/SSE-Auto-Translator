"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Any

import qtawesome as qta
from PySide6.QtWidgets import QApplication, QLineEdit


class KeyEntry(QLineEdit):
    """
    LineEdit for passwords or keys, has a toggle visibility button.
    """

    __is_visible = False

    def __init__(self, *args: Any, **kwargs: dict[str, Any]):
        super().__init__(*args, **kwargs)  # type: ignore[call-overload]

        self.setEchoMode(QLineEdit.EchoMode.Password)

        self.toggle_visibility_action = self.addAction(
            qta.icon("mdi6.eye", color="#ffffff"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.toggle_visibility_action.triggered.connect(self.toggle_visibility)

    def toggle_visibility(self) -> None:
        self.__is_visible = not self.__is_visible

        if self.__is_visible:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_visibility_action.setIcon(
                qta.icon("mdi6.eye-off", color="#ffffff")
            )
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_visibility_action.setIcon(qta.icon("mdi6.eye", color="#ffffff"))


if __name__ == "__main__":
    app = QApplication()

    lineedit = KeyEntry()
    lineedit.show()

    app.exec()
