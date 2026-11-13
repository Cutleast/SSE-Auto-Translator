"""
Copyright (c) Cutleast
"""

from collections.abc import Sequence
from typing import Optional, override

from PySide6.QtCore import QEasingCurve, QRectF, QSize, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPaintEvent
from PySide6.QtWidgets import QSizePolicy, QWidget


class StackedBar(QWidget):
    """
    Horizontal stacked bar with rounded ends for displaying data ratios.
    """

    ANIMATION_DURATION: int = 500
    """The duration of the transition between two sets of values in milliseconds."""

    FALLBACK_COLOR: QColor = QColor(Qt.GlobalColor.lightGray)
    """The color used for segments without a color and for an empty bar."""

    __start_values: list[float]
    __target_values: list[float]
    __displayed_values: list[float]
    __colors: list[QColor]

    __animation: QVariantAnimation

    def __init__(self, values: list[int], colors: Optional[list[QColor]] = None) -> None:
        """
        Args:
            values (list[int]): List of values to display in the stacked bar.
            colors (Optional[list[QColor]], optional):
                List of colors with the same amount of items as the values. Defaults to
                None.
        """

        super().__init__()

        self.__target_values = [float(value) for value in values]
        self.__start_values = list(self.__target_values)
        self.__displayed_values = list(self.__target_values)
        self.__colors = []
        self.setColors(colors or [None for _ in values])

        self.__animation = QVariantAnimation(self)
        self.__animation.setStartValue(0.0)
        self.__animation.setEndValue(1.0)
        self.__animation.setDuration(StackedBar.ANIMATION_DURATION)
        self.__animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.__animation.valueChanged.connect(self.__on_animation_step)

    def setValues(self, values: list[int]) -> None:
        """
        Args:
            values (list[int]): The values to display.
        """

        self.__animation.stop()
        self.__start_values = list(self.__displayed_values)
        self.__target_values = [float(value) for value in values]
        self.__animation.start()

    def setColors(self, colors: Sequence[Optional[QColor]]) -> None:
        """
        Args:
            colors (Sequence[Optional[QColor]]):
                The colors to set for the segments. `None` falls back to light gray.
        """

        self.__colors = [
            StackedBar.FALLBACK_COLOR if color is None else QColor(color)
            for color in colors
        ]
        self.update()

    @override
    def sizeHint(self) -> QSize:
        return QSize(250, 8)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        bar_rect = QRectF(self.rect())
        radius: float = bar_rect.height() / 2
        outline = QPainterPath()
        outline.addRoundedRect(bar_rect, radius, radius)

        total: float = sum(self.__displayed_values)
        if total <= 0:
            painter.fillPath(outline, StackedBar.FALLBACK_COLOR)
            return

        x: float = bar_rect.left()
        for value, color in zip(self.__displayed_values, self.__colors):
            width: float = bar_rect.width() * value / total
            if width <= 0:
                continue

            segment = QPainterPath()
            segment.addRect(QRectF(x, bar_rect.top(), width, bar_rect.height()))
            painter.fillPath(outline.intersected(segment), color)
            x += width

    def __on_animation_step(self, progress: float) -> None:
        """
        Interpolates the displayed values between the start and target values.

        Args:
            progress (float): Progress of the animation, ranging from 0.0 to 1.0.
        """

        self.__displayed_values = [
            start + (target - start) * progress
            for start, target in zip(self.__start_values, self.__target_values)
        ]
        self.update()
