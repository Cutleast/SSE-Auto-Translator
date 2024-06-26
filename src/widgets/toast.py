"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw


class Toast(qtw.QWidget):
    """
    A simple animated toast notification.
    """

    def __init__(
        self,
        text: str,
        duration: int = 2,
        opacity: float = 1,
        anim_duration: float = 0.2,
        pos: qtc.QPoint = None,
        parent: qtw.QWidget = None,
    ):
        super().__init__(parent)

        self.__parent = parent
        self.__parent.installEventFilter(self)
        self.installEventFilter(self)
        self.__timer = qtc.QTimer(self)
        self.__timer.setInterval((duration + anim_duration) * 1000)
        self.__timer.setTimerType(qtc.Qt.TimerType.PreciseTimer)
        self.__timer.timeout.connect(self.hide)

        self.setWindowFlag(qtc.Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(qtc.Qt.WindowType.Popup, True)
        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(qtc.Qt.WindowType.NoDropShadowWindowHint, True)
        self.setFocusPolicy(qtc.Qt.FocusPolicy.NoFocus)
        self.setAttribute(qtc.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(qtc.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(qtc.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.__animation = qtc.QPropertyAnimation(self, b"windowOpacity")
        self.__animation.setDuration(anim_duration * 1000)
        self.__animation.setStartValue(0.0)
        self.__animation.setEndValue(opacity)
        self.__animation.valueChanged.connect(self.__set_opacity)

        vlayout = qtw.QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlayout)
        self.__frame = qtw.QFrame()
        vlayout.addWidget(self.__frame)

        hlayout = qtw.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.__frame.setLayout(hlayout)

        self.icon_label = qtw.QLabel()
        self.icon_label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        hlayout.addWidget(self.icon_label)

        self.text_label = qtw.QLabel(text)
        self.text_label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        # self.text_label.setWordWrap(True)
        hlayout.addWidget(self.text_label)

        self.set_position(pos)
        self.__update_size()

        super().hide()

    def __set_opacity(self, opacity: float):
        self.setWindowOpacity(opacity)

        if opacity == 0.0:
            super().hide()

    def hide(self):
        self.__animation.setDirection(qtc.QAbstractAnimation.Direction.Backward)
        self.__animation.start()

        if self.__timer.isActive():
            self.__timer.stop()

    def set_position(self, pos: qtc.QPoint = None):
        # If pos is None, set pos to center of lower third of screen
        if pos is None:
            scr = qtw.QApplication.primaryScreen().availableGeometry()
            pos = scr.center()
            pos.setY(scr.height() - 50)

        rect = self.geometry()
        rect.moveCenter(pos)
        self.setGeometry(rect)

    def show(self):
        if self.__timer.isActive():
            self.__timer.stop()
            super().hide()

        self.__animation.setDirection(qtc.QAbstractAnimation.Direction.Forward)
        self.__animation.start()
        self.__timer.start()

        super().show()

    def __update_size(self):
        self.text_label.adjustSize()
        self.icon_label.adjustSize()
        self.__frame.adjustSize()

        self.setFixedWidth(max(120, self.__frame.sizeHint().width() + 20))
        self.setFixedHeight(max(60, self.__frame.sizeHint().height() + 20))

    def setText(self, text: str):
        self.text_label.setText(text)

    def setIcon(self, icon: qtg.QIcon | qtg.QPixmap | str):
        if isinstance(icon, qtg.QIcon):
            icon = icon.pixmap(24, 24)
        self.icon_label.setPixmap(icon)

    def eventFilter(self, object: qtc.QObject, event: qtc.QEvent) -> bool:
        if event.type() == event.Type.Resize:
            self.set_position()

        return super().eventFilter(object, event)


if __name__ == "__main__":
    import qtawesome as qta
    from pathlib import Path

    app = qtw.QApplication()

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

    root = qtw.QMainWindow()
    root.setObjectName("root")

    button = qtw.QPushButton("Test")
    button.setIcon(qta.icon("ei.fire", color="#ffffff"))
    root.setCentralWidget(button)

    toast = Toast("Download zur Warteschlange hinzugefügt!", parent=root)
    toast.setIcon(qtg.QIcon("./data/icons/icon.svg"))

    button.clicked.connect(lambda: root.startTimer(1000))
    root.timerEvent = lambda event: (toast.show(), root.killTimer(event.timerId()))

    root.show()
    app.exec()
