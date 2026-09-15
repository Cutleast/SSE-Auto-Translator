"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QWidget


class ShortcutButton(QPushButton):
    """
    Push button that displays its shortcut next to its text.
    """

    __icon: QIcon
    __icon_label: QLabel
    __text_label: QLabel
    __shortcut_label: QLabel
    __layout: QHBoxLayout

    def __init__(
        self,
        text: str = "",
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            text (str, optional): Text displayed by the button. Defaults to "".
            icon (Optional[QIcon], optional):
                Optional icon displayed by the button. Defaults to None.
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__icon = icon or QIcon()

        self.__layout = QHBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)

        self.__icon_label = QLabel()
        self.__icon_label.setObjectName("icon_label")
        self.__layout.addWidget(self.__icon_label)

        self.__text_label = QLabel(text)
        self.__text_label.setObjectName("text_label")
        self.__layout.addWidget(self.__text_label)

        self.__shortcut_label = QLabel()
        self.__shortcut_label.setObjectName("shortcut_label")
        self.__shortcut_label.hide()
        self.__layout.addWidget(self.__shortcut_label)

        self.__update_icon()

    @override
    def sizeHint(self) -> QSize:
        layout_size: QSize = self.__layout.sizeHint()
        button_size: QSize = super().sizeHint()

        return QSize(
            max(layout_size.width(), button_size.width()),
            max(layout_size.height(), button_size.height()),
        )

    @override
    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    @override
    def setText(self, text: str) -> None:
        self.__text_label.setText(text)

        self.updateGeometry()

    @override
    def text(self) -> str:
        return self.__text_label.text()

    @override
    def setIcon(self, icon: QIcon | QPixmap) -> None:
        self.__icon = QIcon(icon) if isinstance(icon, QPixmap) else icon
        self.__update_icon()

    @override
    def icon(self) -> QIcon:
        return self.__icon

    @override
    def setIconSize(self, size: QSize) -> None:
        super().setIconSize(size)

        self.__update_icon()

    @override
    def setShortcut(self, shortcut: QKeySequence) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().setShortcut(shortcut)

        text: str = shortcut.toString(QKeySequence.SequenceFormat.NativeText)

        self.__shortcut_label.setText(text)
        self.__shortcut_label.setVisible(bool(text))

        self.updateGeometry()

    def __update_icon(self) -> None:
        if self.__icon.isNull():
            self.__icon_label.clear()
            self.__icon_label.hide()
        else:
            self.__icon_label.setPixmap(self.__icon.pixmap(self.iconSize()))
            self.__icon_label.show()

        self.setProperty("has_icon", not self.__icon.isNull())
        self.updateGeometry()


if __name__ == "__main__":
    import qtawesome as qta

    app = QApplication()

    widget = QWidget()
    hlayout = QHBoxLayout()
    widget.setLayout(hlayout)

    left_button = ShortcutButton(
        text="Click Me",
        icon=qta.icon("mdi6.chevron-left", color="#000000"),
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

    right_button = ShortcutButton(
        text="Click Me",
        icon=qta.icon("mdi6.chevron-right", color="#000000"),
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
