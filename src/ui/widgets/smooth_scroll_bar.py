"""
Copyright (c) Cutleast

Original code from here:
    https://github.com/tonquer/JMComic-qt/blob/main/src/component/scroll/smooth_scroll_bar.py
and adapted for usage in SSE-AT.
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QScrollBar, QWidget


class SmoothScrollBar(QScrollBar):
    """
    QScrollBar with animated (smooth) scrolling.
    """

    __animation: QPropertyAnimation
    __value: int

    __moveEventSignal = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.__animation = QPropertyAnimation()
        self.__animation.setTargetObject(self)
        self.__animation.setPropertyName(b"value")
        self.__animation.setEasingCurve(QEasingCurve.Type.OutQuint)
        self.__animation.setDuration(500)
        self.__animation.finished.connect(self._finished)

        self.__value = self.value()

    def _finished(self) -> None:
        self.__moveEventSignal.emit()
        return

    def setValue(self, value: int) -> None:
        if value == self.value():
            return

        self.__animation.stop()
        self.__moveEventSignal.emit()
        self.__animation.setStartValue(self.value())
        self.__animation.setEndValue(value)
        self.__animation.start()

    def setScrollValue(self, value: int) -> None:
        self.__value += value
        self.__value = max(self.minimum(), self.__value)
        self.__value = min(self.maximum(), self.__value)

        self.setValue(self.__value)

    def scrollTo(self, value: int) -> None:
        self.__value = value
        self.__value = max(self.minimum(), self.__value)
        self.__value = min(self.maximum(), self.__value)

        self.setValue(self.__value)

    def resetValue(self, value: int) -> None:
        self.__value = value

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.__animation.stop()
        super().mousePressEvent(event)
        self.__value = self.value()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.__animation.stop()
        super().mouseReleaseEvent(event)
        self.__value = self.value()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.__animation.stop()
        super().mouseMoveEvent(event)
        self.__value = self.value()
