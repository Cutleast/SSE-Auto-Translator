"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw


class ProgressWidget(qtw.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = qtw.QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self._layout)

        self.status_label = qtw.QLabel()
        self.status_label.setObjectName("status_label")
        self._layout.addWidget(self.status_label)

        self._layout.addSpacing(2)

        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        self._layout.addWidget(self.progress_bar)

        self.setFixedHeight(40)

