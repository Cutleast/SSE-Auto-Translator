"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Any

from PySide6.QtWidgets import QApplication, QLineEdit

from ui.utilities.icon_provider import IconProvider


class PasteLineEdit(QLineEdit):
    """
    LineEdit with paste button.
    """

    def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

        self.paste_action = self.addAction(
            IconProvider.get_qta_icon("fa5s.paste"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.paste_action.triggered.connect(
            lambda: (
                self.setText(QApplication.clipboard().text())
                if QApplication.clipboard().text().strip()
                else None
            )
        )


if __name__ == "__main__":
    app = QApplication()

    lineedit = PasteLineEdit()
    lineedit.show()

    app.exec()
