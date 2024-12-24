"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from pyperclip import copy
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ProgressWidget(QWidget):
    """
    Custom widget for displaying progress updates in a QTreeWidgetItem.
    """

    __exception_signal = Signal(str)

    __status_label: QLabel
    __progress_bar: QProgressBar
    __copy_button: QPushButton
    __close_button: QPushButton

    def __init__(self, item: QTreeWidgetItem, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.item = item

        self.__exception_signal.connect(self.__set_exception)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        vlayout = QVBoxLayout()
        vlayout.setSpacing(0)
        vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        hlayout.addLayout(vlayout)

        self.__status_label = QLabel()
        self.__status_label.setObjectName("console")
        vlayout.addWidget(self.__status_label)

        vlayout.addSpacing(2)

        self.__progress_bar = QProgressBar()
        self.__progress_bar.setTextVisible(False)
        self.__progress_bar.setFixedHeight(2)
        vlayout.addWidget(self.__progress_bar)

        self.__copy_button = QPushButton()
        self.__copy_button.setFixedSize(35, 35)
        self.__copy_button.setObjectName("download_button")
        self.__copy_button.setIcon(
            qta.icon("mdi6.content-copy", color=self.palette().text().color())
        )
        self.__copy_button.clicked.connect(lambda: copy(self.toolTip()))
        hlayout.addWidget(self.__copy_button)
        self.__copy_button.hide()

        self.__close_button = QPushButton()
        self.__close_button.setFixedSize(35, 35)
        self.__close_button.setObjectName("download_button")
        self.__close_button.setIcon(
            qta.icon("fa.close", color=self.palette().text().color())
        )
        self.__close_button.clicked.connect(lambda: self.item.setHidden(True))
        hlayout.addWidget(self.__close_button)
        self.__close_button.hide()

        self.setFixedHeight(40)

    def setText(self, text: str) -> None:
        """
        Sets text of status label.

        Args:
            text (str): Text to display.
        """

        self.__status_label.setText(text)

    def setProgress(self, current: int, maximum: int) -> None:
        """
        Progress to display on progress bar.

        Args:
            current (int): Current progress.
            maximum (int): Total size or maximum progress.
        """

        if maximum > 1:
            current = round(current / maximum * 100)
            self.__progress_bar.setMaximum(100)
        else:
            self.__progress_bar.setMaximum(maximum)

        self.__progress_bar.setValue(current)

    def set_exception(self, text: str) -> None:
        """
        Shows copy and close button and sets an error message as tooltip.
        This method is thread-safe.

        Args:
            text (str): Error message to display. (Usually the exception message).
        """

        self.__exception_signal.emit(text)

    def __set_exception(self, text: str) -> None:
        self.__copy_button.show()
        self.__close_button.show()
        self.__progress_bar.hide()
        self.__status_label.setWordWrap(True)
        self.setToolTip(text)
