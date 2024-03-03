"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from pathlib import Path

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

from .startup_dialog import StartupDialog


class IntroductionPage(qtw.QWidget):
    """
    First page. Informs user about further steps
    and usage of this application.
    """

    def __init__(self, startup_dialog: StartupDialog):
        super().__init__()

        self.startup_dialog = startup_dialog
        self.loc = startup_dialog.loc
        self.mloc = startup_dialog.mloc

        self.setObjectName("primary")

        vlayout = qtw.QVBoxLayout()
        vlayout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.setLayout(vlayout)

        # Title label
        title_label = qtw.QLabel(self.mloc.startup)
        title_label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label, 0, qtc.Qt.AlignmentFlag.AlignHCenter)
        vlayout.addSpacing(50)

        # Info label
        info_label = qtw.QLabel(self.mloc.introduction)
        vlayout.addWidget(info_label)

        # Documentation button
        documentation_button = qtw.QPushButton(self.loc.main.show_documentation)
        documentation_button.clicked.connect(self.startup_dialog.app.show_documentation)
        vlayout.addWidget(documentation_button)

        vlayout.addStretch()

        # Exit and Next Button
        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.exit_button = qtw.QPushButton()
        self.exit_button.setIcon(qta.icon("fa.close", color="#ffffff"))
        self.exit_button.setText(self.loc.main.exit)
        self.exit_button.clicked.connect(
            lambda: (
                self.startup_dialog.close(),
                self.startup_dialog.app.exit()
            )
        )
        hlayout.addWidget(self.exit_button, 0, qtc.Qt.AlignmentFlag.AlignLeft)

        hlayout.addStretch()

        self.next_button = qtw.QPushButton()
        self.next_button.setIcon(qta.icon("fa5s.chevron-right", color="#ffffff"))
        self.next_button.setText(self.loc.main.next)
        self.next_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.next_button.clicked.connect(self.startup_dialog.page_widget.slideInNext)
        hlayout.addWidget(self.next_button)
