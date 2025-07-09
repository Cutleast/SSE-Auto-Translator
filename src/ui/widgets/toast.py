"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional, override

from PySide6.QtCore import (
    QAbstractAnimation,
    QByteArray,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Toast(QWidget):
    """
    A simple animated toast notification.
    """

    def __init__(
        self,
        text: str,
        duration: int = 2,
        opacity: float = 1,
        anim_duration: float = 0.2,
        pos: Optional[QPoint] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.__parent = parent
        if self.__parent is not None:
            self.__parent.installEventFilter(self)
        self.installEventFilter(self)
        self.__timer = QTimer(self)
        self.__timer.setInterval(int((duration + anim_duration) * 1000))
        self.__timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.__timer.timeout.connect(self.hide)

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.Popup, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.__animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.__animation.setDuration(int(anim_duration * 1000))
        self.__animation.setStartValue(0.0)
        self.__animation.setEndValue(opacity)
        self.__animation.valueChanged.connect(self.__set_opacity)

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlayout)
        self.__frame = QFrame()
        vlayout.addWidget(self.__frame)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.__frame.setLayout(hlayout)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hlayout.addWidget(self.icon_label)

        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.text_label.setWordWrap(True)
        hlayout.addWidget(self.text_label)

        self.set_position(pos)
        self.__update_size()

        super().hide()

    def __set_opacity(self, opacity: float) -> None:
        self.setWindowOpacity(opacity)

        if opacity == 0.0:
            super().hide()

    @override
    def hide(self) -> None:
        self.__animation.setDirection(QAbstractAnimation.Direction.Backward)
        self.__animation.start()

        if self.__timer.isActive():
            self.__timer.stop()

    def set_position(self, pos: Optional[QPoint] = None) -> None:
        # If pos is None, set pos to center of lower third of screen
        if pos is None:
            scr = QApplication.primaryScreen().availableGeometry()
            pos = scr.center()
            pos.setY(scr.height() - 50)

        rect = self.geometry()
        rect.moveCenter(pos)
        self.setGeometry(rect)

    @override
    def show(self) -> None:
        if self.__timer.isActive():
            self.__timer.stop()
            super().hide()

        self.__animation.setDirection(QAbstractAnimation.Direction.Forward)
        self.__animation.start()
        self.__timer.start()

        super().show()

    def __update_size(self) -> None:
        self.text_label.adjustSize()
        self.icon_label.adjustSize()
        self.__frame.adjustSize()

        self.setFixedWidth(max(120, self.__frame.sizeHint().width() + 20))
        self.setFixedHeight(max(60, self.__frame.sizeHint().height() + 20))

    def setText(self, text: str) -> None:
        self.text_label.setText(text)

    def setIcon(self, icon: QIcon | QPixmap | str) -> None:
        if isinstance(icon, QIcon):
            icon = icon.pixmap(24, 24)
        elif isinstance(icon, str):
            icon = QIcon(icon).pixmap(24, 24)
        self.icon_label.setPixmap(icon)

    @override
    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        if event.type() == event.Type.Resize:
            self.set_position()

        return super().eventFilter(object, event)


if __name__ == "__main__":
    from pathlib import Path

    import qtawesome as qta

    app = QApplication()

    #     app.setStyleSheet(
    #         """
    # Toast {
    #     background: transparent;
    #     border: none;
    # }
    # Toast QLabel {
    #     color: #ffffff;
    #     margin: 0px;
    # }
    # Toast QFrame {
    #     background: #202020;
    #     padding: 5px;
    #     border-radius: 4px;
    # }
    # """
    #     )

    app.setStyleSheet(
        Path("./data/app/style.qss")
        .read_text()
        .replace("<accent_color>", "#ff0000")
        .replace("<highlighted_accent>", "#dd8888")
    )

    root = QMainWindow()
    root.setObjectName("root")

    button = QPushButton("Test")
    button.setIcon(qta.icon("ei.fire", color="#ffffff"))
    root.setCentralWidget(button)

    toast = Toast("Download zur Warteschlange hinzugefügt!", parent=root)
    toast.setIcon(QIcon("./data/icons/icon.svg"))

    button.clicked.connect(lambda: root.startTimer(1000))
    root.timerEvent = lambda event: (  # type: ignore[assignment]
        toast.show(),
        root.killTimer(
            event.timerId(),
        ),
    )

    root.show()
    app.exec()
