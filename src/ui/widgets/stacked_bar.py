"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCharts import QBarSet, QChart, QChartView, QHorizontalPercentBarSeries
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QPainter


class StackedBar(QChartView):
    """
    Class for stacked bar for displaying data ratios.
    """

    __chart: QChart
    __series: QHorizontalPercentBarSeries

    __bar_sets: list[QBarSet]

    def __init__(self, values: list[int], colors: Optional[list[QColor]] = None) -> None:
        """
        Args:
            values (list[int]): List of values to display in the stacked bar.
            colors (Optional[list[QColor]], optional):
                List of colors with the same amount of items as the values. Defaults to
                None.
        """

        super().__init__()

        self.setRubberBand(self.RubberBand.NoRubberBand)
        self.setResizeAnchor(self.ViewportAnchor.AnchorViewCenter)
        self.setContentsMargins(0, 0, 0, 0)
        self.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        self.__chart = QChart()
        self.__chart.setMargins(QMargins(0, 0, 0, 0))
        self.__chart.layout().setContentsMargins(0, 0, 0, 0)
        self.__chart.setBackgroundRoundness(0)
        self.__chart.setBackgroundVisible(False)
        self.__chart.legend().hide()
        self.__chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.setChart(self.__chart)
        self.__series = QHorizontalPercentBarSeries()
        self.__series.setBarWidth(2)
        self.__chart.addSeries(self.__series)

        self.__bar_sets = []
        for v, value in enumerate(values):
            bar_set = QBarSet("")
            bar_set.append(value)

            if colors is not None:
                color: QColor = colors[v]
                bar_set.setColor(color)

            bar_set.setBorderColor(Qt.GlobalColor.transparent)
            self.__series.append(bar_set)
            self.__bar_sets.append(bar_set)

    def setValues(self, values: list[int]) -> None:
        """
        Args:
            values (list[int]): The values to display.
        """

        for v, value in enumerate(values):
            bar_set = self.__bar_sets[v]
            bar_set.remove(0)
            bar_set.append(value)

    def setColors(self, colors: list) -> None:
        """
        Args:
            colors (list): The colors to set for the bar sets.
        """

        for c, color in enumerate(colors):
            bar_set = self.__bar_sets[c]
            if color is None:
                color = Qt.GlobalColor.lightGray
            bar_set.setColor(color)
