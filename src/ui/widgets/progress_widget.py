"""
Copyright (c) Cutleast
"""

import traceback
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.utilities.exceptions import ExceptionBase
from ui.utilities.icon_provider import IconProvider


class ProgressWidget(QWidget):
    """
    Custom widget for displaying progress updates in a QTreeWidgetItem.
    """

    close_signal = Signal()
    """
    This signal gets emitted when the close button is pressed.
    """

    __status_label: QLabel
    __progress_bar: QProgressBar
    __copy_button: QPushButton
    __close_button: QPushButton

    def __init__(self, item: QTreeWidgetItem, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.item = item

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
        self.__copy_button.setIcon(IconProvider.get_qta_icon("mdi6.content-copy"))
        self.__copy_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.toolTip())
        )
        hlayout.addWidget(self.__copy_button)
        self.__copy_button.hide()

        self.__close_button = QPushButton()
        self.__close_button.setFixedSize(35, 35)
        self.__close_button.setObjectName("download_button")
        self.__close_button.setIcon(IconProvider.get_qta_icon("mdi6.close"))
        self.__close_button.clicked.connect(self.close_signal.emit)
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

    def setException(self, exception: Exception) -> None:
        """
        Shows copy and close button and sets an error message as tooltip.

        Args:
            exception (Exception): Exception to display.
        """

        self.__copy_button.show()
        self.__close_button.show()
        self.__progress_bar.setObjectName("error")
        self.__progress_bar.setStyleSheet(self.styleSheet())
        self.__progress_bar.setValue(1)
        self.__progress_bar.setMaximum(1)
        self.__status_label.setWordWrap(True)

        if isinstance(exception, ExceptionBase):
            self.__status_label.setText(exception.getLocalizedMessage())
        else:
            self.__status_label.setText(traceback.format_exception(exception)[-1])

        self.setToolTip("".join(traceback.format_exception(exception)))
