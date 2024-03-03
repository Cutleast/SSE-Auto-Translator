"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw


class Menu(qtw.QMenu):
    """
    Animated menu class.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlag(qtc.Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(qtc.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.ani = qtc.QPropertyAnimation(self, b"pos", self)
        self.ani.valueChanged.connect(self.onSlideValueChanged)

        self.aboutToShow.connect(self.show)

    def onSlideValueChanged(self, pos: qtc.QPoint):
        w = self.sizeHint().width()
        h = self.sizeHint().height()
        y = self.ani.endValue().y() - pos.y()
        self.setMask(qtg.QRegion(0, y, w, h))

    def show_anim(self, pos: qtc.QPoint = None):
        if pos is None:
            pos = qtg.QCursor.pos()
            pos.setX(pos.x() - 20)
            pos.setY(pos.y() + 20)
        h = self.sizeHint().height() + 5
        self.ani.setStartValue(pos - qtc.QPoint(0, int(h / 2)))
        self.ani.setEndValue(pos)
        self.ani.setDuration(225)
        self.ani.setEasingCurve(qtc.QEasingCurve.Type.OutQuad)
        self.ani.finished.connect(self.ani.finished.disconnect)
        self.ani.start()

    def show(self):
        super().show()
        self.ani.setDirection(qtc.QAbstractAnimation.Direction.Forward)
        self.show_anim()
