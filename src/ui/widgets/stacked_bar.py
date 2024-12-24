"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional

from PySide6.QtCharts import QBarSet, QChart, QChartView, QHorizontalPercentBarSeries
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QPainter


class StackedBar(QChartView):
    """
    Class for stacked bar for displaying data ratios.
    """

    def __init__(self, values: list[int], colors: Optional[list] = None):
        super().__init__()

        self.setRubberBand(self.RubberBand.NoRubberBand)
        self.setResizeAnchor(self.ViewportAnchor.AnchorViewCenter)
        self.setContentsMargins(0, 0, 0, 0)
        self.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        self._chart = QChart()
        self._chart.setMargins(QMargins(0, 0, 0, 0))
        self._chart.layout().setContentsMargins(0, 0, 0, 0)
        self._chart.setBackgroundRoundness(0)
        self._chart.setBackgroundVisible(False)
        self._chart.legend().hide()
        self._chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.setChart(self._chart)
        self.__series = QHorizontalPercentBarSeries()
        self.__series.setBarWidth(2)
        self._chart.addSeries(self.__series)

        self.__bar_sets: list[QBarSet] = []
        for v, value in enumerate(values):
            bar_set = QBarSet("")
            bar_set.append(value)

            if colors is not None:
                color = colors[v]
                if color is None:
                    color = Qt.GlobalColor.lightGray
                bar_set.setColor(color)

            bar_set.setBorderColor(Qt.GlobalColor.transparent)
            self.__series.append(bar_set)
            self.__bar_sets.append(bar_set)

    def setValues(self, values: list[int]) -> None:
        for v, value in enumerate(values):
            bar_set = self.__bar_sets[v]
            bar_set.remove(0)
            bar_set.append(value)

    def setColors(self, colors: list) -> None:
        for c, color in enumerate(colors):
            bar_set = self.__bar_sets[c]
            if color is None:
                color = Qt.GlobalColor.lightGray
            bar_set.setColor(color)
