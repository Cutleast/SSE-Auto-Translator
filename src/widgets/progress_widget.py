"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw
from pyperclip import copy


class ProgressWidget(qtw.QWidget):
    exception_signal = qtc.Signal(str)

    def __init__(self, item: qtw.QTreeWidgetItem, parent=None):
        super().__init__(parent)

        self.item = item

        self.exception_signal.connect(self.__set_exception)

        hlayout = qtw.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        vlayout = qtw.QVBoxLayout()
        vlayout.setSpacing(0)
        vlayout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        hlayout.addLayout(vlayout)

        self.status_label = qtw.QLabel()
        self.status_label.setObjectName("status_label")
        vlayout.addWidget(self.status_label)

        vlayout.addSpacing(2)

        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        vlayout.addWidget(self.progress_bar)

        self.copy_button = qtw.QPushButton()
        self.copy_button.setFixedSize(35, 35)
        self.copy_button.setObjectName("download_button")
        self.copy_button.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
        self.copy_button.clicked.connect(lambda: copy(self.toolTip()))
        hlayout.addWidget(self.copy_button)
        self.copy_button.hide()

        self.close_button = qtw.QPushButton()
        self.close_button.setFixedSize(35, 35)
        self.close_button.setObjectName("download_button")
        self.close_button.setIcon(qta.icon("fa.close", color="#ffffff"))
        self.close_button.clicked.connect(lambda: self.item.setHidden(True))
        hlayout.addWidget(self.close_button)
        self.close_button.hide()

        self.setFixedHeight(40)

    def set_exception(self, text: str):
        """
        Shows copy and close button and sets `text` as tooltip.
        This method is thread-safe.
        """

        self.exception_signal.emit(text)

    def __set_exception(self, text: str):
        self.copy_button.show()
        self.close_button.show()
        self.progress_bar.hide()
        self.status_label.setWordWrap(True)
        self.setToolTip(text)
