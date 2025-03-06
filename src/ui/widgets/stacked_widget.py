"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from enum import Enum
from typing import Optional, override

from PySide6.QtCore import (
    QByteArray,
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    Signal,
)
from PySide6.QtGui import QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel, QStackedWidget, QStyle, QStyleOption, QWidget


class StackedWidget(QStackedWidget):
    """
    Animated QStackedWidget.

    Parameters:
        parent: QWidget, defaults to None
        orientation: Orientation of the animation, from Enum StackedWidget.Orientation
        reverse: Reverse sliding direction
    """

    class Direction(Enum):
        LeftToRight = "LeftToRight"
        RightToLeft = "RightToLeft"
        TopToBottom = "TopToBottom"
        BottomToTop = "BottomToTop"
        Automatic = "Automatic"

    class Orientation(Enum):
        Vertical = "Vertical"
        Horizontal = "Horizontal"

    duration = 750
    anim_curve = QEasingCurve.Type.InOutCubic
    _active = False

    # Signals
    anim_finish_signal = Signal()
    anim_cancel_signal = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        orientation: Orientation = Orientation.Vertical,
        reverse: bool = False,
    ):
        super().__init__(parent)

        self.orientation = orientation
        self.reverse = reverse

    def setSpeed(self, speed: int) -> None:
        self.duration = speed

    def setAnimationCurve(self, easingCurve: QEasingCurve.Type) -> None:
        self.anim_curve = easingCurve

    def slideInIndex(
        self, index: int, direction: Direction = Direction.Automatic
    ) -> None:
        if index > (self.count() - 1):
            direction = (
                self.Direction.TopToBottom
                if self.orientation == self.Orientation.Vertical
                else self.Direction.RightToLeft
            )
            index = index % self.count()
        elif index < 0:
            direction = (
                self.Direction.BottomToTop
                if self.orientation == self.Orientation.Vertical
                else self.Direction.LeftToRight
            )
            index = (index + self.count()) % self.count()

        self.slideInWidget(self.widget(index), direction)

    def slideInWidget(
        self, nextWidget: QWidget, direction: Direction = Direction.Automatic
    ) -> None:
        if self._active:
            return

        self._active = True
        current_index = self.currentIndex()
        next_index = self.indexOf(nextWidget)
        current_widget = self.currentWidget()
        next_widget = nextWidget

        if current_index == next_index:
            self._active = False
            return

        x_offset = self.frameRect().width()
        y_offset = self.frameRect().height()
        nextWidget.setGeometry(0, 0, x_offset, y_offset)

        if direction == self.Direction.Automatic:
            if current_index < next_index:
                direction = (
                    self.Direction.TopToBottom
                    if self.orientation == self.Orientation.Vertical
                    else self.Direction.RightToLeft
                )
            else:
                direction = (
                    self.Direction.BottomToTop
                    if self.orientation == self.Orientation.Vertical
                    else self.Direction.LeftToRight
                )

        if self.reverse:
            match direction:
                case self.Direction.TopToBottom:
                    direction = self.Direction.BottomToTop
                case self.Direction.BottomToTop:
                    direction = self.Direction.TopToBottom
                case self.Direction.LeftToRight:
                    direction = self.Direction.RightToLeft
                case self.Direction.RightToLeft:
                    direction = self.Direction.LeftToRight

        match direction:
            case self.Direction.BottomToTop:
                x_offset = 0
                y_offset = -y_offset
            case self.Direction.TopToBottom:
                x_offset = 0
            case self.Direction.RightToLeft:
                x_offset = -x_offset
                y_offset = 0
            case self.Direction.LeftToRight:
                y_offset = 0

        point_current = current_widget.pos()
        point_next = next_widget.pos()

        pixmap_current = current_widget.grab()
        pixmap_next = next_widget.grab()

        label_current = QLabel(self)
        label_next = QLabel(self)
        label_current.resize(current_widget.size())
        label_next.resize(next_widget.size())
        label_current.show()
        label_next.show()
        label_current.setPixmap(pixmap_current)
        label_next.setPixmap(pixmap_next)

        label_current.move(0, 0)
        label_next.move(point_next.x() - x_offset, point_next.y() - y_offset)

        anim_current = QPropertyAnimation(label_current, QByteArray(b"pos"))
        anim_next = QPropertyAnimation(label_next, QByteArray(b"pos"))
        anim_group = QParallelAnimationGroup()

        anim_current.setDuration(self.duration)
        anim_next.setDuration(self.duration)
        anim_current.setEasingCurve(self.anim_curve)
        anim_next.setEasingCurve(self.anim_curve)

        anim_current.setStartValue(point_current)
        anim_current.setEndValue(
            QPoint(x_offset + point_current.x(), y_offset + point_current.y())
        )

        anim_next.setStartValue(
            QPoint(-x_offset + point_next.x(), -y_offset + point_next.y())
        )
        anim_next.setEndValue(point_next)

        anim_group.addAnimation(anim_current)
        anim_group.addAnimation(anim_next)

        anim_group.finished.connect(
            lambda: (
                self.setCurrentIndex(next_index),
                current_widget.hide(),
                current_widget.move(point_current),
                self.finish_anim(),
                label_current.hide(),
                label_next.hide(),
            )
        )
        anim_group.start()

        self.anim_cancel_signal.connect(
            lambda: (
                anim_group.setCurrentTime(self.duration)
                if anim_group.currentTime() > 50
                else None
            )
        )

    def finish_anim(self) -> None:
        self._active = False

    def slideInNext(self) -> None:
        self.slideInIndex(
            self.currentIndex() + 1 if self.currentIndex() < (self.count() - 1) else 0
        )

    def slideInPrev(self) -> None:
        self.slideInIndex(
            self.currentIndex() - 1 if self.currentIndex() > 0 else self.count() - 1
        )

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.anim_cancel_signal.emit()
        event.ignore()

    @override
    def paintEvent(self, arg__1: QPaintEvent) -> None:
        super().paintEvent(arg__1)

        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_Widget, option, painter, self
        )
