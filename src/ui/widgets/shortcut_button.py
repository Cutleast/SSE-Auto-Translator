"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QWidget


class ShortcutButton(QPushButton):
    """
    Adapted QPushButton that automatically displays set shortcuts.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(7, 0, 7, 0)
        self.setLayout(hlayout)

        self.__icon_label = QLabel()
        if not self.icon().isNull():
            self.__icon_label.setPixmap(self.icon().pixmap(self.iconSize()))
        else:
            self.__icon_label.hide()
        hlayout.addWidget(self.__icon_label)

        self.__label = QLabel(self.text())
        hlayout.addWidget(self.__label)

        self.__shortcut_label = QLabel()
        hlayout.addWidget(self.__shortcut_label)

        # Clear original icon and text to avoid duplicates
        super().setIcon(QIcon())
        super().setText("")

        # Set minimum width
        self.updateSizeHint()

    def updateSizeHint(self):
        padding = 20

        label_width = self.__label.sizeHint().width()
        shortcut_width = self.__shortcut_label.sizeHint().width()
        icon_width = (
            (self.__icon_label.sizeHint().width() + 10)
            if not self.__icon_label.isHidden()
            else 0
        )
        combined_width = icon_width + label_width + shortcut_width + padding

        self.setMinimumWidth(combined_width)

    def setShortcut(self, shortcut):
        super().setShortcut(shortcut)

        key = self.shortcut().toString()
        if key:
            self.__shortcut_label.setText(f"({key})")
            self.__shortcut_label.show()
        else:
            self.__shortcut_label.hide()

        self.updateSizeHint()

    def setText(self, text: str):
        self.__label.setText(text)

        self.updateSizeHint()

    def setIcon(self, icon: QIcon | QPixmap):
        self.__icon_label.setPixmap(icon.pixmap(self.iconSize()))
        self.__icon_label.show()

        self.updateSizeHint()


if __name__ == "__main__":
    import qtawesome as qta

    app = QApplication()

    widget = QWidget()
    hlayout = QHBoxLayout()
    widget.setLayout(hlayout)

    left_button = ShortcutButton(
        qta.icon("fa5s.chevron-left", color="#000000"), "Click Me"
    )
    left_button.setShortcut(QKeySequence("Alt+N"))
    left_button.clicked.connect(
        lambda: (
            left_button.setText("Button clicked!"),
            left_button.setIcon(qta.icon("fa5s.check", color="#000000")),
        )
    )
    hlayout.addWidget(left_button)

    hlayout.addStretch()
    # hlayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

    right_button = ShortcutButton(
        qta.icon("fa5s.chevron-right", color="#000000"), "Click Me"
    )
    right_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    right_button.setShortcut(QKeySequence("Alt+M"))
    right_button.clicked.connect(
        lambda: (
            right_button.setText("Button clicked!"),
            right_button.setIcon(qta.icon("fa5s.check", color="#000000")),
        )
    )
    hlayout.addWidget(right_button)

    widget.show()

    app.exec()
