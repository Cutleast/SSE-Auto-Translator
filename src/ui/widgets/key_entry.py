"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Any

from PySide6.QtWidgets import QApplication, QLineEdit

from ui.utilities.icon_provider import IconProvider


class KeyEntry(QLineEdit):
    """
    LineEdit for passwords or keys, has a toggle visibility button.
    """

    __is_visible: bool = False

    def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

        self.setEchoMode(QLineEdit.EchoMode.Password)

        self.toggle_visibility_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.eye"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.toggle_visibility_action.triggered.connect(self.toggle_visibility)

    def toggle_visibility(self) -> None:
        self.__is_visible = not self.__is_visible

        if self.__is_visible:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_visibility_action.setIcon(
                IconProvider.get_qta_icon("mdi6.eye-off")
            )
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_visibility_action.setIcon(IconProvider.get_qta_icon("mdi6.eye"))


if __name__ == "__main__":
    app = QApplication()

    lineedit = KeyEntry()
    lineedit.show()

    app.exec()
