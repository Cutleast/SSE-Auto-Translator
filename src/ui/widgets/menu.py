"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
)
from PySide6.QtGui import QCursor, QRegion
from PySide6.QtWidgets import QMenu


class Menu(QMenu):
    """
    Animated menu class.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.ani = QPropertyAnimation(self, b"pos", self)
        self.ani.valueChanged.connect(self.onSlideValueChanged)

        self.aboutToShow.connect(self.show)

    def onSlideValueChanged(self, pos: QPoint):
        w = self.sizeHint().width()
        h = self.sizeHint().height()
        y = self.ani.endValue().y() - pos.y()
        self.setMask(QRegion(0, y, w, h))

    def show_anim(self, pos: QPoint = None):
        if pos is None:
            pos = QCursor.pos()
            pos.setX(pos.x() - 20)
            pos.setY(pos.y() + 20)
        h = self.sizeHint().height() + 5
        self.ani.setStartValue(pos - QPoint(0, int(h / 2)))
        self.ani.setEndValue(pos)
        self.ani.setDuration(225)
        self.ani.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.ani.finished.connect(self.ani.finished.disconnect)
        self.ani.start()

    def show(self):
        super().show()
        self.ani.setDirection(QAbstractAnimation.Direction.Forward)
        self.show_anim()
